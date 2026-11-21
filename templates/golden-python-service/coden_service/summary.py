"""Deterministic synthetic task counter; no model or database connections."""

import re

STATUSES = ("queued", "in_progress", "blocked", "done")
TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")


def summarize(items):
    """Summarize at most 100 synthetic items with strict fail-closed inputs."""
    if not isinstance(items, list) or len(items) > 100:
        raise ValueError("items must be a list of at most 100")
    counts = {status: 0 for status in STATUSES}
    for item in items:
        if not isinstance(item, dict) or set(item) != {"task_id", "status", "classification"}:
            raise ValueError("unexpected task fields")
        task_id = item["task_id"]
        status = item["status"]
        if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
            raise ValueError("invalid task id")
        if not isinstance(status, str) or status not in STATUSES:
            raise ValueError("invalid status")
        if item["classification"] != "synthetic":
            raise ValueError("only synthetic records permitted")
        counts[status] += 1
    return {"total": len(items), **counts}
