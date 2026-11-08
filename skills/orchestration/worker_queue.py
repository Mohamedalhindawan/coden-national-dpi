"""Local integration between the durable queue and bounded worker admission."""
from skills.orchestration.queue import QueueError
from skills.orchestration.worker_runtime import WorkerRuntimeError


class IntegrationError(ValueError):
    pass


class WorkerQueueIntegration:
    def __init__(self, queue, workers):
        self.queue = queue
        self.workers = workers
        self._claims = {}

    def dispatch(self, worker_id, lease_seconds=60, now=None):
        status = self.workers.worker_status(worker_id)
        capabilities = status["capabilities"]
        if (status["active_count"] >= status["max_concurrency"]
                or self.workers.active_count >= self.workers.max_workers):
            return None
        try:
            claim = self.queue.claim(worker_id, lease_seconds=lease_seconds, now=now,
                                     task_kinds=capabilities)
        except QueueError as exc:
            raise IntegrationError(str(exc)) from exc
        if claim is None:
            return None

        # A reclaimed lease invalidates the previous local slot for this task.
        previous = self._claims.get(claim["task_id"])
        if previous:
            try:
                self.workers.release_slot(previous["worker_id"], claim["task_id"])
            except WorkerRuntimeError:
                pass
        try:
            self.workers.acquire_slot(worker_id, claim["task_id"], claim["payload"]["kind"])
        except WorkerRuntimeError as exc:
            # The queue lease remains valid; do not silently discard it.
            raise IntegrationError("Queue task claimed but worker admission failed; lease will expire: " + str(exc)) from exc
        self._claims[claim["task_id"]] = {
            "worker_id": worker_id,
            "lease_token": claim["lease_token"],
        }
        return claim

    def _verify_claim(self, claim):
        if not isinstance(claim, dict) or not claim.get("task_id"):
            raise IntegrationError("A queue claim is required")
        current = self._claims.get(claim["task_id"])
        if not current or current["worker_id"] != claim.get("worker_id") or current["lease_token"] != claim.get("lease_token"):
            raise IntegrationError("Claim is stale or not owned by this integration")
        return current

    def heartbeat(self, claim, lease_seconds=60, now=None):
        current = self._verify_claim(claim)
        try:
            return self.queue.heartbeat(claim["task_id"], current["worker_id"],
                                        current["lease_token"], lease_seconds=lease_seconds, now=now)
        except QueueError as exc:
            raise IntegrationError(str(exc)) from exc

    def complete(self, claim, result, now=None):
        current = self._verify_claim(claim)
        try:
            completed = self.queue.complete(claim["task_id"], current["worker_id"], result,
                                            lease_token=current["lease_token"], now=now)
        except QueueError as exc:
            raise IntegrationError(str(exc)) from exc
        self.workers.release_slot(current["worker_id"], claim["task_id"])
        del self._claims[claim["task_id"]]
        return completed

    def fail(self, claim, error, now=None):
        current = self._verify_claim(claim)
        try:
            failed = self.queue.fail(claim["task_id"], current["worker_id"], error,
                                     lease_token=current["lease_token"], now=now)
        except QueueError as exc:
            raise IntegrationError(str(exc)) from exc
        self.workers.release_slot(current["worker_id"], claim["task_id"])
        del self._claims[claim["task_id"]]
        return failed
