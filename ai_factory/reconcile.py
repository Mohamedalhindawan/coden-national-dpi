"""Read-only diagnostic of SQLite queue vs checkpoint journals after an outage.

This module never updates either store, claims a task, approves work or retries
work. A snapshot cannot replace an atomic cross-store transaction. Treat every
anomaly as requiring operator review and retain independent evidence.
"""

import argparse
from collections import Counter
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import sys
from urllib.parse import quote

from . import checkpoint

MAX_TASKS = 1000
MAX_TASK_FILE = 32768


def _payload_matches(task_dir, task_id, expected):
    path = Path(task_dir) / f"{task_id}.json"
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_TASK_FILE:
            return False
        with os.fdopen(os.dup(fd), "rb") as stream:
            data = stream.read(MAX_TASK_FILE + 1)
    finally:
        os.close(fd)
    return len(data) <= MAX_TASK_FILE and hashlib.sha256(data).hexdigest() == expected


def _queue_rows(db_path):
    path = Path(db_path)
    if not path.is_file() or path.is_symlink() or path.parent.is_symlink():
        raise ValueError("existing regular non-symlink queue database required")
    # Connect read-only. No schema creation, chmod, leases, WAL checkpoint or mutations.
    uri = "file:" + quote(str(path.absolute()), safe="/") + "?mode=ro"
    try:
        with closing(sqlite3.connect(uri, uri=True, timeout=3)) as db:
            db.execute("PRAGMA query_only=ON")
            rows = db.execute(
                "SELECT task_id,branch,commit_sha,task_sha256,status "
                "FROM tasks ORDER BY task_id LIMIT ?", (MAX_TASKS + 1,)
            ).fetchall()
    except sqlite3.Error as exc:
        raise ValueError("unreadable queue database or schema") from exc
    if len(rows) > MAX_TASKS:
        raise ValueError("queue exceeds audit limit")
    return rows


def _evaluate(queue_state, journal_state):
    if queue_state == "cancelled" and journal_state == "prepared":
        # Operator cancelled before any successful claim or execution.
        return "consistent_cancelled_before_start"
    if queue_state == "cancel_requested":
        # The process may still be alive, even after its leader was reaped.
        # Retain a human review requirement; never certify fully cancelled.
        return "cancel_stop_reconciliation_required"
    if queue_state == "needs_review":
        return "manual_review_required"
    if queue_state == "queued" and journal_state == "prepared":
        return "consistent_queued"
    if queue_state == "leased" and journal_state == "prepared":
        return "claim_without_start_evidence"
    if queue_state == "leased" and journal_state == "checkpointed":
        return "active_unverified"
    if queue_state == "leased" and journal_state in ("awaiting_human_review", "blocked"):
        return "journal_ahead_of_queue"
    if queue_state == "awaiting_human_review" and journal_state == "awaiting_human_review":
        return "consistent_review"
    if queue_state in ("blocked", "failed") and journal_state == "blocked":
        return "consistent_blocked"
    return "state_mismatch"


def scan(queue_db, journal_dir, task_dir=None):
    """Return bounded, credential-free findings; never mutate queue or journal."""
    root = Path(journal_dir)
    if root.is_symlink() or root.parent.is_symlink():
        raise ValueError("symlink journal root forbidden")
    if task_dir is not None:
        task_root = Path(task_dir)
        if task_root.is_symlink() or task_root.parent.is_symlink() or not task_root.is_dir():
            raise ValueError("trusted task directory required")
    queue_rows = _queue_rows(queue_db)
    entries = []
    known = set()
    for task_id, branch, commit, task_hash, queue_status in queue_rows:
        checkpoint._id(task_id)
        known.add(task_id)
        condition = None
        journal_status = None
        try:
            journal = checkpoint.read(root, task_id)
            journal_status = journal["status"]
            if journal["last_branch"] != branch or journal["last_commit"] != commit:
                condition = "identity_mismatch"
            else:
                condition = _evaluate(queue_status, journal_status)
        except FileNotFoundError:
            condition = "missing_journal"
        except (OSError, TypeError, ValueError):
            condition = "invalid_journal"
        if task_dir is not None:
            try:
                if not _payload_matches(task_dir, task_id, task_hash):
                    condition = "task_hash_mismatch"
            except (OSError, ValueError):
                condition = "task_hash_mismatch"
        entries.append({
            "task_id": task_id,
            "queue_status": queue_status,
            "journal_status": journal_status,
            "condition": condition,
            "needs_attention": condition not in
                ("consistent_queued", "consistent_review", "consistent_blocked",
                 "consistent_cancelled_before_start"),
            "execution_authorized": False,
            "safe_to_auto_retry": False,
        })
    if root.exists():
        if not root.is_dir():
            raise ValueError("journal root must be directory")
        files = sorted(p for p in root.iterdir() if p.name.endswith(".jsonl"))
        if len(files) + len(entries) > MAX_TASKS * 2:
            raise ValueError("journal audit exceeds limit")
        for path in files:
            task_id = path.name[:-6]
            if task_id in known:
                continue
            condition = "orphan_journal"
            journal_status = None
            try:
                checkpoint._id(task_id)
                state = checkpoint.read(root, task_id)
                journal_status = state["status"]
            except (OSError, ValueError, TypeError):
                condition = "invalid_journal"
            entries.append({
                "task_id": task_id,
                "queue_status": None,
                "journal_status": journal_status,
                "condition": condition,
                "needs_attention": True,
                "execution_authorized": False,
                "safe_to_auto_retry": False,
            })
    entries.sort(key=lambda item: item["task_id"])
    counts = dict(sorted(Counter(item["condition"] for item in entries).items()))
    return {
        "tasks": entries,
        "total": len(entries),
        "needs_attention": any(item["needs_attention"] for item in entries),
        "conditions": counts,
        "execution_authorized": False,
        "safe_to_auto_retry": False,
        "read_only": True,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue-db", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--task-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        result = scan(args.queue_db, args.journal, task_dir=args.task_dir)
    except (OSError, ValueError, sqlite3.Error) as exc:
        print(f"Reconciliation blocked ({type(exc).__name__})", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    return 1 if result["needs_attention"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
