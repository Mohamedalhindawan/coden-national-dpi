"""Aggregate, read-only health snapshot of the existing synthetic queue.

No worker availability assertion, execution authority, recovery, alerts or
database writes. The operator owns the stores. SQLite and journal readings
are separate snapshots; this is diagnostic telemetry, not an admission gate.
"""
from collections import Counter
from contextlib import closing
import math
from pathlib import Path
import sqlite3
from urllib.parse import quote

from . import durable_queue, reconcile

STATES = frozenset({"queued", "leased", "awaiting_human_review",
                    "needs_review", "blocked", "failed"})


def snapshot(queue_db, journal_dir, task_dir, *, now=None):
    stamp = durable_queue.DurableQueue._now(now)
    path = Path(queue_db)
    if not path.is_file() or path.is_symlink() or path.parent.is_symlink():
        raise ValueError("existing trusted queue required")
    uri = "file:" + quote(str(path.absolute()), safe="/") + "?mode=ro"
    try:
        with closing(sqlite3.connect(uri, uri=True, timeout=3)) as db:
            db.execute("PRAGMA query_only=ON")
            db.execute("PRAGMA trusted_schema=OFF")
            rows = db.execute(
                "SELECT status, lease_until FROM tasks LIMIT ?",
                (reconcile.MAX_TASKS + 1,)).fetchall()
    except sqlite3.Error as exc:
        raise ValueError("unreadable queue health snapshot") from exc
    if len(rows) > reconcile.MAX_TASKS:
        raise ValueError("queue exceeds audit limit")
    counts = Counter()
    expired = 0
    for status, deadline in rows:
        if status not in STATES:
            raise ValueError("unknown queue status")
        counts[status] += 1
        if status == "leased":
            if type(deadline) not in (int, float) or not math.isfinite(deadline) or deadline < 0:
                raise ValueError("invalid lease deadline")
            expired += int(deadline < stamp)
        elif deadline is not None:
            raise ValueError("unexpected deadline outside leased state")
    report = reconcile.scan(path, journal_dir, task_dir)
    return {
        "queue_depth": counts["queued"],
        "leased": counts["leased"],
        "expired_leases": expired,
        "awaiting_human_review": counts["awaiting_human_review"],
        "needs_review": counts["needs_review"],
        "blocked": counts["blocked"],
        "failed": counts["failed"],
        "conditions": report["conditions"],
        "needs_attention": bool(expired or report["needs_attention"] or
                                counts["needs_review"] or counts["blocked"] or counts["failed"]),
        "worker_availability": "unverified",
        "read_only": True,
        "execution_authorized": False,
        "automatic_retry_allowed": False,
    }
