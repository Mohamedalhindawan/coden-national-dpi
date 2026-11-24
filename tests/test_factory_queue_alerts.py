"""Aggregate local alert decisions, no delivery, retry or task mutation."""
import json
from pathlib import Path
import tempfile
import unittest
from ai_factory import checkpoint, durable_queue, offline_worker, project


class QueueAlertTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.db = self.root / "queue.sqlite3"
        self.q = durable_queue.DurableQueue(self.db)
        self.tasks = self.root / "tasks"
        self.tasks.mkdir()
        self.journal = self.root / "journal"
        self.journal.mkdir()

    def add(self, task_id):
        task = json.loads(project.EXAMPLE.read_text(encoding="utf-8"))
        task["id"] = task_id
        (self.tasks / (task_id + ".json")).write_text(json.dumps(task), encoding="utf-8")
        offline_worker.submit(self.q, self.journal, self.tasks, task_id,
                              branch="feat/p1", commit="d"*40)

    def check(self, **kwargs):
        from ai_factory import queue_alerts
        return queue_alerts.evaluate(self.db, self.journal, self.tasks, now=1011, **kwargs)

    def test_empty_is_not_worker_liveness_proof(self):
        report = self.check()
        self.assertEqual(report["alerts"], [])
        self.assertEqual(report["worker_availability"], "unverified")
        self.assertFalse(report["delivery_performed"])
        self.assertFalse(report["execution_authorized"])

    def test_expired_lease_alert_does_not_recover_or_disclose(self):
        self.add("private_task_identifier")
        lease = self.q.claim("worker", now=1000, lease_seconds=10)
        before = self.db.read_bytes()
        result = self.check()
        self.assertIn({"code":"expired_leases","severity":"warning","count":1}, result["alerts"])
        self.assertNotIn(lease["lease_token"], json.dumps(result))
        self.assertNotIn("private_task_identifier", json.dumps(result))
        self.assertEqual(before, self.db.read_bytes())
        self.assertFalse(result["automatic_retry_allowed"])

    def test_orphan_requires_review(self):
        checkpoint.create(self.journal, "orphan", branch="feat/p1", commit="d"*40)
        self.assertIn("reconciliation_required", [a["code"] for a in self.check()["alerts"]])

    def test_backlog_threshold(self):
        self.add("one")
        self.add("two")
        self.assertNotIn("queue_backlog", [a["code"] for a in self.check(backlog_threshold=3)["alerts"]])
        self.assertIn({"code":"queue_backlog","severity":"warning","count":2},
                      self.check(backlog_threshold=2)["alerts"])

    def test_invalid_threshold_fails_closed(self):
        for value in (True, 0, -1, 1.5, 1001):
            with self.assertRaises(ValueError):
                self.check(backlog_threshold=value)
