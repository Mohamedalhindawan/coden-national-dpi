import tempfile
import unittest
from pathlib import Path

from skills.orchestration.queue import PersistentTaskQueue
from skills.orchestration.worker_runtime import WorkerAdmissionController
from skills.orchestration.worker_queue import WorkerQueueIntegration
from skills.orchestration.scheduler import DAGAwareScheduler


class DurableWorkflowRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "queue.sqlite"
        self.tasks = [
            {"task_id": "root", "depends_on": [], "payload": {"kind": "synthetic-test"}},
            {"task_id": "child", "depends_on": ["root"], "payload": {"kind": "synthetic-test"}},
        ]

    def tearDown(self):
        self.tmp.cleanup()

    def make_runtime(self):
        queue = PersistentTaskQueue(self.db)
        workers = WorkerAdmissionController(1, ["worker-a"], ["synthetic-test"])
        workers.register_worker("worker-a", ["synthetic-test"], max_concurrency=1)
        integration = WorkerQueueIntegration(queue, workers)
        return queue, workers, integration

    def test_restart_preserves_completed_dependency_and_unlocks_child(self):
        queue, workers, integration = self.make_runtime()
        scheduler = DAGAwareScheduler(queue, integration, self.tasks)
        scheduler.enqueue_ready(now=10)
        claim = scheduler.dispatch("worker-a", now=11)
        scheduler.complete(claim, {"status": "simulated"}, now=12)
        queue.close()

        queue2, workers2, integration2 = self.make_runtime()
        scheduler2 = DAGAwareScheduler(queue2, integration2, self.tasks)
        self.assertEqual(scheduler2.states()["root"], "succeeded")
        self.assertEqual(scheduler2.enqueue_ready(now=13), ["child"])
        self.assertEqual(queue2.get("child")["status"], "pending")
        queue2.close()

    def test_restart_reclaims_expired_lease_and_rejects_stale_claim(self):
        queue, workers, integration = self.make_runtime()
        scheduler = DAGAwareScheduler(queue, integration, self.tasks)
        scheduler.enqueue_ready(now=10)
        old_claim = scheduler.dispatch("worker-a", lease_seconds=2, now=11)
        queue.close()

        queue2, workers2, integration2 = self.make_runtime()
        scheduler2 = DAGAwareScheduler(queue2, integration2, self.tasks)
        new_claim = scheduler2.dispatch("worker-a", lease_seconds=10, now=14)
        self.assertEqual(new_claim["task_id"], "root")
        self.assertNotEqual(new_claim["lease_token"], old_claim["lease_token"])
        with self.assertRaises(Exception):
            integration2.complete(old_claim, {"status": "stale"}, now=15)
        queue2.close()

    def test_restart_reconstructs_blocked_descendants(self):
        queue, workers, integration = self.make_runtime()
        scheduler = DAGAwareScheduler(queue, integration, self.tasks)
        scheduler.enqueue_ready(now=10)
        claim = scheduler.dispatch("worker-a", now=11)
        scheduler.fail(claim, "permanent", now=12)
        scheduler.refresh_blocked()
        queue.close()

        queue2, workers2, integration2 = self.make_runtime()
        scheduler2 = DAGAwareScheduler(queue2, integration2, self.tasks)
        scheduler2.refresh_blocked()
        self.assertEqual(scheduler2.states()["child"], "blocked")
        queue2.close()
