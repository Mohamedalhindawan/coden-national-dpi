"""CODEN 84-source Adopt-First admission review backlog (read-only).

Loads real, strictly validated factory catalog data. The genuine Qwen-generated
candidate is preserved as a QUARANTINED source artifact and hash-verified as
evidence ONLY: never import, eval, compile, execute or authorize that code.
All 84 entries currently require independent license AND security review.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

from . import factory_84_registry

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = ROOT / "ai_factory" / "review_candidates" / "qwen_oss_admission_transform.py"
CANDIDATE_SOURCE_SHA256 = "c410f3e98b7e01e9208954da558cd6b94ee22fc0fe5fa04fa3a1027db401f9cc"
MODEL_CANDIDATE_PYZ_SHA256 = "e011e317dc06efb6870978d40e4d17263a308c30655a565518006af23b564573"
ORIGIN_RUN = "https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45239038437"
PRIORITIES = ("P0", "P1", "P2")
EXPECTED = {"P0": 26, "P1": 39, "P2": 19}
SOURCE_ID = re.compile(r"^(?:source-\d{3}|r29-\d{2})$")


def _verify_quarantine():
    """Verify exact source extracted from real Qwen package, with zero execution."""
    path = Path(CANDIDATE_PATH)
    if path.is_symlink() or not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("untrusted generated candidate path")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if not stat.S_ISREG(metadata.st_mode) or not 0 < metadata.st_size <= 4096:
                raise ValueError("invalid generated candidate source")
            content = stream.read(4097)
            if len(content) != metadata.st_size:
                raise ValueError("source changed during read")
    except OSError as exc:
        raise ValueError("cannot safely inspect generated candidate") from exc
    if hashlib.sha256(content).hexdigest() != CANDIDATE_SOURCE_SHA256:
        raise ValueError("quarantined candidate bytes differ from real model artifact")
    return CANDIDATE_SOURCE_SHA256


def build_report():
    """Strict no-write view over 84 real records: no admission state changes."""
    _verify_quarantine()
    rows = factory_84_registry.load()
    if not isinstance(rows, list) or len(rows) != 84:
        raise ValueError("expected 84 verified factory candidates")
    ids = set()
    repos = set()
    by_priority = {k: {"sources": 0, "pending_checks": 0} for k in PRIORITIES}
    results = []
    for item in rows:
        if not isinstance(item, dict):
            raise ValueError("invalid catalog row")
        source_id = item.get("id")
        priority = item.get("priority")
        repository = item.get("upstream_repo")
        if (not isinstance(source_id, str) or SOURCE_ID.fullmatch(source_id) is None
                or source_id in ids
                or priority not in EXPECTED
                or not isinstance(repository, str) or "/" not in repository
                or not isinstance(item.get("source_url"), str)
                or not item["source_url"].startswith(f"https://github.com/{repository}/")
                   and item["source_url"] != f"https://github.com/{repository}"
                or item.get("license_review") != "pending"
                or item.get("security_review") != "pending"
                or item.get("admission") != "proposed_only"
                or item.get("approved") is not False
                or item.get("enabled") is not False
                or item.get("installed") is not False
                or item.get("pinned_commit") is not None):
            raise ValueError("catalog row is missing or attempts source promotion")
        ids.add(source_id)
        repos.add(repository.casefold())
        by_priority[priority]["sources"] += 1
        # These labels are from the independently verified source fields;
        # NEVER interpreted as approval or permission to execute.
        flags = ["license_pending", "security_pending"]
        by_priority[priority]["pending_checks"] += len(flags)
        results.append({
            "id": source_id,
            "upstream_repo": repository,
            "priority": priority,
            "pending_flags": flags,
        })
    if ({p: by_priority[p]["sources"] for p in PRIORITIES} != EXPECTED
            or len(ids) != 84 or len(repos) != 76):
        raise ValueError("source registry no longer matches verified 84-source snapshot")
    return {
        "source": "verified_84_source_adopt_first_registry",
        "metric_kind": "read_only_source_review_backlog",
        "source_entries": len(rows),
        "unique_upstream_repositories": len(repos),
        "source_approval_pending": len(rows),
        "license_review_pending": len(rows),
        "security_review_pending": len(rows),
        "review_checks_pending": 2 * len(rows),
        "by_priority": by_priority,
        "rows": results,
        "candidate_source_sha256": CANDIDATE_SOURCE_SHA256,
        "model_candidate_pyzip_sha256": MODEL_CANDIDATE_PYZ_SHA256,
        "candidate_review_evidence": ORIGIN_RUN,
        "candidate_status": "awaiting_human_review",
        "model_candidate_executed_by_report": False,
        "source_catalog_modified": False,
        "release_authorized": False,
        "paid_calls": 0,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only real 84-source license/security backlog")
    parser.add_argument("--json", action="store_true", help="Show complete sanitized report")
    args = parser.parse_args(argv)
    try:
        report = build_report()
    except (OSError, ValueError, TypeError, UnicodeError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(2, f"84-source admission report BLOCKED ({type(exc).__name__})\n")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print("CODEN 84-source review backlog (REAL CATALOG, READ ONLY)")
        print("Sources: 84 | unique GitHub repos: 76")
        print("Pending license reviews: 84 | pending security reviews: 84")
        print("Pending checks total: 168 | approved/enabled from report: 0")
        print("P0: 52 checks | P1: 78 checks | P2: 38 checks")
        print("Qwen candidate: quarantined for human review; never executed by report.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
