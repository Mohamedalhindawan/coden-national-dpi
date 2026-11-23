"""Strict, read-only validation of CODEN's source snapshot candidates.

This is a source provenance index, NOT a dependency installer, vulnerability
scanner, license clearance or agent runtime admission service. Git object IDs
are SHA-1, and must not be misrepresented as distribution-file SHA-256 hashes.
"""
import argparse
import hashlib
import os
import stat
import json
from pathlib import Path
import re
import sys

from .adopt_first_registry import validate as validate_original_catalog

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCKS = ROOT / "configs" / "factory_critical_source_pins_v0_1.json"
DEFAULT_BASELINE = ROOT / "configs" / "factory_72_adopt_first.json"
CRITICAL_IDS = frozenset({
    "source-001", "source-002", "source-003", "source-004",
    "source-005", "source-009", "source-011", "source-012",
    "source-013", "source-015", "source-018"
})
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
REPO_NAME = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
EXPECTED_KEYS = frozenset({
    "source_id", "repo", "commit_sha", "evidence_path", "blob_sha",
    "immutable_url", "source_verified", "approved_for_install",
    "runtime_enabled", "license_review", "security_review",
    "dependency_review",
})
REPO_ROOT_PATHS = {"source-009": "README.md", "source-015": "README.md"}


