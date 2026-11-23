"""Fail-closed Docker inspect verifier for a synthetic isolation smoke pilot.

This does not start a Docker container or execute arbitrary commands.
The dedicated CI job supplies actual inspected Docker state and separately
verifies guest cgroup/filesystem/no-new-privileges constraints.
No authorization to start OpenHands or approve a production workload.
"""
import argparse
import json
import os
from pathlib import Path
import stat
import sys

TEST_IMAGE = (
    "docker.io/library/busybox@sha256:"
    "73aaf090f3d85aa34ee199857f03fa3a95c8ede2ffd4cc2cdb5b94e566b11662"
)
CPU_NANO = 1_000_000_000
MEMORY_BYTES = 256 * 1024 * 1024
PIDS = 64
TMPFS = "rw,noexec,nosuid,nodev,size=16m,mode=1777"
MAX_INSPECT_BYTES = 120_000


def _require(condition, message):
    if not condition:
        raise ValueError("Docker isolation policy BLOCKED: " + message)


def inspect_config(data):
    """Verify ONE Docker-created container's immutable config, no live permission.

    HostConfig is evidence of requested flags, not independent evidence of
    kernel enforcement or proof of a rootless trusted Docker daemon.
    """
    _require(isinstance(data, dict), "inspect object missing")
    state = data.get("State")
    cfg = data.get("Config")
    host = data.get("HostConfig")
    _require(all(isinstance(x, dict) for x in (state, cfg, host)),
             "missing Docker inspect sections")
    _require(state.get("Running") is True, "fixture must be running")
    _require(cfg.get("Image") == TEST_IMAGE, "unexpected image tag/digest")
    _require(cfg.get("User") == "65534:65534", "root/nonfixed identity forbidden")
    env = cfg.get("Env")
    _require(isinstance(env, list) and len(env) <= 2
             and all(isinstance(v, str) and v.startswith("PATH=")
                     and len(v) <= 600 for v in env),
             "unknown or inherited environment variables")
    _require(host.get("NanoCpus") == CPU_NANO and type(host.get("NanoCpus")) is int,
             "CPU cgroup cap not requested")
    _require(host.get("Memory") == MEMORY_BYTES and type(host.get("Memory")) is int,
             "memory cap not requested")
    _require(host.get("MemorySwap") == MEMORY_BYTES and type(host.get("MemorySwap")) is int,
             "swap beyond memory forbidden")
    _require(host.get("PidsLimit") == PIDS and type(host.get("PidsLimit")) is int,
             "PID cap not requested")
    _require(host.get("CapDrop") == ["ALL"] and host.get("CapAdd") in (None, []),
             "capability drop not complete")
    _require(host.get("Privileged") is False, "privileged forbidden")
    _require(host.get("ReadonlyRootfs") is True, "read-only root missing")
    _require(host.get("NetworkMode") == "none", "outbound network not denied")
    _require(host.get("PidMode") == "private", "PID host namespace forbidden")
    _require(host.get("IpcMode") == "private", "IPC host namespace forbidden")
    _require(host.get("SecurityOpt") == ["no-new-privileges"],
             "no-new-privileges absent")
    _require(host.get("Binds") in (None, [])
             and host.get("Devices") in (None, [])
             and host.get("Mounts") in (None, []),
             "host bindings/devices forbidden")
    tmpfs = host.get("Tmpfs")
    _require(isinstance(tmpfs, dict) and tmpfs == {"/tmp": TMPFS},
             "only precisely bounded tmpfs permitted")
    mounts = data.get("Mounts")
    _require(isinstance(mounts, list)
             and all(isinstance(x, dict) and
                     x.get("Type") == "tmpfs" and
                     x.get("Destination") == "/tmp"
                     for x in mounts),
             "unexpected host or named volume")
    _require(host.get("AutoRemove") is True, "container must auto-clean")
    restart = host.get("RestartPolicy")
    _require(isinstance(restart, dict) and restart.get("Name") == "no",
             "restart is not permitted")
    _require(isinstance(data.get("Image"), str) and
             data["Image"].startswith("sha256:") and len(data["Image"]) == 71,
             "missing Docker image content identity")
    return {
        "source_id": "source-004",
        "test_image_upstream": "Docker Official Images/busybox:1.36.1",
        "image": TEST_IMAGE,
        "policy_state": "CONSTRAINED_FIXTURE_METADATA_PASS",
        "scope": "SYNTHETIC_BUSYBOX_FIXTURE_ONLY",
        "cpu_limit_configured": True,
        "memory_limit_configured": True,
        "pids_limit_configured": True,
        "all_capabilities_dropped": True,
        "nonroot_container_user": True,
        "read_only_rootfs": True,
        "network_disabled": True,
        "no_privileged_mounts": True,
        "docker_host_rootless_verified": False,
        "agent_server_image_and_sbom_verified": False,
        "actual_guest_limits_verified_by_this_module": False,
        "openhands_runtime_state": "BLOCKED_FOR_REAL_SESSION",
        "openhands_live_execution_authorized": False,
        "factory_production_authorized": False,
        "release_authorized": False,
        "paid_calls": 0,
        "warning": (
            "Inspect data verifies the selected Docker configuration only. "
            "Independent guest cgroup/network/negative tests and a rootless "
            "host, real OpenHands image SBOM and SDK locking are still needed."
        ),
    }


def inspect_file(path):
    """Only read a bounded pre-existing local regular JSON file; no exec."""
    file = Path(path)
    if file.is_symlink() or not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("untrusted inspect file")
    fd = os.open(file, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_INSPECT_BYTES:
            raise ValueError("untrusted inspect file size/type")
        with os.fdopen(os.dup(fd), "rb") as f:
            content = f.read(MAX_INSPECT_BYTES + 1)
        if len(content) != info.st_size:
            raise ValueError("inspect file modified during read")
    finally:
        os.close(fd)
    values = json.loads(content.decode("utf-8"))
    if not isinstance(values, list) or len(values) != 1:
        raise ValueError("must inspect exactly one container")
    return inspect_config(values[0])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspect-json", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        receipt = inspect_file(args.inspect_json)
        if (not args.receipt.is_absolute() or args.receipt.exists()
                or args.receipt.is_symlink() or args.receipt.parent.is_symlink()
                or not args.receipt.parent.is_dir()):
            raise ValueError("trusted fresh absolute receipt path needed")
        with args.receipt.open("x", encoding="utf-8") as f:
            json.dump(receipt, f, sort_keys=True, indent=2)
            f.write("\n")
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, json.JSONDecodeError):
        parser.exit(2, "Docker resource boundary BLOCKED\n")
    print(json.dumps({
        "policy_state": receipt["policy_state"],
        "image": receipt["image"],
        "openhands_live_execution_authorized": False,
        "release_authorized": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
