"""Read-only worker queue recovery backlog based on REAL SQLite metadata.

No generated candidate source is imported or executed here. Source was
independently reviewed after the real Qwen task #169, but that candidate
is QUARANTINED, not approved or silently promoted.

This report CANNOT request cancellation, retry, or recover leases; the DurableQueue writer is the
ONLY owner of state transitions. Cancellation requests do NOT terminate processes. Fail closed on invalid/unknown task statuses.
"""
import argparse
from contextlib import closing
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys
import time

MAX_DATABASE_BYTES = 64 * 1024 * 1024
MAX_ROWS = 10_000
STATUSES = frozenset({
    "queued", "leased", "cancel_requested", "cancelled", "needs_review", "awaiting_human_review", "blocked", "failed"
})
REQUIRED_COLUMNS = frozenset({
    "task_id", "status", "lease_token", "lease_until"
})
LEASE_TOKEN = re.compile(r"[0-9a-f]{32}\Z")


def _now(value):
    stamp = time.time() if value is None else value
    if type(stamp) not in (float, int) or not math.isfinite(stamp) or stamp < 0:
        raise ValueError("invalid snapshot clock")
    return float(stamp)


def _open_readonly(path):
    """Open real regular SQLite file by verified Linux descriptor, no symlink."""

    path = Path(path)
    if not path.is_absolute():
        raise ValueError("absolute operator-owned queue DB path required")
    if (not hasattr(os, "O_NOFOLLOW") or not Path("/proc/self/fd").is_dir()
            or path.is_symlink() or path.parent.is_symlink()):
        raise ValueError("untrusted queue database path")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError as exc:
        raise ValueError("queue DB missing or unreadable") from exc

    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_DATABASE_BYTES):
            raise ValueError("invalid SQLite regular file or size")
        # Using the already-open file descriptor prevents replacement of the
        # original path between preflight and SQLite's file-open operation.
        uri = f"file:/proc/self/fd/{fd}?mode=ro"
        db = sqlite3.connect(uri, uri=True, timeout=2, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA trusted_schema=OFF")
        db.execute("PRAGMA query_only=ON")
        return db, fd
    except Exception:
        os.close(fd)
        raise


def snapshot(path, *, now=None):
    """Read live queue states once, without changing leases or exposing IDs."""
    stamp = _now(now)
    db = None
    fd = None
    try:
        db, fd = _open_readonly(Path(path))
        with closing(db):
            db.execute("BEGIN")
            cols = {item["name"] for item in db.execute("PRAGMA table_info(tasks)")}
            if not REQUIRED_COLUMNS.issubset(cols):
                raise ValueError("unrecognized worker queue schema")
            rows = db.execute(
                "SELECT status, lease_until, lease_token FROM tasks LIMIT ?",
                (MAX_ROWS + 1,),
            ).fetchall()
            if len(rows) > MAX_ROWS:
                raise ValueError("queue exceeds bounded read-only inspection limit")

            counts = {s: 0 for s in STATUSES}
            active = 0
            expired = 0
            cancel_active = 0
            cancel_expired = 0
            for row in rows:
                state, until, token = row["status"], row["lease_until"], row["lease_token"]
                if not isinstance(state, str) or state not in STATUSES:
                    raise ValueError("unrecognized queue state; fail closed")
                if state in ("leased", "cancel_requested"):
                    if (type(until) not in (int, float) or
                            not math.isfinite(until) or until < 0 or
                            not isinstance(token, str) or
                            LEASE_TOKEN.fullmatch(token) is None):
                        raise ValueError("invalid leased task metadata")
                    if until < stamp:
                        if state == "leased":
                            expired += 1
                        else:
                            cancel_expired += 1
                    else:
                        if state == "leased":
                            active += 1
                        else:
                            cancel_active += 1
                elif token is not None or until is not None:
                    raise ValueError("unexpected lease secrets outside active lease")
                counts[state] += 1
            db.execute("COMMIT")
        return {
            "source": "real_durable_queue_sqlite_metadata",
            "scope": "CODEN_FACTORY_SYNTHETIC_OPERATOR_QUEUE_ONLY",
            "plan_version": "v1.0",
            "plan_sections": [19, 51, 66, 72],
            "total_tasks": len(rows),
            "queued": counts["queued"],
            "leased_active": active,
            "leased_expired_pending_review": expired,
            "needs_review_quarantined": counts["needs_review"],
            "cancelled_before_start": counts["cancelled"],
            "cancel_requested_active": cancel_active,
            "cancel_requested_expired": cancel_expired,
            "manual_attention_total": (
                expired + counts["needs_review"] + cancel_active + cancel_expired
            ),
            "awaiting_human_review": counts["awaiting_human_review"],
            "blocked": counts["blocked"],
            "failed": counts["failed"],
            "cancellation_support": "REQUEST_ONLY_NO_PROCESS_TERMINATION",
            "cancellation_process_termination_verified": False,
            "qwen_candidate_status": "QUARANTINED_NOT_EXECUTED",
            "model_code_executed": False,
            "queue_modified": False,
            "worker_executed": False,
            "automatic_retry_authorized": False,
            "release_authorized": False,
            "paid_calls": 0,
        }
    except (sqlite3.Error, OSError, TypeError, UnicodeError) as exc:
        raise ValueError("worker queue read-only inspection blocked") from exc
    finally:
        if fd is not None:
            os.close(fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--now", type=float,
                        help="Optional deterministic synthetic test clock")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        data = snapshot(args.db, now=args.now)
    except (OSError, ValueError, TypeError):
        parser.exit(2, "CODEN worker queue snapshot BLOCKED\n")
    if args.json:
        print(json.dumps(data, sort_keys=True))
    else:
        print(
            f"CODEN queue: {data['total_tasks']} tasks; "
            f"{data['leased_expired_pending_review']} expired leases; "
            f"{data['needs_review_quarantined']} quarantined; "
            "ZERO mutations, ZERO automatic retries."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