def _read_small_json(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 180_000:
        raise ValueError("untrusted/missing/oversized catalog")
    return json.loads(path.read_text(encoding="utf-8"))


def validate(locks, original):
    """Return the 11 candidate file snapshots only after fail-closed checks."""
    if not isinstance(locks, dict) or not isinstance(original, dict):
        raise ValueError("source-lock data must be objects")
    baseline_rows = validate_original_catalog(original)
    for key, expected in {
        "schema_version": "0.1",
        "project": "CODEN AI Factory",
        "status": "candidate_snapshots_only",
        "baseline_catalog": "configs/factory_72_adopt_first.json",
        "expected_source_count": 11,
        "expected_unique_repo_count": 6,
        "auto_install": False,
        "enable_runtime": False,
        "allow_paid_models": False,
        "authorize_release": False,
    }.items():
        value = locks.get(key)
        if value != expected or type(value) is not type(expected):
            raise ValueError("candidate pins cannot elevate or change control: " + key)
    rows = locks.get("sources")
    if not isinstance(rows, list) or len(rows) != 11:
        raise ValueError("expected exactly 11 unapproved critical-source snapshots")
    baseline = {row["id"]: row for row in baseline_rows}
    found_ids = set()
    repo_commits = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != EXPECTED_KEYS:
            raise ValueError("invalid candidate lock fields")
        ident = row.get("source_id")
        if ident not in CRITICAL_IDS or ident in found_ids:
            raise ValueError("unknown or duplicate critical source")
        found_ids.add(ident)
        expected = baseline[ident]
        repo = row.get("repo")
        if (not isinstance(repo, str) or REPO_NAME.fullmatch(repo) is None
                or repo != expected["upstream_repo"]):
            raise ValueError("source lock is not for the recorded upstream")
        sha, blob = row.get("commit_sha"), row.get("blob_sha")
        if (not isinstance(sha, str) or GIT_SHA.fullmatch(sha) is None
                or not isinstance(blob, str) or GIT_SHA.fullmatch(blob) is None):
            raise ValueError("Git commit and blob metadata require exactly 40 hex chars")
        prior = repo_commits.setdefault(repo, sha)
        if prior != sha:
            raise ValueError("one upstream must use the same immutable commit across files")
        path = row.get("evidence_path")
        if (not isinstance(path, str) or not path or len(path) > 240
                or path.startswith("/") or path.endswith("/")
                or any(p in ("", ".", "..") for p in path.split("/"))
                or "\\" in path or "%" in path
                or any(ord(c) < 32 for c in path)):
            raise ValueError("untrusted or malformed source file path")
        floating = expected["source_url"]
        if "/blob/HEAD/" in floating:
            if path != floating.split("/blob/HEAD/", 1)[1]:
                raise ValueError("evidence path differs from the source catalog")
        elif path != REPO_ROOT_PATHS.get(ident):
            raise ValueError("repo-root source evidence path not in the reviewed shortlist")
        immutable = f"https://github.com/{repo}/blob/{sha}/{path}"
        if row.get("immutable_url") != immutable:
            raise ValueError("source must use immutable official GitHub commit URL")
        if row.get("source_verified") != "github_api_revision_and_blob_metadata":
            raise ValueError("source evidence status is untrusted")
        if row.get("approved_for_install") is not False or row.get("runtime_enabled") is not False:
            raise ValueError("source snapshots must not grant admission or runtime rights")
        for field in ("license_review", "security_review", "dependency_review"):
            if row.get(field) != "pending":
                raise ValueError("cannot approve review merely by pinning a source")
    if found_ids != CRITICAL_IDS or len(repo_commits) != 6:
        raise ValueError("critical-source inventory incomplete")
    return rows


def load(lock_path=DEFAULT_LOCKS, baseline_path=DEFAULT_BASELINE):
    return validate(_read_small_json(lock_path), _read_small_json(baseline_path))


def select(rows, *, source_id=None):
    if source_id is None:
        return list(rows)
    if source_id not in CRITICAL_IDS:
        raise ValueError("unknown critical source id")
    selection = [row for row in rows if row["source_id"] == source_id]
    if len(selection) != 1:
        raise ValueError("missing critical source record")
    return selection



def verify_staged_blob(file_path, expected_blob_sha, *, max_bytes=2_000_000):
    """Verify one staged, local regular file against its pinned Git blob SHA-1.

    Checks byte-for-byte Git object identity only. This does NOT execute the
    staged file, certify source authenticity against GitHub, grant install
    permission or replace modern SHA-256 signed-distribution verification.
    """
    if (not isinstance(expected_blob_sha, str)
            or GIT_SHA.fullmatch(expected_blob_sha) is None):
        raise ValueError("expected Git blob object SHA-1 must be 40 lowercase hex characters")
    if type(max_bytes) is not int or not 1 <= max_bytes <= 2_000_000:
        raise ValueError("invalid maximum staged source size")
    if not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("safe no-follow file access unavailable")
    flags = os.O_RDONLY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    try:
        fd = os.open(file_path, flags)
    except OSError as exc:
        raise ValueError("cannot open staged source without following symlinks") from exc
    try:
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= max_bytes:
                raise ValueError("staged source is not a bounded regular file")
            content = stream.read(max_bytes + 1)
            if len(content) != info.st_size:
                raise ValueError("staged source size changed while reading")
    except OSError as exc:
        raise ValueError("could not securely read staged source file") from exc
    # Git SHA-1 object ID is SHA1("blob " + decimal length + NUL + file bytes).
    git_blob_sha1 = hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\0" + content
    ).hexdigest()
    if git_blob_sha1 != expected_blob_sha:
        raise ValueError("staged source bytes differ from pinned Git blob object")
    return {
        "git_blob_sha1": git_blob_sha1,
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
        "integrity": "local_bytes_match_recorded_git_blob_object",
        "install_authorized": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only 11-source immutable GitHub candidate snapshots")
    parser.add_argument("--source-id", choices=sorted(CRITICAL_IDS))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--verify-file", type=Path, help="Verify local bytes against locked Git blob, never execute")
    args = parser.parse_args(argv)
    try:
        rows = select(load(), source_id=args.source_id)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Source locks BLOCKED ({type(exc).__name__})\n")
    if args.verify_file is not None:
        if args.source_id is None:
            parser.exit(2, "Source locks BLOCKED (explicit --source-id required)\n")
        try:
            proof = verify_staged_blob(args.verify_file, rows[0]["blob_sha"])
        except ValueError as exc:
            parser.exit(2, f"Staged source integrity BLOCKED ({type(exc).__name__})\n")
        print(json.dumps({"source_id": rows[0]["source_id"], **proof}, sort_keys=True))
    elif args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        for row in rows:
            print(f"{row['source_id']} {row['repo']} @ {row['commit_sha'][:12]} (NOT APPROVED)")
        print(f"Verified snapshot metadata: {len(rows)}; enabled=0; installed=0; accepted=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
