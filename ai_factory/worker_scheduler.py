"""Operator-invoked bounded batch for the existing synthetic-only worker.

Not a daemon, cron service, model executor, approval authority or sandbox.
The trusted operator must control all stores. A local advisory lock serializes
cooperating batches on the canonical database path. Direct worker calls and
other hosts do not share this guard; reconciliation is not a transaction.
No automatic replay, retry, lease repair, paid provider or production action.
"""
import fcntl
import os
import stat
from time import monotonic as _monotonic

from . import checkpoint, reconcile, worker_supervisor

MAX_BATCH_TASKS = 10


def run_batch(*, queue_db, journal, task_dir, output_root, worker_id,
              max_tasks=1, timeout_seconds=60, lease_seconds=120,
              max_batch_seconds=None):
    """Run at most max_tasks one-shot workers, stopping on uncertain evidence.

    Optional batch budget is a launch deadline, not an OS-enforced wall-clock
    cap. Reconciliation, cleanup and an already-running worker may overrun it.
    Never start another worker without its full timeout plus grace remaining.
    """
    checkpoint._id(worker_id)
    if type(max_tasks) is not int or not 1 <= max_tasks <= MAX_BATCH_TASKS:
        raise ValueError("batch limit must be 1 to 10")
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 900:
        raise ValueError("invalid worker timeout")
    if type(lease_seconds) is not int or not (
        timeout_seconds + worker_supervisor.MIN_GRACE_SECONDS <= lease_seconds <= 3600
    ):
        raise ValueError("invalid lease duration")
    if max_batch_seconds is not None and (
        type(max_batch_seconds) is not int or not 1 <= max_batch_seconds <= 3600
    ):
        raise ValueError("invalid batch time budget")
    deadline = None if max_batch_seconds is None else _monotonic() + max_batch_seconds
    db = worker_supervisor._db(queue_db)
    journals = worker_supervisor._dir(journal, label="journal")
    tasks = worker_supervisor._dir(task_dir, label="task")
    outputs = worker_supervisor._dir(output_root, label="output")
    count = 0

    def receipt(status):
        return {"status": status, "review_candidates": count,
                "execution_authorized": False, "automatic_retry_allowed": False}

    # Keep the inode stable: never unlink a lock file, even after release.
    # O_NONBLOCK also avoids hanging if a special file occupies the path.
    fd = os.open(db + ".batch.lock",
                 os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                 0o600)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or
                info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600):
            raise ValueError("trusted private batch lock required")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return receipt("batch_busy")
        for _ in range(max_tasks):
            try:
                before = reconcile.scan(db, journals, tasks)
            except (OSError, ValueError):
                # Missing durable evidence cannot permit another dispatch or retry.
                return receipt("reconciliation_required")
            if before["needs_attention"]:
                return receipt("reconciliation_required")
            queued = {x["task_id"] for x in before["tasks"]
                      if x["condition"] == "consistent_queued"}
            if not queued:
                return receipt("idle" if count == 0 else "queue_drained")
            order = before["queued_order"]
            if len(order) != len(queued) or set(order) != queued:
                return receipt("reconciliation_required")
            selected = order[0]
            if deadline is not None and (
                deadline - _monotonic() < timeout_seconds + worker_supervisor.MIN_GRACE_SECONDS
            ):
                return receipt("batch_time_budget_exhausted")
            try:
                result = worker_supervisor.run_once(
                    queue_db=db, journal=journals, task_dir=tasks, output_root=outputs,
                    worker_id=worker_id, timeout_seconds=timeout_seconds,
                    lease_seconds=lease_seconds, task_id=selected)
            except (OSError, ValueError):
                return receipt("worker_review_required")
            if (not isinstance(result, dict) or
                    set(result) != {"status", "execution_authorized", "automatic_retry_allowed"} or
                    result["execution_authorized"] is not False or
                    result["automatic_retry_allowed"] is not False or
                    result["status"] != "awaiting_human_review"):
                return receipt("worker_review_required")
            try:
                after = reconcile.scan(db, journals, tasks)
            except (OSError, ValueError):
                # Missing durable evidence cannot permit another dispatch or retry.
                return receipt("reconciliation_required")
            if after["needs_attention"]:
                return receipt("reconciliation_required")
            old = {x["task_id"]: x["condition"] for x in before["tasks"]}
            new = {x["task_id"]: x["condition"] for x in after["tasks"]}
            changed = {k for k in old if old[k] != new.get(k)}
            if (old.keys() != new.keys() or changed != {selected} or
                    any(new[k] != "consistent_review" for k in changed)):
                return receipt("worker_review_required")
            count += 1
        return receipt("batch_limit_reached")
    finally:
        os.close(fd)
