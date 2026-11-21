"""Bounded worker admission control; intentionally does not execute task payloads."""
from threading import RLock


class WorkerRuntimeError(ValueError):
    pass


class WorkerAdmissionController:
    def __init__(self, max_workers, allowed_worker_ids, allowed_task_kinds):
        if isinstance(max_workers, bool) or not isinstance(max_workers, int) or not 1 <= max_workers <= 32:
            raise WorkerRuntimeError("max_workers must be between 1 and 32")
        if not isinstance(allowed_worker_ids, (list, tuple, set)) or not allowed_worker_ids:
            raise WorkerRuntimeError("At least one allowed worker ID is required")
        if not isinstance(allowed_task_kinds, (list, tuple, set)) or not allowed_task_kinds:
            raise WorkerRuntimeError("At least one allowed task kind is required")
        if any(not isinstance(item, str) or not item.strip() for item in allowed_worker_ids):
            raise WorkerRuntimeError("Worker IDs must be non-empty strings")
        if any(not isinstance(item, str) or not item.strip() for item in allowed_task_kinds):
            raise WorkerRuntimeError("Task kinds must be non-empty strings")
        self.max_workers = max_workers
        self.allowed_worker_ids = frozenset(allowed_worker_ids)
        self.allowed_task_kinds = frozenset(allowed_task_kinds)
        self._workers = {}
        self._active = {}
        self._paused = False
        self._lock = RLock()

    @property
    def active_count(self):
        with self._lock:
            return len(self._active)

    @property
    def paused(self):
        with self._lock:
            return self._paused

    def register_worker(self, worker_id, capabilities, max_concurrency=1):
        if worker_id not in self.allowed_worker_ids:
            raise WorkerRuntimeError("Worker is not allowlisted")
        if not isinstance(capabilities, (list, tuple, set)) or not capabilities:
            raise WorkerRuntimeError("Worker capabilities are required")
        if any(item not in self.allowed_task_kinds for item in capabilities):
            raise WorkerRuntimeError("Worker capability is not allowlisted")
        if isinstance(max_concurrency, bool) or not isinstance(max_concurrency, int) or not 1 <= max_concurrency <= 8:
            raise WorkerRuntimeError("max_concurrency must be between 1 and 8")
        with self._lock:
            if worker_id in self._workers:
                raise WorkerRuntimeError("Worker is already registered")
            self._workers[worker_id] = {
                "capabilities": frozenset(capabilities),
                "max_concurrency": max_concurrency,
                "active": set(),
                "status": "ready",
            }
            return self.worker_status(worker_id)

    def can_accept(self, worker_id, task_kind):
        with self._lock:
            worker = self._workers.get(worker_id)
            return bool(
                not self._paused and worker and worker["status"] == "ready"
                and task_kind in worker["capabilities"]
                and len(worker["active"]) < worker["max_concurrency"]
                and len(self._active) < self.max_workers
            )

    def acquire_slot(self, worker_id, job_id, task_kind):
        if not isinstance(job_id, str) or not job_id.strip():
            raise WorkerRuntimeError("job_id is required")
        with self._lock:
            if job_id in self._active:
                raise WorkerRuntimeError("job_id is already active")
            if not self.can_accept(worker_id, task_kind):
                raise WorkerRuntimeError("Worker admission denied by capability, pause, or concurrency policy")
            self._active[job_id] = {"worker_id": worker_id, "task_kind": task_kind}
            self._workers[worker_id]["active"].add(job_id)
            return {"job_id": job_id, "worker_id": worker_id, "task_kind": task_kind, "status": "admitted"}

    def release_slot(self, worker_id, job_id):
        with self._lock:
            active = self._active.get(job_id)
            if active is None:
                raise WorkerRuntimeError("Unknown active job")
            if active["worker_id"] != worker_id:
                raise WorkerRuntimeError("Only the owning worker can release this slot")
            del self._active[job_id]
            self._workers[worker_id]["active"].remove(job_id)
            return {"job_id": job_id, "worker_id": worker_id, "status": "released"}

    def pause(self):
        with self._lock:
            self._paused = True
            return {"paused": True, "active_count": len(self._active)}

    def resume(self):
        with self._lock:
            self._paused = False
            return {"paused": False, "active_count": len(self._active)}

    def worker_status(self, worker_id):
        with self._lock:
            worker = self._workers.get(worker_id)
            if worker is None:
                raise WorkerRuntimeError("Unknown worker")
            return {
                "worker_id": worker_id,
                "status": worker["status"],
                "capabilities": sorted(worker["capabilities"]),
                "active_count": len(worker["active"]),
                "max_concurrency": worker["max_concurrency"],
            }
