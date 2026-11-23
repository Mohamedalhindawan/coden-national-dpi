"""Read-only inspection of real hash-pinned local Qwen server and client.

This code only checks Docker inspect/completion receipts. It does NOT execute
Docker, fetch models, authenticate an OpenHands SDK runtime or approve releases.
Actual model execution must be separately proven by the CI runner's guest HTTP
request against the already-running constrained real local inference server.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

from .factory_docker_isolation_probe import TEST_IMAGE as CLIENT_IMAGE
from .factory_internal_model_network_probe import _limited_container as _limited_client

LLAMA_SHA = "da524c71f9dd09913df29264bb7229b99a2de82d8a26e6902e6921d413560d6d"
MODEL_SHA = "1d9614638d18024d0fbb36575a15f1302a3adf044df10345688ec4f6e1c4ff32"
LIBGOMP_SHA = "870c27299185a5dd4accad3b15bf82a7409fd7073cccaa8025875307da4d0ce2"
LIBCURL_SHA = "2fc35b8056aebaa6cfe9a5672a8e06339c3e690657fbebc6c5d6b50d9f9626fb"
LIBSTDCXX_SHA = "29ef3d289b272704b75141906c8f683db0f2bdb0942061366691333bfb289bdc"
UBUNTU_BASE = (
    "docker.io/library/ubuntu@sha256:"
    "f64b2ffc2f10ab8f8505aa56b2664bd846cbb9df87c7e2532e30f7667021c0e6"
)
NAME = re.compile(r"coden-factory-real-qwen-[0-9]+-[0-9]+\Z")
SERVER = re.compile(r"coden-qwen-private:[0-9]+-[0-9]+\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
IMAGE_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")
LABELS = {
    "org.coden.llama_archive_sha256": LLAMA_SHA,
    "org.coden.qwen_weights_sha256": MODEL_SHA,
    "org.coden.ubuntu_base": UBUNTU_BASE,
    "org.coden.pilot_scope": "read-only-synthetic-internal-llama-server",
    "org.coden.libgomp_archive_sha256": LIBGOMP_SHA,
    "org.coden.libcurl_archive_sha256": LIBCURL_SHA,
    "org.coden.libstdcxx_archive_sha256": LIBSTDCXX_SHA,
}
MAX_BYTES = 180_000


def _check(ok, why):
    if not ok:
        raise ValueError("Real Qwen private server admission BLOCKED: " + why)


def _server_check(x, network_name, network_id):
    _check(isinstance(x, dict), "missing model server")
    host = x.get("HostConfig")
    cfg = x.get("Config")
    state = x.get("State")
    ns = x.get("NetworkSettings")
    _check(all(isinstance(v, dict) for v in (host, cfg, state, ns)),
           "incomplete model server metadata")
    _check(state.get("Running") is True, "model server not running")
    _check(isinstance(x.get("Id"), str) and HASH.fullmatch(x["Id"]),
           "invalid model container identity")
    _check(isinstance(x.get("Image"), str) and IMAGE_HASH.fullmatch(x["Image"]),
           "missing model server content digest")
    image = cfg.get("Image")
    _check(isinstance(image, str) and SERVER.fullmatch(image),
           "unapproved local image name")
    _check(cfg.get("Labels") == LABELS, "unverified model/runtime provenance")
    _check(cfg.get("User") == "65534:65534", "model root execution forbidden")
    env = cfg.get("Env")
    _check(isinstance(env, list) and 1 <= len(env) <= 3
           and set(env) == {
               "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
               "LD_LIBRARY_PATH=/opt/llama:/opt/runtime-libs",
           }, "untrusted model environment/credentials")
    limits = {
        "NanoCpus": 2_000_000_000,
        "Memory": 1_610_612_736,
        "MemorySwap": 1_610_612_736,
        "PidsLimit": 64,
    }
    for k, v in limits.items():
        _check(type(host.get(k)) is int and host[k] == v, "unbounded model " + k)
    _check(host.get("CapDrop") == ["ALL"] and host.get("CapAdd") in (None, []),
           "model capabilities escalated")
    _check(host.get("Privileged") is False and
           host.get("ReadonlyRootfs") is True,
           "model runtime privilege or writable root")
    _check(host.get("NetworkMode") == network_name and
           host.get("PidMode") in ("", "private") and
           host.get("IpcMode") == "private", "model namespaces wrong")
    _check(host.get("SecurityOpt") == ["no-new-privileges"],
           "model no-new-privileges absent")
    _check(host.get("Binds") in (None, []) and
           host.get("Devices") in (None, []) and
           host.get("Mounts") in (None, []) and
           host.get("PortBindings") in (None, {}),
           "model mounts/devices/published ports")
    _check(host.get("Tmpfs") == {
        "/tmp": "rw,noexec,nosuid,nodev,size=32m,mode=1777"
    }, "model unexpected writable path")
    _check(host.get("AutoRemove") is True and
           isinstance(host.get("RestartPolicy"), dict) and
           host["RestartPolicy"].get("Name") == "no",
           "model process lifecycle unbounded")
    mounts = x.get("Mounts")
    _check(isinstance(mounts, list) and all(
        isinstance(y, dict) and y.get("Type") == "tmpfs"
        and y.get("Destination") == "/tmp"
        for y in mounts
    ), "unrecognized model filesystem mount")
    networks = ns.get("Networks")
    _check(isinstance(networks, dict) and set(networks) == {network_name}
           and isinstance(networks[network_name], dict) and
           networks[network_name].get("NetworkID") == network_id,
           "model attached to another network")
    ports = ns.get("Ports")
    _check(ports in (None, {}) or (
        isinstance(ports, dict) and
        all(v in (None, []) for v in ports.values())
    ), "model port exposed to host")


def audit_pair(network, client, server):
    """Validate resource and provenance metadata without claiming inference."""
    _check(isinstance(network, dict), "network missing")
    name = network.get("Name")
    _check(isinstance(name, str) and NAME.fullmatch(name),
           "unexpected network identity")
    _check(network.get("Internal") is True and
           network.get("Driver") == "bridge" and
           network.get("Scope") == "local", "not internal local network")
    network_id = network.get("Id")
    _check(isinstance(network_id, str) and HASH.fullmatch(network_id),
           "missing network sha identity")
    members = network.get("Containers")
    _check(isinstance(members, dict) and len(members) == 2,
           "unexpected third network participant")
    _limited_client(client, name, network_id)
    _server_check(server, name, network_id)
    _check(client["Id"] != server["Id"] and
           set(members) == {client["Id"], server["Id"]},
           "wrong live network participants")
    _check(client["Config"]["Image"] == CLIENT_IMAGE,
           "unexpected client fixture image")
    return {
        "plan_version": "v1.0",
        "state": "REAL_QWEN_PRIVATE_NETWORK_INSPECT_PASS",
        "scope": "SYNTHETIC_LLAMA_CPP_QWEN_SERVER_ONLY",
        "runtime_archive_sha256": LLAMA_SHA,
        "model_sha256": MODEL_SHA,
        "base_image": UBUNTU_BASE,
        "client_image": CLIENT_IMAGE,
        "two_resource_capped_containers": True,
        "network_internal": True,
        "no_published_ports": True,
        "model_inference_proven_by_inspect": False,
        "rootless_daemon_verified": False,
        "model_license_review_approved": False,
        "transitive_sbom_verified": False,
        "openhands_sdk_agent_server_proven": False,
        "openhands_live_execution_authorized": False,
        "factory_production_authorized": False,
        "release_authorized": False,
        "paid_calls": 0,
    }


def audit_completion(data):
    """Accept only bounded actual llama.cpp completion data from CI HTTP POST."""
    _check(isinstance(data, dict), "invalid completion JSON")
    content = data.get("content")
    n = data.get("tokens_predicted")
    timings = data.get("timings")
    _check(isinstance(content, str) and 0 < len(content) <= 1000,
           "no bounded model-generated text")
    _check(type(n) is int and 1 <= n <= 32,
           "no real completion token count")
    _check(isinstance(timings, dict) and
           type(timings.get("predicted_n")) is int and
           timings["predicted_n"] == n,
           "missing model token/timing counter")
    return {
        "state": "LLAMA_SERVER_COMPLETION_SHAPE_PASS",
        "tokens_predicted": n,
        "response_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "real_model_output_origin": "runner_observed_private_local_llama_cpp_http",
        "response_body_published": False,
        "openhands_live_execution_authorized": False,
        "release_authorized": False,
        "paid_calls": 0,
    }


def _load_one(path):
    f = Path(path)
    _check(not f.is_symlink() and hasattr(os, "O_NOFOLLOW"), "bad inspect path")
    fd = os.open(f, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        st = os.fstat(fd)
        _check(stat.S_ISREG(st.st_mode) and
               0 < st.st_size <= MAX_BYTES, "inspect size not bounded")
        with os.fdopen(os.dup(fd), "rb") as file:
            data = file.read(MAX_BYTES + 1)
        _check(len(data) == st.st_size, "inspect concurrent modification")
    finally:
        os.close(fd)
    x = json.loads(data.decode("utf-8"))
    _check(isinstance(x, list) and len(x) == 1 and
           isinstance(x[0], dict), "expected exactly one inspect object")
    return x[0]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--network", type=Path, required=True)
    parser.add_argument("--client", type=Path, required=True)
    parser.add_argument("--server", type=Path, required=True)
    parser.add_argument("--completion", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        evidence = audit_pair(
            _load_one(args.network),
            _load_one(args.client),
            _load_one(args.server),
        )
        # llama-server returns a single JSON object rather than Docker's list.
        p = args.completion
        _check(not p.is_symlink() and p.is_file()
               and 0 < p.stat().st_size <= 16_384,
               "untrusted model JSON")
        actual = json.loads(p.read_text(encoding="utf-8"))
        evidence["real_cpu_completion"] = audit_completion(actual)
        evidence["actual_real_qwen_completion_verified"] = True
        evidence["actual_private_client_request_observed"] = True
        evidence["openhands_live_execution_authorized"] = False
        evidence["release_authorized"] = False
        output = args.receipt
        _check(output.is_absolute() and not output.exists() and
               not output.is_symlink() and output.parent.is_dir() and
               not output.parent.is_symlink(), "unsafe evidence destination")
        with output.open("x", encoding="utf-8") as handle:
            json.dump(evidence, handle, sort_keys=True, indent=2)
            handle.write("\n")
    except (OSError, TypeError, ValueError, KeyError, UnicodeError, json.JSONDecodeError):
        parser.exit(2, "REAL Qwen model/network evidence BLOCKED\n")
    print(json.dumps({
        "real_model_completion_verified": True,
        "release_authorized": False,
        "openhands_live_execution_authorized": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
