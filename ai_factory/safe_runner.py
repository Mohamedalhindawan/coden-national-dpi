"""Minimal local read-only demo executor. No shell, network, or writes."""
from pathlib import Path


def run_read_only(order, repository_root):
    if not isinstance(order, dict):
        return {"status": "blocked", "reason": "invalid_order"}
    if order.get("ready_for_review") is not True:
        return {"status": "blocked", "reason": "unreviewed_order"}
    if order.get("allowed_actions") != ["read_repository"]:
        return {"status": "blocked", "reason": "unsupported_action"}
    root = Path(repository_root)
    if not (root / "README.md").is_file():
        return {"status": "blocked", "reason": "missing_readme"}
    try:
        with (root / "README.md").open("r", encoding="utf-8") as handle:
            handle.read(1)
    except (OSError, UnicodeError):
        return {"status": "blocked", "reason": "read_failed"}
    return {"status": "completed_read_only", "files_checked": ["README.md"]}
