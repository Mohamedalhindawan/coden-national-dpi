"""Strict, read-only validation of CODEN's source snapshot candidates.

This is a source provenance index, NOT a dependency installer, vulnerability
scanner, license clearance or agent runtime admission service. Git object IDs
are SHA-1, and must not be misrepresented as distribution-file SHA-256 hashes.
"""
import argparse
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


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only 11-source immutable GitHub candidate snapshots")
    parser.add_argument("--source-id", choices=sorted(CRITICAL_IDS))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        rows = select(load(), source_id=args.source_id)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Source locks BLOCKED ({type(exc).__name__})\n")
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        for row in rows:
            print(f"{row['source_id']} {row['repo']} @ {row['commit_sha'][:12]} (NOT APPROVED)")
        print(f"Verified snapshot metadata: {len(rows)}; enabled=0; installed=0; accepted=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
