"""Read-only 72-source Adopt-First registry for CODEN AI Factory.

No dynamic imports, installs, credential handling, HTTP requests, code execution,
model invocation, automatic approval, or production changes happen here.
Do not mistake a GitHub URL for a verified or pinned dependency.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

REGISTRY = Path(__file__).resolve().parents[1] / "configs" / "factory_72_adopt_first.json"
PRIORITIES = {"P0", "P1", "P2"}
SAFE_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
EXPECTED_ITEM_KEYS = {
    "id", "name", "priority", "upstream_repo", "source_url", "pinned_commit",
    "source_verification", "license_review", "security_review",
    "installed_by_registry", "approved", "enabled",
}
EXPECTED_COUNTS = {"P0": 23, "P1": 33, "P2": 16}


def validate(document):
    """Fail closed if registry metadata silently promotes a source to execution."""
    if not isinstance(document, dict) or (
        document.get("schema_version") != "1.0.0"
        or document.get("project") != "CODEN AI Factory"
        or document.get("registry_status") != "proposed_only"
        or document.get("manifest_version") != "v2.0"
        or document.get("candidate_count") != 72
    ):
        raise ValueError("invalid factory catalog envelope")
    for guard in (
        "auto_install", "production_deploy_enabled",
        "paid_usage_enabled", "run_unreviewed_components"
    ):
        if document.get(guard) is not False:
            raise ValueError("factory source admission cannot be enabled by registry")
    rows = document.get("candidates")
    if not isinstance(rows, list) or len(rows) != 72:
        raise ValueError("factory catalog must contain exactly 72 entries")
    priorities = Counter()
    for i, row in enumerate(rows, 1):
        if not isinstance(row, dict) or set(row) != EXPECTED_ITEM_KEYS:
            raise ValueError("invalid candidate fields")
        if row.get("id") != f"source-{i:03d}":
            raise ValueError("duplicate or out-of-sequence source id")
        name = row.get("name")
        if not isinstance(name, str) or not 1 <= len(name) <= 90 or name.strip() != name:
            raise ValueError("invalid name")
        priority = row.get("priority")
        if priority not in PRIORITIES:
            raise ValueError("invalid priority")
        priorities[priority] += 1
        repo = row.get("upstream_repo")
        if not isinstance(repo, str) or SAFE_REPO.fullmatch(repo) is None:
            raise ValueError("untrusted upstream repository")
        url = row.get("source_url")
        if not isinstance(url, str) or len(url) > 500:
            raise ValueError("invalid upstream source URL")
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https" or parsed.netloc != "github.com"
            or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment
            or not (parsed.path == "/" + repo
                    or parsed.path.startswith("/" + repo + "/blob/HEAD/"))
            or ".." in parsed.path.split("/") or "\\" in url or "%" in parsed.path
        ):
            raise ValueError("source link must be an unpinned GitHub repository or example")
        if any(c in url for c in ("\n", "\r", "\t", " ")):
            raise ValueError("control character in source URL")
        if (
            row.get("pinned_commit") is not None
            or row.get("source_verification") != "unverified_at_pin"
            or row.get("license_review") != "pending"
            or row.get("security_review") != "pending"
            or row.get("installed_by_registry") is not False
            or row.get("approved") is not False
            or row.get("enabled") is not False
        ):
            raise ValueError("candidate is not admitted or installed by this registry")
    if dict(priorities) != EXPECTED_COUNTS:
        raise ValueError("unexpected candidate priority inventory")
    by_name = {row["name"]: row for row in rows}
    required = {
        "Hermes Agent": "NousResearch/hermes-agent",
        "Hermes Self-Evolution": "NousResearch/hermes-agent-self-evolution",
        "OmniRoute": "cheaper-inference/OmniRoute",
        "FreeLLMAPI — original upstream": "tashfeenahmed/freellmapi",
    }
    if len(by_name) != len(rows) or any(
        by_name.get(name, {}).get("upstream_repo") != repo
        for name, repo in required.items()
    ):
        raise ValueError("missing or incorrect required upstream candidate")
    if by_name["Hermes Self-Evolution"]["priority"] != "P2":
        raise ValueError("costly self-evolution must remain deferred")
    return rows


def load_catalog(path=REGISTRY):
    """Load a local repository-tracked JSON file; never retrieve remote code."""
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 200_000:
        raise ValueError("catalog unavailable or untrusted")
    return validate(json.loads(path.read_text(encoding="utf-8")))


def select(items, *, priority=None, text=None):
    """Select indexed sources without changing their admission state."""
    if priority is not None and priority not in PRIORITIES:
        raise ValueError("priority must be P0, P1 or P2")
    if text is not None and not isinstance(text, str):
        raise ValueError("text must be a string")
    term = text.casefold() if text else None
    return [
        row for row in items
        if (priority is None or row["priority"] == priority)
        and (term is None or term in row["name"].casefold()
             or term in row["upstream_repo"].casefold())
    ]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only CODEN 72-source registry")
    parser.add_argument("--priority", choices=sorted(PRIORITIES))
    parser.add_argument("--contains", help="Substring in name or upstream owner/repo")
    parser.add_argument("--json", action="store_true", help="Print full filtered records")
    args = parser.parse_args(argv)
    try:
        all_rows = load_catalog()
        chosen = select(all_rows, priority=args.priority, text=args.contains)
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Registry BLOCKED ({type(exc).__name__})\n")
    if args.json:
        print(json.dumps(chosen, indent=2, ensure_ascii=False))
    elif args.priority or args.contains:
        for item in chosen:
            print(f"{item['id']} [{item['priority']}] {item['name']} — {item['upstream_repo']}")
        print(f"Found: {len(chosen)} | enabled: 0 | approved: 0 | installed by this registry: 0")
    else:
        counts = Counter(r["priority"] for r in all_rows)
        print(
            "CODEN Adopt-First candidates: "
            f"{len(all_rows)} (P0={counts['P0']}, P1={counts['P1']}, P2={counts['P2']})"
        )
        print("Approved: 0 | enabled: 0 | installed by this registry: 0 | authorized spend: $0")
        print("This catalog is a proposal. Verify exact upstream revisions and licenses before adoption.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
