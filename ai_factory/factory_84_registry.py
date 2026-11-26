"""Unified, read-only 84-source catalog INSIDE CODEN AI Factory.

72 prior file/component candidate references + 12 R29-only proposals.
This module does not fetch, install, import, run, approve or activate the
referenced upstream software. The dated link audit is evidence of reachability
ONLY, never of license approval or security/operational readiness.
"""
import argparse
from collections import Counter, defaultdict
import json
import hashlib
import os
import stat
from pathlib import Path
import re
import sys

from .adopt_first_registry import validate as validate_72
from .r29_factory_scope import validate as validate_r29, EXCLUDED

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "configs" / "factory_72_adopt_first.json"
R29 = ROOT / "configs" / "factory_r29_only_requirements.json"
AUDIT = ROOT / "configs" / "factory_84_source_availability_audit_2026-11-23.json"
V1_1 = ROOT / "configs" / "factory_v1_1_repository_reconciliation.json"
# Git blob identity is a repository consistency pin, not signature or trust approval.
V1_1_GIT_BLOB = "80a6aeb9c9305db15463cea1f07e45051d9dea52"
GATEWAY_REVIEW = ROOT / "configs" / "factory_v1_1_gateway_mcp_review.json"
GATEWAY_REVIEW_BLOB = "e4012a6cd2575fa7d29b740831cc0f4804b12563"
COUNTS = {"P0": 26, "P1": 39, "P2": 19}
SOURCE_ID = re.compile(r"^(?:source-\d{3}|r29-\d{2})$")
REQUIREMENT = re.compile(r"^ADD-(\d{2})$")
WAVES = frozenset({"W0", "W1", "W2", "W3", "W4"})


def read_json(path: Path) -> dict:
    """Read bounded repository-local data only; no HTTP, plugin loader or symlinks."""
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 150_000:
        raise ValueError("untrusted or missing source catalog")
    return json.loads(path.read_text(encoding="utf-8"))


def build_view(base: dict, r29: dict, audit: dict) -> list[dict]:
    """Fail-closed joining of independently maintained, existing catalogs."""
    original = validate_72(base)
    checked = validate_r29(r29, baseline=base)
    extra = checked["extra_sources"]
    if not isinstance(audit, dict) or any(
        type(audit.get(key)) is not int or audit[key] != expected
        for key, expected in {
            "total_catalog_entries": 84,
            "unique_git_repositories": 76,
            "source_admitted_by_this_audit": 0,
            "source_installed_by_this_audit": 0,
            "source_enabled_by_this_audit": 0,
            "un_pinned_sources": 84,
            "missing_independent_license_reviews": 84,
            "missing_independent_security_reviews": 84,
            "distinct_file_links_checked": 48,
            "repository_root_links_checked": 36,
        }.items()
    ):
        raise ValueError("84-source audit inventory or admission drift")
    if audit.get("audit_id") != "CODEN-FACTORY-84-AUDIT-2026-11-23":
        raise ValueError("untrusted dated audit ID")
    if audit.get("paid_usage_authorized") is not False:
        raise ValueError("source audit must authorize no spend")

    entries = audit.get("entries")
    if not isinstance(entries, list) or len(entries) != 84:
        raise ValueError("audit must cover all 84 candidates")
    checked_rows = original + extra
    ids = [x["id"] for x in checked_rows]
    if len(ids) != 84 or len(set(ids)) != 84:
        raise ValueError("duplicate catalog source IDs")
    by_id = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("invalid audit entry")
        source_id = entry.get("id")
        if not isinstance(source_id, str) or source_id in by_id:
            raise ValueError("duplicate or invalid audited source")
        by_id[source_id] = entry
    if set(by_id) != set(ids):
        raise ValueError("audit does not match source inventory")

    linked = defaultdict(set)
    req_waves = defaultdict(set)
    for requirement in checked["requirements"]:
        for source_id in requirement["linked_sources"]:
            linked[source_id].add(requirement["id"])
            req_waves[source_id].add(requirement["wave"])

    combined = []
    for row in checked_rows:
        source_id = row["id"]
        is_extra = source_id.startswith("r29-")
        repo = row["upstream_repo"]
        url = row["url"] if is_extra else row["source_url"]
        item = by_id[source_id]
        if any((
            item.get("source") != repo,
            item.get("url") != url,
            item.get("priority") != row["priority"],
            item.get("name") != (row["why"] if is_extra else row["name"]),
            item.get("reachable_on_date") is not True,
            item.get("pinned_revision") is not None,
            item.get("license_review") != "pending",
            item.get("security_review") != "pending",
            item.get("installed_by_this_catalog") is not False,
            item.get("approved") is not False,
            item.get("enabled") is not False,
            item.get("link_kind") not in ("file_at_moving_HEAD", "repository"),
        )):
            raise ValueError("candidate and dated audit disagree or attempt admission")
        is_file = "/blob/HEAD/" in url
        if (item["link_kind"] == "file_at_moving_HEAD") != is_file:
            raise ValueError("audited link kind mismatch")
        if row.get("pinned_commit") is not None:
            raise ValueError("cannot admit candidate from the catalog")
        combined.append({
            "id": source_id,
            "name": row["why"] if is_extra else row["name"],
            "upstream_repo": repo,
            "source_url": url,
            "priority": row["priority"],
            "wave": row["wave"] if is_extra else None,
            "origin": "r29_addition" if is_extra else "adopt_first_v2",
            "required_by": sorted(linked[source_id]),
            "requirement_waves": sorted(req_waves[source_id]),
            "admission": "proposed_only",
            "pinned_commit": None,
            "license_review": "pending",
            "security_review": "pending",
            "installed": False,
            "approved": False,
            "enabled": False,
        })

    if dict(Counter(x["priority"] for x in combined)) != COUNTS:
        raise ValueError("84-source priority inventory drift")
    if len({x["upstream_repo"].casefold() for x in combined}) != 76:
        raise ValueError("unexpected unique GitHub repository count")
    if audit.get("source_priorities") != COUNTS:
        raise ValueError("audit priorities no longer match registry")
    return combined


