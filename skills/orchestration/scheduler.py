"""DAG-aware queue scheduler; planning and dispatch control only, never execution."""
from skills.orchestration.dag import DAGError, build_execution_plan, propagate_blocked
from skills.orchestration.queue import QueueError
from skills.orchestration.worker_queue import IntegrationError


class SchedulerError(ValueError):
    pass


class DAGAwareScheduler:
    def __init__(self, queue, integration, tasks):
        self.queue = queue
        self.integration = integration
        if not isinstance(tasks, list) or not tasks:
            raise SchedulerError("tasks must be a non-empty list")
        self.tasks = {}
        normalized = []
        for item in tasks:
            if not isinstance(item, dict):
                raise SchedulerError("each task must be an object")
            task_id = item.get("task_id")
            payload = item.get("payload")
            dependencies = item.get("depends_on", [])
            if not isinstance(task_id, str) or not task_id.strip():
                raise SchedulerError("task_id is required")
            if task_id in self.tasks:
                raise SchedulerError("duplicate task_id: " + task_id)
            if not isinstance(payload, dict) or not isinstance(payload.get("kind"), str):
                raise SchedulerError("task payload requires a string kind")
            if not isinstance(dependencies, list):
                raise SchedulerError("depends_on must be a list")
            self.tasks[task_id] = {"payload": payload, "depends_on": dependencies}
            normalized.append({"task_id": task_id, "depends_on": dependencies})
        try:
            self.plan = build_execution_plan(normalized)
        except DAGError as exc:
            raise SchedulerError(str(exc)) from exc
        self._known_queue_ids = set()
        self._blocked = set()

    def _queue_states(self):
        result = {task_id: "pending" for task_id in self.tasks}
        for task_id in self.tasks:
            try:
                status = self.queue.get(task_id)["status"]
            except QueueError:
                continue
            result[task_id] = {
                "pending": "pending", "running": "running",
                "succeeded": "succeeded", "failed": "failed",
                "cancelled": "cancelled",
            }[status]
        return result

    def states(self):
        current = self._queue_states()
        try:
            blocked = propagate_blocked(
                [{"task_id": task_id, "depends_on": item["depends_on"]}
                 for task_id, item in self.tasks.items()], current)
        except DAGError as exc:
            raise SchedulerError(str(exc)) from exc
        self._blocked.update(blocked)
        for task_id in self._blocked:
            current[task_id] = "blocked"
        return current

    def enqueue_ready(self, now=None):
        current = self.states()
        ready = []
        for task_id in self._ready_ids(current):
            if task_id in self._known_queue_ids:
                continue
            task = self.tasks[task_id]
            try:
                self.queue.enqueue(task_id, task["payload"], now=now)
            except QueueError as exc:
                raise SchedulerError(str(exc)) from exc
            self._known_queue_ids.add(task_id)
            ready.append(task_id)
        return ready

    def _ready_ids(self, current):
        # A pending task already present in the queue is ready only if every
        # dependency is still successful; the queue itself remains the source of lease state.
        pending_graph = [
            {"task_id": task_id, "depends_on": item["depends_on"]}
            for task_id, item in self.tasks.items()
        ]
        from skills.orchestration.dag import ready_tasks
        try:
            return ready_tasks(pending_graph, current)
        except DAGError as exc:
            raise SchedulerError(str(exc)) from exc

    def dispatch(self, worker_id, lease_seconds=60, now=None):
        self.enqueue_ready(now=now)
        try:
            claim = self.integration.dispatch(worker_id, lease_seconds=lease_seconds, now=now)
        except IntegrationError as exc:
            raise SchedulerError(str(exc)) from exc
        if claim is not None and claim["task_id"] not in self.tasks:
            raise SchedulerError("Queue returned a task outside this scheduler graph")
        return claim

    def complete(self, claim, result, now=None):
        task_id = claim.get("task_id") if isinstance(claim, dict) else None
        if task_id not in self.tasks:
            raise SchedulerError("Claim is not part of this DAG")
        try:
            return self.integration.complete(claim, result, now=now)
        except IntegrationError as exc:
            raise SchedulerError(str(exc)) from exc

    def fail(self, claim, reason, now=None):
        task_id = claim.get("task_id") if isinstance(claim, dict) else None
        if task_id not in self.tasks:
            raise SchedulerError("Claim is not part of this DAG")
        try:
            return self.integration.fail(claim, reason, now=now)
        except IntegrationError as exc:
            raise SchedulerError(str(exc)) from exc

    def cancel(self, task_id, actor, now=None):
        if task_id not in self.tasks:
            raise SchedulerError("Unknown DAG task: " + str(task_id))
        try:
            return self.queue.cancel(task_id, actor=actor, now=now)
        except QueueError as exc:
            raise SchedulerError(str(exc)) from exc

    def refresh_blocked(self):
        current = self._queue_states()
        try:
            blocked = propagate_blocked(
                [{"task_id": task_id, "dependencies": item["depends_on"]}
                 for task_id, item in self.tasks.items()],
                current,
            )
        except DAGError as exc:
            raise SchedulerError(str(exc)) from exc
        for task_id in blocked:
            self._blocked.add(task_id)
            # A dependent may already be pending in the queue. Cancel it to
            # invalidate any claim and preserve a terminal blocked state locally.
            try:
                row = self.queue.get(task_id)
            except QueueError:
                continue
            if row["status"] in {"pending", "running"}:
                self.queue.cancel(task_id, actor="dag-scheduler")
        return blocked
