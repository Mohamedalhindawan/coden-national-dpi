"""CODEN Playbook V5 R29 factory-only Adopt-First requirements (read-only).

This module neither installs upstream code nor promotes a requirement to an
implemented/approved state. It reads one tracked JSON from the local checkout,
cross-checking the existing 72-source registry before returning references.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "configs" / "factory_r29_only_requirements.json"
BASE = ROOT / "configs" / "factory_72_adopt_first.json"
COUNTS = {"W0": 19, "W1": 12, "W2": 5, "W3": 8, "W4": 3}
EXCLUDED = {"ADD-32", "ADD-33", "ADD-34", "ADD-36", "ADD-40"}
GATES = ["G0", "G1", "G2", "G3", "G4", "G5", "G6", "G8"]
TESTS = [f"T{i:02d}" for i in range(1, 11)] + ["T12"]
PILOTS = [f"PILOT-{i:02d}" for i in range(1, 6)]
GITHUB_REPO = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")
SAFE_ADD = re.compile(r"^ADD-(\d{2})$")


def validate(data, *, baseline=None):
    if not isinstance(data, dict):
        raise ValueError("not an object")
    for k, v in {
        "schema_version": "1.0.0",
        "scope": "CODEN_AI_FACTORY_ONLY",
        "source_document_id": "CODEN-PLAYBOOK-V5-R29",
        "document_status": "UNAPPROVED",
        "execution_status": "not_proven_by_blueprint",
        "baseline_adopt_first_manifest": "configs/factory_72_adopt_first.json",
        "baseline_source_count": 72,
        "extra_source_count": 12,
        "combined_candidate_entries": 84,
        "auto_install": False,
        "automatic_merge": False,
        "paid_calls": False,
        "excluded_gate": "G7",
        "excluded_scenario": "T11",
    }.items():
        if data.get(k) != v or type(data.get(k)) is not type(v):
            raise ValueError("invalid factory-only control " + k)
    if set(data.get("excluded_additions", ())) != EXCLUDED:
        raise ValueError("excluded non-factory additions changed")
    rows, extra = data.get("requirements"), data.get("extra_sources")
    if not isinstance(rows, list) or len(rows) != 47:
        raise ValueError("expected 47 factory-only requirements")
    if not isinstance(extra, list) or len(extra) != 12:
        raise ValueError("expected 12 new proposed OSS source candidates")
    if not isinstance(baseline, dict):
        raise ValueError("existing 72-source registry required")
    try:
        from .adopt_first_registry import validate as validate_baseline
        base_rows = validate_baseline(baseline)
    except (ImportError, KeyError, TypeError) as exc:
        raise ValueError("existing baseline unavailable") from exc
    base_ids = {x["id"] for x in base_rows}
    base_repos = {x["upstream_repo"].casefold() for x in base_rows}
    new_ids = set()
    new_repos = set()
    for i, candidate in enumerate(extra, 1):
        if not isinstance(candidate, dict) or candidate.get("id") != f"r29-{i:02d}":
            raise ValueError("R29 source id must be unique and ordered")
        repo = candidate.get("upstream_repo")
        if not isinstance(repo, str) or GITHUB_REPO.fullmatch(repo) is None:
            raise ValueError("invalid proposed GitHub repository")
        if repo.casefold() in base_repos or repo.casefold() in new_repos:
            raise ValueError("upstream duplicates an existing proposed source")
        if candidate.get("url") != "https://github.com/" + repo:
            raise ValueError("only verified GitHub repository paths accepted")
        if candidate.get("pinned_commit") is not None:
            raise ValueError("not admitted by importing proposal")
        if candidate.get("license_review") != "pending" or candidate.get("security_review") != "pending":
            raise ValueError("cannot approve licensing/security by catalog")
        if candidate.get("installed") is not False or candidate.get("enabled") is not False or candidate.get("approved") is not False:
            raise ValueError("no source may be auto-enabled or installed")
        if candidate.get("wave") not in COUNTS or candidate.get("priority") not in {"P0", "P1", "P2"}:
            raise ValueError("invalid proposed source phase")
        new_repos.add(repo.casefold())
        new_ids.add(candidate["id"])
    requirement_ids = set()
    wave_counts = Counter()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid requirement")
        rid = row.get("id")
        if not isinstance(rid, str) or SAFE_ADD.fullmatch(rid) is None or rid in requirement_ids or rid in EXCLUDED:
            raise ValueError("invalid/duplicate/non-factory addition")
        requirement_ids.add(rid)
        if row.get("wave") not in COUNTS:
            raise ValueError("invalid R29 execution wave")
        wave_counts[row["wave"]] += 1
        for key in ("title", "acceptance", "source_document", "source_reference"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError("missing R29 evidence reference")
        if row["source_document"] != "CODEN-PLAYBOOK-V5-R29":
            raise ValueError("unknown source document")
        number = int(rid[-2:])
        expected_priority = (
            "P0" if 41 <= number <= 46 else
            "P1" if number in {47, 48, 49, 51} else
            "P2" if number in {50, 52} else None
        )
        if row.get("priority_in_source") != expected_priority:
            raise ValueError("priority must match R29 or remain unspecified")
        links = row.get("linked_sources")
        if not isinstance(links, list) or not links or len(links) != len(set(links)):
            raise ValueError("empty/duplicated requirement source references")
        if not set(links) <= base_ids | new_ids:
            raise ValueError("unregistered source reference")
        if row.get("implemented_by_import") is not False or row.get("tested_by_blueprint") is not False:
            raise ValueError("requirements are proposed, not implemented")
    if requirement_ids != {f"ADD-{i:02d}" for i in range(1, 53)} - EXCLUDED:
        raise ValueError("R29 scope incomplete")
    if dict(wave_counts) != COUNTS:
        raise ValueError("wrong wave assignments")
    for field, ids in (("gates", GATES), ("reference_tests", TESTS), ("pilots", PILOTS)):
        arr = data.get(field)
        if not isinstance(arr, list) or [x.get("id") for x in arr if isinstance(x, dict)] != ids or len(arr) != len(ids):
            raise ValueError("missing R29 acceptance scenario " + field)
    return data


def load(path=SPEC):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 150_000:
        raise ValueError("untrusted R29 requirement catalog")
    if BASE.is_symlink() or not BASE.is_file() or BASE.stat().st_size > 150_000:
        raise ValueError("untrusted base registry")
    data = json.loads(path.read_text(encoding="utf-8"))
    baseline = json.loads(BASE.read_text(encoding="utf-8"))
    return validate(data, baseline=baseline)


def filter_requirements(requirements, *, wave=None):
    if wave is not None and wave not in COUNTS:
        raise ValueError("wave must be W0–W4")
    return [x for x in requirements if wave is None or x["wave"] == wave]


def main(argv=None):
    parser = argparse.ArgumentParser(description="R29 factory-only requirements (read-only)")
    parser.add_argument("--wave", choices=sorted(COUNTS))
    parser.add_argument("--missing-sources", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        data = load()
        rows = (data["extra_sources"] if args.missing_sources
                else filter_requirements(data["requirements"], wave=args.wave))
    except (OSError, ValueError, json.JSONDecodeError, UnicodeError) as exc:
        parser.exit(2, f"R29 source scope BLOCKED ({type(exc).__name__})\n")
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        for row in rows:
            name = row.get("title") or row.get("upstream_repo")
            print(f"{row['id']} [{row['wave']}] {name}")
        print(f"Count: {len(rows)} | approved: 0 | installed by catalog: 0 | auto-spend: $0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