def load() -> list[dict]:
    """Load only three repository-tracked JSON documents; do not contact GitHub."""
    return build_view(read_json(BASE), read_json(R29), read_json(AUDIT))


def select(items, *, priority=None, wave=None, requires=None, source_id=None, text=None):
    """Read-only lookup; requirements are index links, never executor permissions."""
    if priority is not None and priority not in COUNTS:
        raise ValueError("invalid priority")
    if wave is not None and wave not in WAVES:
        raise ValueError("invalid wave")
    if requires is not None:
        match = REQUIREMENT.fullmatch(requires) if isinstance(requires, str) else None
        if not match or not 1 <= int(match.group(1)) <= 52 or requires in EXCLUDED:
            raise ValueError("invalid factory requirement")
    if source_id is not None and (
        not isinstance(source_id, str) or SOURCE_ID.fullmatch(source_id) is None
    ):
        raise ValueError("invalid source id")
    if text is not None and not isinstance(text, str):
        raise ValueError("invalid search term")
    term = text.casefold() if text else None
    return [
        row for row in items
        if (priority is None or row["priority"] == priority)
        and (wave is None or row["wave"] == wave or wave in row["requirement_waves"])
        and (requires is None or requires in row["required_by"])
        and (source_id is None or row["id"] == source_id)
        and (term is None or term in row["name"].casefold()
             or term in row["upstream_repo"].casefold()
             or term in row["id"].casefold())
    ]


def _read_pinned_catalog(path, expected_blob):
    path = Path(path)
    if ".." in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("untrusted v1.1 catalog path")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= 150_000:
            raise ValueError("invalid v1.1 catalog")
        raw = stream.read(150_001)
    if len(raw) != info.st_size or len(raw) > 150_000:
        raise ValueError("v1.1 catalog size mismatch")
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw,
                        usedforsecurity=False).hexdigest()
    if blob != expected_blob:
        raise ValueError("v1.1 catalog blob mismatch")
    return json.loads(raw)


def load_v1_1() -> list[dict]:
    """Read exact pinned supplemental discovery index; no admission or execution.

    The checkout and its parent directories must be operator controlled.
    Historical 84-source/47-requirement queries remain independent.
    """
    data = _read_pinned_catalog(V1_1, V1_1_GIT_BLOB)
    rows = data["entries"]
    if (len(rows) != 128 or len({r["repository"].casefold() for r in rows}) != 128
            or sum(len(r["legacy_entry_ids"]) for r in rows) != 84
            or sum(len(r["plan_references"]) for r in rows) != 89
            or any(data.get(k) is not False for k in ("auto_install",
                   "run_unreviewed_components", "paid_usage_enabled", "release_authorized"))
            or any(r.get("approved") is not False or r.get("enabled") is not False
                   or r.get("installed_by_this_catalog") is not False
                   or r.get("pinned_commit") is not None
                   or r.get("decision") not in ("proposed_only", "hold_archived")
                   for r in rows)):
        raise ValueError("v1.1 discovery scope drift")
    return rows


