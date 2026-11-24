"""Local aggregate alert evaluation over the existing queue health snapshot.

No daemon, delivery integration, task mutation, retry or execution permission.
An empty alert list does not prove worker availability. The operator must
review findings; the underlying snapshot is not an atomic admission gate.
"""
from . import queue_health, reconcile

DEFAULT_BACKLOG_THRESHOLD = 20
CONSISTENT = frozenset({"consistent_queued", "consistent_review", "consistent_blocked"})


def evaluate(queue_db, journal_dir, task_dir, *, now=None,
             backlog_threshold=DEFAULT_BACKLOG_THRESHOLD):
    """Return deterministic aggregate alert records without identifiers."""
    if (type(backlog_threshold) is not int or
            not 1 <= backlog_threshold <= reconcile.MAX_TASKS):
        raise ValueError("invalid backlog threshold")
    health = queue_health.snapshot(queue_db, journal_dir, task_dir, now=now)
    alerts = []

    def add(code, severity, count):
        if count > 0:
            alerts.append({"code": code, "severity": severity, "count": count})

    add("expired_leases", "warning", health["expired_leases"])
    add("reconciliation_required", "warning",
        sum(count for condition, count in health["conditions"].items()
            if condition not in CONSISTENT))
    add("blocked_tasks", "warning", health["blocked"])
    add("failed_tasks", "warning", health["failed"])
    if health["queue_depth"] >= backlog_threshold:
        add("queue_backlog", "warning", health["queue_depth"])
    return {
        "alerts": alerts,
        "needs_attention": bool(alerts or health["needs_attention"]),
        "worker_availability": "unverified",
        "delivery_performed": False,
        "read_only": True,
        "execution_authorized": False,
        "automatic_retry_allowed": False,
    }
