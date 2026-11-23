"""Offline, review-only reuse of three real, immutable GitHub Spec Kit templates.

A bounded source asset copier, NOT a code executor, a generated specification,
a model call, or a component admission/approval operation. No network access.
The three source IDs stay proposed/disabled in the 84-source catalog.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys

from .factory_source_locks import load as load_locks, verify_staged_blob

SPEC_KIT_COMMIT = "fa7c88fb1c56034a10c4553c9d5527d1a62fc919"
LICENSE_BLOB_SHA = "28a50fa22639e32febe14e4ffc7a732b0ba8c90a"
ASSETS = (
    Path(__file__).resolve().parents[1]
    / "third_party" / "source_pilots" / "spec-kit-fa7c88f"
)
TEMPLATES = {
    "source-011": "spec-template.md",
    "source-012": "plan-template.md",
    "source-013": "tasks-template.md",
}
OUTPUT_NAMES = {
    "source-011": "spec.md",
    "source-012": "plan.md",
    "source-013": "tasks.md",
}
UPSTREAM_PATHS = {
    "source-011": "templates/spec-template.md",
    "source-012": "templates/plan-template.md",
    "source-013": "templates/tasks-template.md",
}


def _read_checked(path: Path, sha: str) -> bytes:
    """Read a regular non-symlink file without following links and verify bytes."""
    if not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("secure source file reading unavailable")
    # Reuse the independently tested Git-object verification before staging.
    verify_staged_blob(path, sha, max_bytes=100_000)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size < 100_000:
                raise ValueError("untrusted pinned source asset")
            content = stream.read(100_001)
    except OSError as exc:
        raise ValueError("cannot safely read pinned source asset") from exc
    blob = hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\0" + content
    ).hexdigest()
    if blob != sha:
        raise ValueError("source asset changed after initial hash check")
    return content


def validated_templates():
    """Return immutable source bytes and metadata, never executable behavior."""
    pins = {row["source_id"]: row for row in load_locks()}
    outputs = {}
    proofs = {}
    for source_id, local_name in TEMPLATES.items():
        lock = pins[source_id]
        if (lock["repo"] != "github/spec-kit"
                or lock["commit_sha"] != SPEC_KIT_COMMIT
                or lock["evidence_path"] != UPSTREAM_PATHS[source_id]
                or lock["approved_for_install"] is not False
                or lock["runtime_enabled"] is not False
                or lock["license_review"] != "pending"
                or lock["security_review"] != "pending"
                or lock["dependency_review"] != "pending"):
            raise ValueError("Spec Kit source is not from recorded unapproved pin")
        content = _read_checked(ASSETS / local_name, lock["blob_sha"])
        outputs[OUTPUT_NAMES[source_id]] = content
        proofs[source_id] = {
            "upstream_file": lock["evidence_path"],
            "git_blob_sha1": lock["blob_sha"],
            "sha256": hashlib.sha256(content).hexdigest(),
        }
    license_bytes = _read_checked(ASSETS / "LICENSE", LICENSE_BLOB_SHA)
    if not license_bytes.startswith(b"MIT License\n") or b"Copyright GitHub, Inc." not in license_bytes:
        raise ValueError("required MIT attribution missing")
    outputs["LICENSE"] = license_bytes
    return outputs, proofs


def stage(destination: Path):
    """Create a fresh review-only folder with exact sources and license."""
    destination = Path(destination)
    # Do not create arbitrary parent directories, overwrite data or follow
    # symlinks. Source verification is entirely completed before any output.
    if (not destination.is_absolute()
            or ".." in destination.parts or destination.name in ("", ".", "..")
            or destination.exists() or destination.is_symlink()
            or destination.parent.is_symlink()
            or not destination.parent.is_dir()):
        raise ValueError("pilot destination must be a fresh folder under a real parent")
    outputs, proofs = validated_templates()
    receipt = {
        "status": "awaiting_human_review",
        "upstream_repo": "github/spec-kit",
        "upstream_commit": SPEC_KIT_COMMIT,
        "source_kind": "byte_identical_offline_markdown_source_templates",
        "sources": proofs,
        "license": "MIT",
        "license_blob_sha1": LICENSE_BLOB_SHA,
        "license_sha256": hashlib.sha256(outputs["LICENSE"]).hexdigest(),
        "release_authorized": False,
        "runtime_enabled": False,
        "paid_calls": 0,
        "network_calls_by_stager": 0,
        "note": "Original templates only. No automatic filling, installation, code execution or deployment.",
    }
    destination.mkdir(mode=0o700)
    try:
        for name, content in outputs.items():
            with (destination / name).open("xb") as stream:
                stream.write(content)
        with (destination / "evidence.json").open("x", encoding="utf-8") as stream:
            json.dump(receipt, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except Exception:
        shutil.rmtree(destination)
        raise
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline Spec Kit source pilot — human review only")
    parser.add_argument("--output", required=True, type=Path, help="New absolute directory for candidate docs")
    args = parser.parse_args(argv)
    try:
        receipt = stage(args.output)
    except (OSError, ValueError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Spec Kit source pilot BLOCKED ({type(exc).__name__})\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
