"""Read-only aggregate health of the existing synthetic queue."""
import json
from pathlib import Path
import tempfile
import unittest
from ai_factory import checkpoint, durable_queue, offline_worker, project


class QueueHealthTests(unittest.TestCase):
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

    def health(self, now=1011):
        from ai_factory import queue_health
        return queue_health.snapshot(self.db, self.journal, self.tasks, now=now)

    def add(self, task_id):
        task = json.loads(project.EXAMPLE.read_text(encoding="utf-8"))
        task["id"] = task_id
        (self.tasks / (task_id + ".json")).write_text(json.dumps(task), encoding="utf-8")
        offline_worker.submit(self.q, self.journal, self.tasks, task_id,
                              branch="feat/p1", commit="d"*40)

    def test_empty_queue_is_not_proof_of_worker_availability(self):
        result = self.health()
        self.assertEqual(result["queue_depth"], 0)
        self.assertEqual(result["expired_leases"], 0)
        self.assertEqual(result["worker_availability"], "unverified")
        self.assertFalse(result["execution_authorized"])
        self.assertTrue(result["read_only"])

    def test_queued_and_expired_leases_count_without_recovery_or_secret_disclosure(self):
        self.add("one")
        self.add("two")
        lease = self.q.claim("worker", now=1000, lease_seconds=10)
        before = self.db.read_bytes()
        result = self.health()
        self.assertEqual(result["queue_depth"], 1)
        self.assertEqual(result["leased"], 1)
        self.assertEqual(result["expired_leases"], 1)
        self.assertTrue(result["needs_attention"])
        self.assertNotIn(lease["lease_token"], json.dumps(result))
        self.assertEqual(before, self.db.read_bytes())
        self.assertEqual(self.q.read(lease["task_id"])["status"], "leased")

    def test_expiry_boundary_matches_existing_queue(self):
        self.add("one")
        self.q.claim("worker", now=1000, lease_seconds=10)
        self.assertEqual(self.health(now=1010)["expired_leases"], 0)
        self.assertEqual(self.health(now=1011)["expired_leases"], 1)

    def test_orphan_report_is_aggregate_only(self):
        checkpoint.create(self.journal, "orphan", branch="feat/p1", commit="d"*40)
        report = self.health()
        self.assertEqual(report["conditions"], {"orphan_journal": 1})
        self.assertTrue(report["needs_attention"])
        self.assertNotIn("task_id", json.dumps(report))
        self.assertNotIn("feat/p1", json.dumps(report))

    def test_invalid_timestamp_rejected(self):
        for now in (True, -1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                self.health(now)


    def test_health_detects_queue_change_between_read_only_snapshots(self):
        from unittest.mock import patch
        from ai_factory import reconcile
        self.add("one")
        real_scan = reconcile.scan
        def scan_after_claim(*args, **kwargs):
            self.q.claim("operator", now=1000, lease_seconds=30)
            return real_scan(*args, **kwargs)
        with patch.object(reconcile, "scan", side_effect=scan_after_claim):
            result = self.health()
        self.assertFalse(result["snapshot_counts_consistent"])
        self.assertTrue(result["needs_attention"])
        self.assertFalse(result["automatic_retry_allowed"])
        self.assertEqual(result["conditions"], {"claim_without_start_evidence": 1})

    def test_health_stable_counts_are_not_atomicity_or_runtime_proof(self):
        self.add("one")
        result = self.health()
        self.assertTrue(result["snapshot_counts_consistent"])
        self.assertFalse(result["snapshot_atomic"])
        self.assertFalse(result["execution_authorized"])
