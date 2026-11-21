"""Unified local workflow control facade; no task payload execution."""
from collections import Counter

from skills.orchestration.queue import QueueError
from skills.orchestration.worker_runtime import WorkerRuntimeError


class ControlPlaneError(ValueError):
    pass


class WorkflowControlPlane:
    def __init__(self, scheduler, workers):
        self.scheduler = scheduler
        self.workers = workers

    def pause(self):
        return self.workers.pause()

    def resume(self):
        return self.workers.resume()

    def dispatch(self, worker_id, lease_seconds=60, now=None):
        if self.workers.paused:
            raise ControlPlaneError("Workflow dispatch is paused")
        try:
            return self.scheduler.dispatch(worker_id, lease_seconds=lease_seconds, now=now)
        except (ValueError, WorkerRuntimeError) as exc:
            raise ControlPlaneError(str(exc)) from exc

    def reconcile(self):
        try:
            blocked = sorted(self.scheduler.refresh_blocked())
            states = self.scheduler.states()
        except ValueError as exc:
            raise ControlPlaneError(str(exc)) from exc
        return {
            "blocked": blocked,
            "state_counts": dict(sorted(Counter(states.values()).items())),
        }

    def snapshot(self):
        try:
            states = self.scheduler.states()
            workers = [
                self.workers.worker_status(worker_id)
                for worker_id in sorted(self.workers.allowed_worker_ids)
            ]
        except (ValueError, WorkerRuntimeError) as exc:
            raise ControlPlaneError(str(exc)) from exc
        counts = Counter(states.values())
        return {
            "paused": self.workers.paused,
            "tasks": {state: counts.get(state, 0) for state in
                      ("pending", "running", "succeeded", "failed", "cancelled", "blocked")},
            "workers": {
                "registered_count": len(workers),
                "active_count": sum(worker["active_count"] for worker in workers),
                "workers": workers,
            },
        }

    def task_audit(self, task_id):
        if task_id not in self.scheduler.tasks:
            raise ControlPlaneError("Unknown workflow task: " + str(task_id))
        try:
            return self.scheduler.queue.audit_log(task_id)
        except QueueError as exc:
            raise ControlPlaneError(str(exc)) from exc
