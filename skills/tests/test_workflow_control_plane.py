import tempfile
import unittest
from pathlib import Path

from skills.orchestration.queue import PersistentTaskQueue
from skills.orchestration.worker_runtime import WorkerAdmissionController
from skills.orchestration.worker_queue import WorkerQueueIntegration
from skills.orchestration.scheduler import DAGAwareScheduler
from skills.orchestration.control_plane import WorkflowControlPlane, ControlPlaneError


class WorkflowControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.queue = PersistentTaskQueue(Path(self.tmp.name) / "queue.sqlite")
        self.workers = WorkerAdmissionController(2, ["worker-a"], ["synthetic-test"])
        self.workers.register_worker("worker-a", ["synthetic-test"], max_concurrency=2)
        self.integration = WorkerQueueIntegration(self.queue, self.workers)
        tasks = [
            {"task_id": "root", "depends_on": [], "payload": {"kind": "synthetic-test"}},
            {"task_id": "child", "depends_on": ["root"], "payload": {"kind": "synthetic-test"}},
        ]
        self.scheduler = DAGAwareScheduler(self.queue, self.integration, tasks)
        self.control = WorkflowControlPlane(self.scheduler, self.workers)

    def tearDown(self):
        self.queue.close()
        self.tmp.cleanup()

    def test_pause_blocks_dispatch_and_resume_reopens_admission(self):
        self.control.pause()
        with self.assertRaises(ControlPlaneError):
            self.control.dispatch("worker-a", now=10)
        self.control.resume()
        claim = self.control.dispatch("worker-a", now=11)
        self.assertEqual(claim["task_id"], "root")

    def test_snapshot_reports_durable_task_states_and_worker_capacity(self):
        self.control.dispatch("worker-a", now=10)
        snapshot = self.control.snapshot()
        self.assertEqual(snapshot["tasks"]["running"], 1)
        self.assertEqual(snapshot["tasks"]["pending"], 1)
        self.assertEqual(snapshot["workers"]["active_count"], 1)
        self.assertFalse(snapshot["paused"])

    def test_reconcile_rebuilds_blocked_tasks_after_restart(self):
        self.scheduler.enqueue_ready(now=10)
        claim = self.control.dispatch("worker-a", now=11)
        self.scheduler.fail(claim, "permanent", now=12)
        report = self.control.reconcile()
        self.assertEqual(report["blocked"], ["child"])
        self.assertEqual(self.control.snapshot()["tasks"]["blocked"], 1)

    def test_unknown_task_audit_is_rejected(self):
        with self.assertRaises(ControlPlaneError):
            self.control.task_audit("missing")
