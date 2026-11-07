import tempfile
import unittest
from pathlib import Path

from skills.orchestration.queue import PersistentTaskQueue, QueueError


class PersistentQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "queue.sqlite"
        self.queue = PersistentTaskQueue(self.path)

    def tearDown(self):
        self.queue.close()
        self.tmp.cleanup()

    def test_enqueue_is_idempotent_for_same_task_payload(self):
        first = self.queue.enqueue("task-1", {"kind": "synthetic-check"}, max_attempts=2)
        second = self.queue.enqueue("task-1", {"kind": "synthetic-check"}, max_attempts=2)
        self.assertEqual(first["task_id"], second["task_id"])
        self.assertEqual(second["status"], "pending")
        with self.assertRaises(QueueError):
            self.queue.enqueue("task-1", {"kind": "different"}, max_attempts=2)

    def test_claim_lease_and_complete(self):
        self.queue.enqueue("task-1", {"kind": "synthetic"})
        claimed = self.queue.claim("worker-a", lease_seconds=30)
        self.assertEqual(claimed["worker_id"], "worker-a")
        self.assertEqual(claimed["status"], "running")
        done = self.queue.complete("task-1", "worker-a", {"result": "simulated"})
        self.assertEqual(done["status"], "succeeded")

    def test_worker_ownership_is_required_for_heartbeat_and_completion(self):
        self.queue.enqueue("task-1", {"kind": "synthetic"})
        self.queue.claim("worker-a")
        with self.assertRaises(QueueError):
            self.queue.heartbeat("task-1", "worker-b")
        with self.assertRaises(QueueError):
            self.queue.complete("task-1", "worker-b", {"result": "bad"})

    def test_expired_lease_can_be_reclaimed_and_old_worker_fenced(self):
        self.queue.enqueue("task-1", {"kind": "synthetic"})
        self.queue.claim("worker-a", lease_seconds=1, now=100)
        reclaimed = self.queue.claim("worker-b", lease_seconds=30, now=102)
        self.assertEqual(reclaimed["worker_id"], "worker-b")
        with self.assertRaises(QueueError):
            self.queue.complete("task-1", "worker-a", {"result": "stale"})

    def test_failure_retries_only_within_attempt_limit(self):
        self.queue.enqueue("task-1", {"kind": "synthetic"}, max_attempts=2)
        self.queue.claim("worker-a")
        pending = self.queue.fail("task-1", "worker-a", "transient")
        self.assertEqual(pending["status"], "pending")
        self.assertEqual(pending["attempts"], 1)
        self.queue.claim("worker-b")
        failed = self.queue.fail("task-1", "worker-b", "again")
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["attempts"], 2)

    def test_cancel_pending_and_running_tasks(self):
        self.queue.enqueue("pending", {"kind": "synthetic"})
        self.queue.cancel("pending", actor="operator")
        self.assertEqual(self.queue.get("pending")["status"], "cancelled")
        self.queue.enqueue("running", {"kind": "synthetic"})
        self.queue.claim("worker-a")
        self.queue.cancel("running", actor="operator")
        with self.assertRaises(QueueError):
            self.queue.complete("running", "worker-a", {"result": "late"})

    def test_persists_across_restart_and_audit_is_append_only(self):
        self.queue.enqueue("task-1", {"kind": "synthetic"})
        self.queue.close()
        self.queue = PersistentTaskQueue(self.path)
        self.assertEqual(self.queue.get("task-1")["status"], "pending")
        self.assertGreaterEqual(len(self.queue.audit_log("task-1")), 1)
        with self.assertRaises(Exception):
            self.queue.db.execute("DELETE FROM queue_events")

    def test_payload_and_result_must_be_json_objects(self):
        with self.assertRaises(QueueError):
            self.queue.enqueue("bad", ["not", "an", "object"])
        self.queue.enqueue("task-1", {"kind": "synthetic"})
        self.queue.claim("worker-a")
        with self.assertRaises(QueueError):
            self.queue.complete("task-1", "worker-a", ["not", "an", "object"])


if __name__ == "__main__":
    unittest.main()
