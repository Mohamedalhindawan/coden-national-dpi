import tempfile
import unittest
from pathlib import Path

from skills.orchestration.queue import PersistentTaskQueue
from skills.orchestration.worker_runtime import WorkerAdmissionController, WorkerRuntimeError
from skills.orchestration.worker_queue import WorkerQueueIntegration, IntegrationError


class WorkerQueueIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.queue = PersistentTaskQueue(Path(self.tmp.name) / "queue.sqlite")
        self.workers = WorkerAdmissionController(
            max_workers=2,
            allowed_worker_ids=["worker-a", "worker-b"],
            allowed_task_kinds=["synthetic-test", "docs-check"],
        )
        self.workers.register_worker("worker-a", ["synthetic-test"], max_concurrency=1)
        self.workers.register_worker("worker-b", ["docs-check"], max_concurrency=1)
        self.integration = WorkerQueueIntegration(self.queue, self.workers)

    def tearDown(self):
        self.queue.close()
        self.tmp.cleanup()

    def test_dispatch_claims_only_a_task_supported_by_worker(self):
        self.queue.enqueue("docs-1", {"kind": "docs-check"})
        self.queue.enqueue("test-1", {"kind": "synthetic-test"})
        claim = self.integration.dispatch("worker-a")
        self.assertEqual(claim["task_id"], "test-1")
        self.assertEqual(self.queue.get("docs-1")["status"], "pending")
        self.assertEqual(self.workers.active_count, 1)

    def test_complete_releases_worker_capacity(self):
        self.queue.enqueue("test-1", {"kind": "synthetic-test"})
        claim = self.integration.dispatch("worker-a")
        result = self.integration.complete(claim, {"status": "simulated"})
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(self.workers.active_count, 0)

    def test_failure_releases_capacity_and_respects_queue_retry(self):
        self.queue.enqueue("test-1", {"kind": "synthetic-test"}, max_attempts=2)
        claim = self.integration.dispatch("worker-a")
        failed = self.integration.fail(claim, "transient error")
        self.assertEqual(failed["status"], "pending")
        self.assertEqual(self.workers.active_count, 0)

    def test_worker_capacity_limit_prevents_second_dispatch(self):
        self.queue.enqueue("test-1", {"kind": "synthetic-test"})
        self.queue.enqueue("test-2", {"kind": "synthetic-test"})
        first = self.integration.dispatch("worker-a")
        self.assertIsNotNone(first)
        self.assertIsNone(self.integration.dispatch("worker-a"))
        self.assertEqual(self.queue.get("test-2")["status"], "pending")

    def test_expired_lease_fences_stale_claim_completion(self):
        self.queue.enqueue("test-1", {"kind": "synthetic-test"}, max_attempts=2)
        first = self.integration.dispatch("worker-a", lease_seconds=1, now=100)
        second = self.integration.dispatch("worker-a", lease_seconds=30, now=102)
        with self.assertRaises(IntegrationError):
            self.integration.complete(first, {"status": "late"})
        self.assertEqual(self.queue.get("test-1")["worker_id"], "worker-a")
        self.assertEqual(self.workers.active_count, 1)

    def test_invalid_payload_kind_is_not_dispatched(self):
        self.queue.enqueue("bad", {"kind": "unlisted"})
        self.assertIsNone(self.integration.dispatch("worker-a"))
        self.assertEqual(self.queue.get("bad")["status"], "pending")
