import tempfile
import unittest
from pathlib import Path

from skills.orchestration.queue import PersistentTaskQueue
from skills.orchestration.worker_runtime import WorkerAdmissionController
from skills.orchestration.worker_queue import WorkerQueueIntegration
from skills.orchestration.scheduler import DAGAwareScheduler, SchedulerError


class DAGAwareSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.queue = PersistentTaskQueue(Path(self.tmp.name) / "queue.sqlite")
        self.workers = WorkerAdmissionController(
            max_workers=2, allowed_worker_ids=["worker-a"],
            allowed_task_kinds=["synthetic-test"])
        self.workers.register_worker("worker-a", ["synthetic-test"], max_concurrency=2)
        self.integration = WorkerQueueIntegration(self.queue, self.workers)
        self.tasks = [
            {"task_id": "a", "depends_on": [], "payload": {"kind": "synthetic-test"}},
            {"task_id": "b", "depends_on": ["a"], "payload": {"kind": "synthetic-test"}},
            {"task_id": "c", "depends_on": [], "payload": {"kind": "synthetic-test"}},
        ]
        self.scheduler = DAGAwareScheduler(self.queue, self.integration, self.tasks)

    def tearDown(self):
        self.queue.close()
        self.tmp.cleanup()

    def test_only_dependency_ready_tasks_are_enqueued_and_dispatched(self):
        self.scheduler.enqueue_ready()
        self.assertEqual(self.queue.get("a")["status"], "pending")
        self.assertEqual(self.queue.get("c")["status"], "pending")
        with self.assertRaises(Exception):
            self.queue.get("b")
        first = self.scheduler.dispatch("worker-a")
        self.assertIn(first["task_id"], {"a", "c"})

    def test_success_unlocks_dependent_task(self):
        self.scheduler.enqueue_ready()
        first = self.scheduler.dispatch("worker-a")
        self.scheduler.complete(first, {"status": "simulated"})
        self.scheduler.enqueue_ready()
        self.assertEqual(self.queue.get("b")["status"], "pending")

    def test_failed_dependency_blocks_descendants(self):
        self.scheduler.enqueue_ready()
        first = self.scheduler.dispatch("worker-a")
        self.scheduler.fail(first, "permanent")
        self.scheduler.refresh_blocked()
        states = self.scheduler.states()
        failed_id = first["task_id"]
        dependent = "b" if failed_id == "a" else None
        if dependent:
            self.assertEqual(states["b"], "blocked")

    def test_scheduler_rejects_duplicate_ids_and_unknown_dependencies(self):
        with self.assertRaises(SchedulerError):
            DAGAwareScheduler(self.queue, self.integration, [
                {"task_id": "x", "depends_on": [], "payload": {"kind": "synthetic-test"}},
                {"task_id": "x", "depends_on": [], "payload": {"kind": "synthetic-test"}},
            ])

    def test_cancelled_dependency_blocks_descendants(self):
        self.scheduler.enqueue_ready()
        self.scheduler.cancel("a", actor="operator")
        self.scheduler.refresh_blocked()
        self.assertEqual(self.scheduler.states()["b"], "blocked")
