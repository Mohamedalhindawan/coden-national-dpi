"""Opt-in **offline synthetic-only** queue-to-checkpoint project worker.

This is an operator-invoked, single-task execution adapter, NOT a daemon,
provider router, general coding agent, production approval or autonomous retry.
The existing project.run controls all untrusted candidate code sandboxing.
Never use this on real citizen/government/customer data.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

from . import checkpoint, durable_queue, project

MAX_TASK_BYTES = 32768


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _task_file(tasks_dir, task_id):
    checkpoint._id(task_id)
    folder = Path(tasks_dir)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("operator task directory required")
    return folder / (task_id + ".json")


def _load_task(tasks_dir, task_id):
    path = _task_file(tasks_dir, task_id)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_TASK_BYTES:
            raise ValueError("task must be a bounded regular file")
        with os.fdopen(os.dup(fd), "rb") as stream:
            data = stream.read(MAX_TASK_BYTES + 1)
        if len(data) > MAX_TASK_BYTES:
            raise ValueError("task exceeds size limit")
    finally:
        os.close(fd)
    digest = hashlib.sha256(data).hexdigest()
    task = json.loads(data.decode("utf-8"), object_pairs_hook=_unique_keys)
    if not project.valid(task) or task["id"] != task_id or task["recipe"] != "status-counts":
        raise ValueError("only approved synthetic status-counts pilot tasks supported")
    return task, digest


def submit(queue, checkpoint_root, tasks_dir, task_id, *, branch, commit):
    """Register a pre-existing trusted synthetic JSON task (never runs it)."""
    task, digest = _load_task(tasks_dir, task_id)
    checkpoint._branch(branch)
    checkpoint._commit(commit)
    if not branch or not commit:
        raise ValueError("branch and full commit required")
    # Checkpoint comes first. If queue insertion fails, leave an orphan record
    # for operator inspection; never silently recover or re-enqueue.
    checkpoint.create(checkpoint_root, task_id, branch=branch, commit=commit)
    return queue.enqueue(task_id, branch, commit, digest)


def _public(lease, status, *, directory=None):
    result = {
        "task_id": lease["task_id"],
        "status": status,
        "execution_authorized": False,
    }
    if directory is not None:
        result["directory"] = Path(directory)
    return result


def work_once(queue, checkpoint_root, tasks_dir, output_root, *, worker_id, lease_seconds=300):
    """Claim one task and run existing bounded pilot; no unattended retries."""
    if not Path(output_root).is_dir() or Path(output_root).is_symlink():
        raise ValueError("existing operator output directory required")
    lease = queue.claim(worker_id, lease_seconds=lease_seconds)
    if lease is None:
        return None
    task_id = lease["task_id"]
    token = lease["lease_token"]
    execution_started = False
    try:
        task, digest = _load_task(tasks_dir, task_id)
        original = checkpoint.read(checkpoint_root, task_id)
        if (digest != lease["task_sha256"] or
            original["last_branch"] != lease["branch"] or
            original["last_commit"] != lease["commit"] or
            original["status"] != "prepared"):
            raise ValueError("task or checkpoint integrity mismatch")
        # Verifies this claim remains current before any work starts.
        queue.heartbeat(task_id, token, extend_seconds=lease_seconds)
        checkpoint.record(checkpoint_root, task_id, event="checkpoint",
                          next_action="offline_project_run", event_key="worker_start")
        execution_started = True
        directory, outcome = project.run(task, output_root)
        if outcome == "awaiting_human_review":
            checkpoint.record(checkpoint_root, task_id, event="review_requested",
                              next_action="human_review", event_key="worker_review")
            queue.finish(task_id, token, "awaiting_human_review")
            return _public(lease, "awaiting_human_review", directory=directory)
        if outcome not in ("blocked", "failed"):
            raise ValueError("unrecognized project outcome")
        checkpoint.record(checkpoint_root, task_id, event="blocked",
                          next_action="inspect_offline_logs", event_key="worker_block")
        queue.finish(task_id, token, "blocked")
        return _public(lease, "blocked", directory=directory)
    except Exception:
        # Once the project runner has been invoked, it may have created files
        # even if an exception is raised or a subsequent journal/DB write fails.
        # Leave the lease intact for expiry quarantine + operator reconciliation:
        # do not overwrite review evidence with a false terminal "blocked".
        if execution_started:
            return _public(lease, "needs_review")
        # An explicit SIGKILL or KeyboardInterrupt escapes: after lease expiry,
        # recover_expired quarantines instead of automatically re-running.
        # Do not log raw exception details (they may contain task/secret data).
        journal_ok = True
        try:
            checkpoint.record(checkpoint_root, task_id, event="blocked",
                              next_action="inspect_offline_logs", event_key="worker_block")
        except (OSError, ValueError, TypeError):
            journal_ok = False
        try:
            queue.finish(task_id, token, "blocked")
        except (OSError, ValueError):
            return _public(lease, "needs_review")
        return _public(lease, "blocked" if journal_ok else "needs_review")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue-db", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--task-dir", type=Path, required=True)
    modes = parser.add_subparsers(dest="command", required=True)
    submit_cmd = modes.add_parser("submit", help="Operator registers synthetic task without running it")
    submit_cmd.add_argument("task_id")
    submit_cmd.add_argument("--branch", required=True)
    submit_cmd.add_argument("--commit", required=True)
    once = modes.add_parser("work-once", help="Operator explicitly processes at most one queued task")
    once.add_argument("--output-root", type=Path, required=True)
    once.add_argument("--worker-id", default="offline_operator")
    once.add_argument("--lease-seconds", type=int, default=300)
    modes.add_parser("inspect-expired", help="Quarantine expired leases, never replay")
    args = parser.parse_args(argv)
    try:
        q = durable_queue.DurableQueue(args.queue_db)
        if args.command == "submit":
            output = submit(q, args.journal, args.task_dir, args.task_id, branch=args.branch, commit=args.commit)
        elif args.command == "work-once":
            output = work_once(q, args.journal, args.task_dir, args.output_root,
                               worker_id=args.worker_id, lease_seconds=args.lease_seconds)
        else:
            output = {"quarantined": q.recover_expired(), "execution_authorized": False}
    except (OSError, ValueError, TypeError) as exc:
        print(f"Operator worker blocked ({type(exc).__name__})", file=sys.stderr)
        return 2
    if output is not None and "directory" in output:
        output["directory"] = str(output["directory"])
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