def load_gateway_review() -> list[dict]:
    """Join pinned review metadata to discovery, never to execution authority."""
    data = _read_pinned_catalog(GATEWAY_REVIEW, GATEWAY_REVIEW_BLOB)
    catalog = {row["repository"].casefold(): row for row in load_v1_1()}
    rows = data["entries"]
    if (data.get("status") != "REVIEW_ONLY_UNAPPROVED"
            or data.get("candidate_count") != 6 or len(rows) != 6
            or data.get("first_trial_route") != {
                "model": "openai/local-qwen", "base_url": "http://qwen3:11434/v1",
                "fallback": False, "external_provider_allowed": False}):
        raise ValueError("gateway review scope mismatch")
    seen = set()
    result = []
    for row in rows:
        key = row["repository"].casefold()
        discovery = catalog.get(key)
        if (key in seen or discovery is None or discovery["decision"] != "proposed_only"
                or any(row.get(k) is not False for k in
                       ("approved", "enabled", "installed", "source_to_artifact_verified"))
                or row.get("security_review") != "pending"
                or row.get("license_review") != "pending"
                or row.get("integration_test") != "not_run"
                or not re.fullmatch(r"[0-9a-f]{40}", row["commit"])):
            raise ValueError("gateway candidate drift or admission attempt")
        seen.add(key)
        result.append(dict(row, discovery_decision=discovery["decision"]))
    if Counter(r["role"] for r in result) != {
            "agent_orchestration": 1, "model_gateway": 3, "mcp": 2}:
        raise ValueError("gateway role inventory mismatch")
    return result


def select_v1_1(items, term=""):
    """Search repository metadata only; return disabled candidates."""
    if not isinstance(term, str) or len(term) > 200:
        raise ValueError("invalid repository search")
    term = term.casefold()
    return [r for r in items if term in r["repository"].casefold()
            or any(term in x.casefold() for x in r["plan_references"])]


def main(argv=None):
    parser = argparse.ArgumentParser(description="CODEN 84-source factory registry — NO installation")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--v1-1", action="store_true", help="Query 128 proposed repositories")
    modes.add_argument("--gateway-review", action="store_true", help="Query six review-only gateway and MCP candidates")
    parser.add_argument("--priority", choices=sorted(COUNTS))
    parser.add_argument("--wave", choices=sorted(WAVES))
    parser.add_argument("--requires", help="R29 factory requirement, e.g. ADD-13")
    parser.add_argument("--id", dest="source_id", help="Exact candidate ID, e.g. r29-03")
    parser.add_argument("--contains", dest="text", help="Match source name or GitHub owner/repo")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.gateway_review:
            if any((args.priority, args.wave, args.requires, args.source_id)):
                raise ValueError("legacy filters do not apply to gateway review")
            term = args.text or ""
            if len(term) > 200:
                raise ValueError("invalid search term")
            selected = [row for row in load_gateway_review()
                        if term.casefold() in row["repository"].casefold()
                        or term.casefold() in row["role"].casefold()]
            if args.json:
                print(json.dumps(selected, indent=2, ensure_ascii=False))
            else:
                for row in selected:
                    print(f"{row['repository']} — {row['role']} — REVIEW ONLY")
                print(f"Matching candidates: {len(selected)}; approved: 0; enabled: 0; installed: 0")
            return 0
        if args.v1_1:
            if any((args.priority, args.wave, args.requires, args.source_id)):
                raise ValueError("legacy filters do not apply to v1.1 repositories")
            selected = select_v1_1(load_v1_1(), args.text or "")
            if args.json:
                print(json.dumps(selected, indent=2, ensure_ascii=False))
            else:
                for row in selected:
                    print(f"{row['repository']} — {row['decision']}")
                print(f"Matching repositories: {len(selected)}; admitted: 0; installed: 0")
            return 0
        all_rows = load()
        selected = select(
            all_rows, priority=args.priority, wave=args.wave,
            requires=args.requires, source_id=args.source_id, text=args.text,
        )
    except (OSError, ValueError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"84-source registry BLOCKED ({type(exc).__name__})\n")
    if args.json:
        print(json.dumps(selected, indent=2, ensure_ascii=False))
    elif any((args.priority, args.wave, args.requires, args.source_id, args.text)):
        for row in selected:
            print(f"{row['id']} [{row['priority']}] {row['name']} — {row['upstream_repo']}")
        print(f"Matching proposals: {len(selected)}; admitted: 0; installed: 0")
    else:
        print("CODEN AI Factory: 84 candidate entries (72+12) in 76 upstream GitHub repos")
        print("P0=26 | P1=39 | P2=19 | approved=0 | enabled=0 | installed-by-registry=0")
        print("47 R29 factory-only requirements linked; no paid usage or automatic admission.")
        print("Use --json, --contains, --id, --requires or --wave to query proposals.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
