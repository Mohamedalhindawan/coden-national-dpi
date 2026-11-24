"""Bounded operator batch over the existing worker supervisor; never a daemon."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ai_factory import durable_queue, offline_worker, project, worker_supervisor, reconcile


class WorkerBatchTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.db = self.root / "queue.sqlite3"
        self.q = durable_queue.DurableQueue(self.db)
        self.tasks = self.root / "tasks"
        self.tasks.mkdir()
        self.journal = self.root / "journal"
        self.journal.mkdir()
        self.out = self.root / "outputs"
        self.out.mkdir()

    def run_batch(self, **kwargs):
        from ai_factory import worker_scheduler
        params = dict(queue_db=self.db, journal=self.journal, task_dir=self.tasks,
                      output_root=self.out, worker_id="operator", max_tasks=2,
                      timeout_seconds=20, lease_seconds=40)
        params.update(kwargs)
        return worker_scheduler.run_batch(**params)

    def add(self, task_id):
        task = json.loads(project.EXAMPLE.read_text(encoding="utf-8"))
        task["id"] = task_id
        (self.tasks / (task_id + ".json")).write_text(json.dumps(task), encoding="utf-8")
        offline_worker.submit(self.q, self.journal, self.tasks, task_id,
                              branch="feat/p1", commit="d"*40)

    def test_empty_queue_never_starts_worker(self):
        with patch.object(worker_supervisor, "run_once") as worker:
            result = self.run_batch()
        worker.assert_not_called()
        self.assertEqual(result["status"], "idle")
        self.assertFalse(result["execution_authorized"])

    def test_invalid_limits_rejected_before_worker(self):
        with patch.object(worker_supervisor, "run_once") as worker:
            for value in (0, 11, True, 1.5):
                with self.assertRaises(ValueError):
                    self.run_batch(max_tasks=value)
            with self.assertRaises(ValueError):
                self.run_batch(timeout_seconds=40, lease_seconds=40)
        worker.assert_not_called()

    def test_orphan_blocks_other_queued_work(self):
        from ai_factory import checkpoint
        self.add("ready")
        checkpoint.create(self.journal, "orphan", branch="feat/p1", commit="d"*40)
        with patch.object(worker_supervisor, "run_once") as worker:
            result = self.run_batch()
        worker.assert_not_called()
        self.assertEqual(result["status"], "reconciliation_required")
        self.assertEqual(self.q.read("ready")["attempts"], 0)

    def test_uncertain_worker_result_stops_batch_without_retry(self):
        self.add("one")
        self.add("two")
        with patch.object(worker_supervisor, "run_once", return_value={
            "status":"timed_out_review_required", "execution_authorized":False,
            "automatic_retry_allowed":False}) as worker:
            result = self.run_batch()
        worker.assert_called_once()
        self.assertEqual(result["status"], "worker_review_required")
        self.assertFalse(result["automatic_retry_allowed"])

    def test_unsafe_receipt_is_rejected(self):
        self.add("one")
        with patch.object(worker_supervisor, "run_once", return_value={
            "status":"awaiting_human_review", "execution_authorized":True,
            "automatic_retry_allowed":False}) as worker:
            result = self.run_batch()
        worker.assert_called_once()
        self.assertEqual(result["status"], "worker_review_required")
        self.assertFalse(result["execution_authorized"])

    def test_real_two_task_batch_stops_at_limit(self):
        if not project.supported_host() and os.getenv("CODEN_REQUIRE_SANDBOX") != "1":
            self.skipTest("requires pinned Linux sandbox")
        for task_id in ("one", "two", "three"):
            self.add(task_id)
        result = self.run_batch()
        self.assertEqual(result["status"], "batch_limit_reached")
        self.assertEqual(result["review_candidates"], 2)
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["automatic_retry_allowed"])
        self.assertEqual(len(list(self.out.glob("*/candidate.pyz"))), 2)
        report = reconcile.scan(self.db, self.journal, self.tasks)
        self.assertEqual(report["conditions"], {"consistent_queued":1, "consistent_review":2})
        self.assertEqual(sum(self.q.read(x)["attempts"] for x in ("one","two","three")), 2)
