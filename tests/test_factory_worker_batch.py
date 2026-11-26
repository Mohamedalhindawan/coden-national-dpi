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


    def test_second_batch_refused_while_first_holds_lock(self):
        self.add("one")
        nested = []
        def worker(**kwargs):
            nested.append(self.run_batch())
            return {"status":"timed_out_review_required", "execution_authorized":False,
                    "automatic_retry_allowed":False}
        with patch.object(worker_supervisor, "run_once", side_effect=worker) as call:
            # Avoid recursion on the RED baseline if no lock exists.
            def bounded_worker(**kwargs):
                if nested or call.call_count > 1:
                    return {"status":"timed_out_review_required", "execution_authorized":False,
                            "automatic_retry_allowed":False}
                return worker(**kwargs)
            call.side_effect = bounded_worker
            result = self.run_batch()
        self.assertEqual(call.call_count, 1)
        self.assertEqual(nested[0]["status"], "batch_busy")
        self.assertEqual(result["status"], "worker_review_required")
        self.assertEqual(self.q.read("one")["attempts"], 0)

    def test_lock_released_after_worker_error(self):
        self.add("one")
        with patch.object(worker_supervisor, "run_once", side_effect=ValueError("synthetic")) as call:
            self.assertEqual(self.run_batch()["status"], "worker_review_required")
            self.assertEqual(self.run_batch()["status"], "worker_review_required")
        self.assertEqual(call.call_count, 2)

    def test_symlink_lock_refused_without_touching_target(self):
        self.add("one")
        target = self.root / "protected"
        target.write_text("unchanged")
        Path(str(self.db) + ".batch.lock").symlink_to(target)
        with patch.object(worker_supervisor, "run_once") as worker:
            with self.assertRaises((OSError, ValueError)):
                self.run_batch()
        worker.assert_not_called()
        self.assertEqual(target.read_text(), "unchanged")

    def test_external_process_lock_is_respected_and_released_on_exit(self):
        import subprocess
        import sys
        self.add("one")
        lock = Path(str(self.db) + ".batch.lock")
        script = (
            "import fcntl, os, sys; "
            "fd=os.open(sys.argv[1], os.O_CREAT|os.O_RDWR, 0o600); "
            "fcntl.flock(fd, fcntl.LOCK_EX); "
            "print('locked',flush=True); sys.stdin.read()"
        )
        with subprocess.Popen([sys.executable, "-c", script, str(lock)],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              text=True) as child:
            try:
                self.assertEqual(child.stdout.readline().strip(), "locked")
                with patch.object(worker_supervisor, "run_once") as worker:
                    self.assertEqual(self.run_batch()["status"], "batch_busy")
                    worker.assert_not_called()
            finally:
                child.stdin.close()
                child.wait(timeout=5)
        with patch.object(worker_supervisor, "run_once", side_effect=ValueError("synthetic")) as worker:
            self.assertEqual(self.run_batch()["status"], "worker_review_required")
            worker.assert_called_once()


    def test_batch_budget_rejects_insufficient_time_before_dispatch(self):
        self.add("one")
        with patch.object(worker_supervisor, "run_once") as worker:
            result = self.run_batch(max_batch_seconds=10)
        worker.assert_not_called()
        self.assertEqual(result["status"], "batch_time_budget_exhausted")
        self.assertEqual(result["review_candidates"], 0)
        self.assertEqual(self.q.read("one")["attempts"], 0)

    def test_batch_budget_stops_second_dispatch_without_retry(self):
        from ai_factory import checkpoint, worker_scheduler
        self.add("one")
        self.add("two")
        now = [100.0]
        def finish_first(**kwargs):
            lease = self.q.claim("operator", task_id="one", lease_seconds=40)
            checkpoint.record(self.journal, "one", event="checkpoint")
            checkpoint.record(self.journal, "one", event="review_requested")
            self.q.finish("one", lease["lease_token"], "awaiting_human_review")
            now[0] += 35
            return {"status": "awaiting_human_review", "execution_authorized": False,
                    "automatic_retry_allowed": False}
        with patch.object(worker_scheduler, "_monotonic", side_effect=lambda: now[0]), \
                patch.object(worker_supervisor, "run_once", side_effect=finish_first) as worker:
            result = self.run_batch(max_batch_seconds=60)
        self.assertEqual(result["status"], "batch_time_budget_exhausted")
        self.assertEqual(result["review_candidates"], 1)
        worker.assert_called_once()
        self.assertEqual(self.q.read("one")["attempts"], 1)
        self.assertEqual(self.q.read("two")["attempts"], 0)
        self.assertFalse(result["automatic_retry_allowed"])

    def test_invalid_batch_time_budget_rejected(self):
        with patch.object(worker_supervisor, "run_once") as worker:
            for value in (0, True, -1, 3601, 1.5):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    self.run_batch(max_batch_seconds=value)
            worker.assert_not_called()
