"""Read-only pinned OpenHands SDK source compatibility/safety witness.

This inspects REAL upstream source bytes, NEVER imports or executes them.
It cannot validate Docker daemon/SDK dependency security or run an agent.
A verified source with missing resource controls stays BLOCKED for a live run.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tomllib

ASSETS = (Path(__file__).resolve().parents[1] /
          "third_party/source_pilots/openhands-077f3fad")
UPSTREAM_COMMIT = "077f3fad6d31cd852be5c87176e0a93c3b446126"
FILES = {
    "workspace.py": "0a28fb27053f5e830b91914bdb4592aec30d3cc1",
    "sdk-pyproject.toml": "1304f0106a4229451882dcf28501df594a921d15",
    "workspace-pyproject.toml": "3da2c0bdc2c818d9b3aedc3ae7f64a30b0a31034",
    "LICENSE": "b0bd86a6335a564bd3766666bebbf014fd6a8013",
}
# Presence in GitHub upstream code does not prove enforcement in the image.
RESOURCE_FLAGS = {
    "cpu_cgroup": "--cpus",
    "memory_cgroup": "--memory",
    "pids_limit": "--pids-limit",
    "capability_drop": "--cap-drop",
    "read_only_root": "--read-only",
}


def _verified_bytes(path: Path, blob_sha: str) -> bytes:
    """Read a bounded regular source file once; reject symlinks and drift."""
    path = Path(path)
    if path.is_symlink() or not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("untrusted source path")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as handle:
            info = os.fstat(handle.fileno())
            if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= 160_000:
                raise ValueError("untrusted source size/type")
            data = handle.read(160_001)
            if len(data) != info.st_size:
                raise ValueError("source size changed during read")
    except OSError as exc:
        raise ValueError("cannot safely read source") from exc
    digest = hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\x00" + data
    ).hexdigest()
    if digest != blob_sha:
        raise ValueError("pinned Git blob content mismatch")
    return data


def inspect() -> dict:
    """Verify official source snapshots and report missing capabilities."""
    if ASSETS.is_symlink() or not ASSETS.is_dir():
        raise ValueError("untrusted upstream source directory")
    data = {name: _verified_bytes(ASSETS / name, blob)
            for name, blob in FILES.items()}
    lic = data["LICENSE"].decode("utf-8")
    if not lic.startswith("MIT License\n") or "OpenHands contributors" not in lic:
        raise ValueError("missing pinned license attribution")
    sdk = tomllib.loads(data["sdk-pyproject.toml"].decode("utf-8"))["project"]
    workspace = tomllib.loads(data["workspace-pyproject.toml"].decode("utf-8"))["project"]
    if (sdk.get("name") != "openhands-sdk" or
            workspace.get("name") != "openhands-workspace" or
            sdk.get("version") != "1.63.1" or
            workspace.get("version") != "1.63.1" or
            sdk.get("requires-python") != ">=3.12" or
            workspace.get("requires-python") != ">=3.12" or
            not any(dep.startswith("openhands-agent-server")
                    for dep in workspace.get("dependencies", []))):
        raise ValueError("unrecognized pinned SDK/workspace package metadata")

    tree = ast.parse(data["workspace.py"].decode("utf-8"))
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == "DockerWorkspace"]
    if len(classes) != 1:
        raise ValueError("missing upstream DockerWorkspace class")
    cls = classes[0]
    declared_fields = {
        n.target.id for n in cls.body
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
    }
    expected_fields = {
        "server_image", "forward_env", "volumes", "network",
        "extra_ports", "enable_gpu", "host_port", "health_check_timeout",
    }
    if not expected_fields <= declared_fields:
        raise ValueError("incompatible upstream DockerWorkspace fields")
    starts = [n for n in cls.body if isinstance(n, ast.FunctionDef)
              and n.name == "_start_container"]
    inits = [n for n in cls.body if isinstance(n, ast.FunctionDef)
             and n.name == "model_post_init"]
    if len(starts) != 1 or len(inits) != 1:
        raise ValueError("unrecognized upstream Docker lifecycle")
    launches_during_init = any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        and n.func.attr == "_start_container"
        for n in ast.walk(inits[0])
    )
    if not launches_during_init:
        raise ValueError("cannot prove lifecycle from pinned source")
    docker_literals = {
        n.value for n in ast.walk(starts[0])
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    }
    if not {"docker", "run", "--network", "--rm", "--ulimit"} <= docker_literals:
        raise ValueError("upstream Docker run configuration changed unexpectedly")
    missing = sorted(
        name for name, flag in RESOURCE_FLAGS.items()
        if flag not in docker_literals
    )
    # Never turn source-analysis evidence into Docker execution authorization.
    return {
        "source_id": "source-004",
        "upstream_repo": "OpenHands/software-agent-sdk",
        "upstream_commit": UPSTREAM_COMMIT,
        "upstream_blob_sha1": FILES["workspace.py"],
        "source_integrity_verified": True,
        "package_version": "1.63.1",
        "license": "MIT",
        "upstream_workspace_starts_container": launches_during_init,
        "missing_docker_controls": missing,
        "runtime_state": "BLOCKED_FOR_REAL_SESSION",
        "sdk_install_status": "not_installed_by_preflight",
        "docker_container_started": False,
        "model_invoked": False,
        "paid_calls": 0,
        "live_agent_execution_authorized": False,
        "release_authorized": False,
        "warning": (
            "Immutable Git source file equivalence only. No pinned full dependency "
            "SBOM, image digest or independent Docker network/cgroup verification."
        ),
    }


def write_receipt(path: Path) -> dict:
    """Create one new local JSON evidence file, no overwrite or execution."""
    path = Path(path)
    if (not path.is_absolute() or ".." in path.parts or path.exists()
            or path.is_symlink() or path.parent.is_symlink()
            or not path.parent.is_dir()):
        raise ValueError("trusted fresh absolute receipt path required")
    receipt = inspect()
    with path.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, ensure_ascii=True, sort_keys=True, indent=2)
        stream.write("\n")
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description="Real immutable OpenHands source review only; no session")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        receipt = write_receipt(args.receipt) if args.receipt else inspect()
    except (OSError, ValueError, SyntaxError, TypeError, UnicodeError, KeyError) as exc:
        parser.exit(2, f"OpenHands source preflight BLOCKED ({type(exc).__name__})\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
