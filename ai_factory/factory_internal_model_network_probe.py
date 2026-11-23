"""Read-only, fail-closed metadata verifier for a two-container private HTTP pilot.

This inspects Docker's true live inspect JSON supplied by CI and does not run
Docker itself. Network-policy metadata does not independently prove kernel
egress filtering. A separate real Docker guest exercise must demonstrate it.
"""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys

from .factory_docker_isolation_probe import (
    TEST_IMAGE, CPU_NANO, MEMORY_BYTES, PIDS, TMPFS
)

NAME_RE = re.compile(r"coden-factory-ollama-[0-9]+-[0-9]+\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
IMAGE_SHA = re.compile(r"sha256:[0-9a-f]{64}\Z")
MAX_JSON_BYTES = 180_000


def _require(value, reason):
    if not value:
        raise ValueError("private model network policy BLOCKED: " + reason)


def _limited_container(container, network_name, network_id):
    _require(isinstance(container, dict), "missing container")
    host = container.get("HostConfig")
    cfg = container.get("Config")
    state = container.get("State")
    links = container.get("NetworkSettings")
    _require(all(isinstance(x, dict) for x in (host, cfg, state, links)),
             "incomplete container inspect")
    _require(state.get("Running") is True, "container not running")
    _require(isinstance(container.get("Id"), str) and HEX64.fullmatch(container["Id"]),
             "invalid container identity")
    _require(isinstance(container.get("Image"), str)
             and IMAGE_SHA.fullmatch(container["Image"]),
             "missing exact image content identity")
    _require(cfg.get("Image") == TEST_IMAGE, "unapproved image")
    _require(cfg.get("User") == "65534:65534", "root forbidden")
    env = cfg.get("Env")
    _require(isinstance(env, list) and 0 < len(env) <= 2
             and all(isinstance(x, str) and
                     x.startswith("PATH=") and len(x) <= 600
                     for x in env), "inherited secret/unknown environment")
    _require(type(host.get("NanoCpus")) is int
             and host["NanoCpus"] == CPU_NANO, "CPU limit missing")
    _require(type(host.get("Memory")) is int
             and host["Memory"] == MEMORY_BYTES, "memory limit missing")
    _require(type(host.get("MemorySwap")) is int
             and host["MemorySwap"] == MEMORY_BYTES, "swap beyond budget")
    _require(type(host.get("PidsLimit")) is int
             and host["PidsLimit"] == PIDS, "PID limit missing")
    _require(host.get("CapDrop") == ["ALL"]
             and host.get("CapAdd") in (None, []), "capability escalation")
    _require(host.get("Privileged") is False
             and host.get("ReadonlyRootfs") is True,
             "root/privilege/filesystem escape")
    _require(host.get("NetworkMode") == network_name
             and host.get("PidMode") in ("", "private")
             and host.get("IpcMode") == "private",
             "unexpected network/PID/IPC namespaces")
    _require(host.get("SecurityOpt") == ["no-new-privileges"],
             "new privileges possible")
    _require(host.get("AutoRemove") is True
             and isinstance(host.get("RestartPolicy"), dict)
             and host["RestartPolicy"].get("Name") == "no",
             "unsafe auto restart/lifecycle")
    _require(host.get("Binds") in (None, [])
             and host.get("Devices") in (None, [])
             and host.get("Mounts") in (None, [])
             and host.get("PortBindings") in (None, {}),
             "host bind/device/port forbidden")
    _require(host.get("Tmpfs") == {"/tmp": TMPFS},
             "unexpected writable tmpfs")
    mounts = container.get("Mounts")
    _require(isinstance(mounts, list)
             and all(isinstance(x, dict) and
                     x.get("Type") == "tmpfs" and
                     x.get("Destination") == "/tmp" for x in mounts),
             "unexpected container mounts")
    namespaces = links.get("Networks")
    _require(isinstance(namespaces, dict) and set(namespaces) == {network_name},
             "attached to unexpected network")
    attach = namespaces[network_name]
    _require(isinstance(attach, dict)
             and attach.get("NetworkID") == network_id,
             "network identity mismatch")
    ports = links.get("Ports")
    _require(ports in (None, {}) or
             (isinstance(ports, dict) and
              all(value in (None, []) for value in ports.values())),
             "container publishes public ports")


def inspect_pair(network, client, server):
    """Restrict one real Docker network to exactly two capped fixture containers."""
    _require(isinstance(network, dict), "missing network metadata")
    name = network.get("Name")
    _require(isinstance(name, str) and NAME_RE.fullmatch(name),
             "operator-owned network naming required")
    _require(network.get("Internal") is True
             and network.get("Driver") == "bridge"
             and network.get("Scope") == "local",
             "not an internal local bridge")
    network_id = network.get("Id")
    _require(isinstance(network_id, str) and HEX64.fullmatch(network_id),
             "network digest/identity missing")
    container_map = network.get("Containers")
    _require(isinstance(container_map, dict), "network containers missing")
    _limited_container(client, name, network_id)
    _limited_container(server, name, network_id)
    ids = (client["Id"], server["Id"])
    _require(ids[0] != ids[1] and set(container_map) == set(ids)
             and len(container_map) == 2,
             "unexpected third network participant or duplicate identity")
    return {
        "plan_version": "v1.0",
        "scope": "TWO_SYNTHETIC_BUSYBOX_CONTAINERS_ONLY",
        "policy_state": "SYNTHETIC_INTERNAL_NETWORK_METADATA_PASS",
        "image": TEST_IMAGE,
        "container_count": 2,
        "docker_network_internal": True,
        "same_isolated_network": True,
        "both_containers_resource_capped": True,
        "no_host_port_publications": True,
        "actual_egress_proved_by_metadata_alone": False,
        "actual_guest_http_and_egress_tests_run_by_this_module": False,
        "real_model_invoked": False,
        "real_ollama_endpoint_tested": False,
        "rootless_docker_host_verified": False,
        "openhands_sdk_dependencies_and_image_sbom_verified": False,
        "openhands_live_execution_authorized": False,
        "factory_production_authorized": False,
        "release_authorized": False,
        "paid_calls": 0,
        "warning": "Synthetic HTTP endpoint only; does not verify real Ollama, rootless daemon, OpenHands, SBOM or continuous egress isolation.",
    }


def _load_exact_one(path):
    """Open bounded regular JSON by O_NOFOLLOW; refuse symlink and huge files."""
    path = Path(path)
    _require(not path.is_symlink() and hasattr(os, "O_NOFOLLOW"),
             "unsafe inspect path")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise ValueError("missing inspect input") from exc
    try:
        item = os.fstat(fd)
        _require(stat.S_ISREG(item.st_mode) and
                 0 < item.st_size <= MAX_JSON_BYTES, "oversize/invalid inspect file")
        with os.fdopen(os.dup(fd), "rb") as f:
            data = f.read(MAX_JSON_BYTES + 1)
        _require(len(data) == item.st_size, "inspect file changed")
    finally:
        os.close(fd)
    found = json.loads(data.decode("utf-8"))
    _require(isinstance(found, list) and len(found) == 1
             and isinstance(found[0], dict),
             "one Docker inspect JSON object required")
    return found[0]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--network-json", type=Path, required=True)
    parser.add_argument("--client-json", type=Path, required=True)
    parser.add_argument("--server-json", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        out = inspect_pair(
            _load_exact_one(args.network_json),
            _load_exact_one(args.client_json),
            _load_exact_one(args.server_json),
        )
        dest = args.receipt
        _require(dest.is_absolute() and not dest.exists()
                 and not dest.is_symlink() and dest.parent.is_dir()
                 and not dest.parent.is_symlink(),
                 "evidence path must be new and local")
        with dest.open("x", encoding="utf-8") as handle:
            json.dump(out, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except (ValueError, OSError, TypeError, UnicodeError, json.JSONDecodeError):
        parser.exit(2, "private model network proof BLOCKED\n")
    print(json.dumps({
        "policy_state": out["policy_state"],
        "openhands_live_execution_authorized": False,
        "release_authorized": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
