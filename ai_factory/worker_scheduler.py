"""Operator-invoked bounded batch for the existing synthetic-only worker.

Not a daemon, cron service, model executor, approval authority or sandbox.
The trusted operator must control all stores and serialize batches. Read-only
reconciliation snapshots are not a distributed lock or cross-store transaction.
No automatic replay, retry, lease repair, paid provider or production action.
"""
from . import checkpoint, reconcile, worker_supervisor

MAX_BATCH_TASKS = 10


def run_batch(*, queue_db, journal, task_dir, output_root, worker_id,
              max_tasks=1, timeout_seconds=60, lease_seconds=120):
    """Run at most max_tasks one-shot workers, stopping on uncertain evidence."""
    checkpoint._id(worker_id)
    if type(max_tasks) is not int or not 1 <= max_tasks <= MAX_BATCH_TASKS:
        raise ValueError("batch limit must be 1 to 10")
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 900:
        raise ValueError("invalid worker timeout")
    if type(lease_seconds) is not int or not (
        timeout_seconds + worker_supervisor.MIN_GRACE_SECONDS <= lease_seconds <= 3600
    ):
        raise ValueError("invalid lease duration")
    db = worker_supervisor._db(queue_db)
    journals = worker_supervisor._dir(journal, label="journal")
    tasks = worker_supervisor._dir(task_dir, label="task")
    outputs = worker_supervisor._dir(output_root, label="output")
    count = 0

    def receipt(status):
        return {"status": status, "review_candidates": count,
                "execution_authorized": False, "automatic_retry_allowed": False}

    for _ in range(max_tasks):
        before = reconcile.scan(db, journals, tasks)
        if before["needs_attention"]:
            return receipt("reconciliation_required")
        queued = {x["task_id"] for x in before["tasks"]
                  if x["condition"] == "consistent_queued"}
        if not queued:
            return receipt("idle" if count == 0 else "queue_drained")
        try:
            result = worker_supervisor.run_once(
                queue_db=db, journal=journals, task_dir=tasks, output_root=outputs,
                worker_id=worker_id, timeout_seconds=timeout_seconds,
                lease_seconds=lease_seconds)
        except (OSError, ValueError):
            return receipt("worker_review_required")
        if (not isinstance(result, dict) or
                set(result) != {"status", "execution_authorized", "automatic_retry_allowed"} or
                result["execution_authorized"] is not False or
                result["automatic_retry_allowed"] is not False or
                result["status"] != "awaiting_human_review"):
            return receipt("worker_review_required")
        after = reconcile.scan(db, journals, tasks)
        if after["needs_attention"]:
            return receipt("reconciliation_required")
        old = {x["task_id"]: x["condition"] for x in before["tasks"]}
        new = {x["task_id"]: x["condition"] for x in after["tasks"]}
        changed = {k for k in old if old[k] != new.get(k)}
        if (old.keys() != new.keys() or len(changed) != 1 or
                not changed <= queued or
                any(new[k] != "consistent_review" for k in changed)):
            return receipt("worker_review_required")
        count += 1
    return receipt("batch_limit_reached")
