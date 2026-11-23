"""RED/GREEN: real SQLite worker queue admission/recovery view, not a fake model.

The Qwen-generated synthetic 'lease_expired' helper in Draft PR #169
is a research candidate. Real queue status is authoritative here.
"""
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout

from ai_factory import durable_queue
from ai_factory import factory_worker_recovery_status as status

SHA = "c" * 40
HASH = "1" * 64


class WorkerRecoveryReadOnlyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "operator" / "queue.sqlite3"
        self.q = durable_queue.DurableQueue(self.path)

    def enqueue(self, name):
        self.q.enqueue(name, "feat/worker-pilot", SHA, HASH)

    def test_real_sqlite_lease_expiry_and_quarantine_not_synthetic_counts(self):
        for name in ("task_a", "task_b", "task_c"):
            self.enqueue(name)
        first = self.q.claim("worker_a", now=1000, lease_seconds=20)
        self.assertEqual(first["task_id"], "task_a")
        self.assertEqual(self.q.recover_expired(now=1021), 1)
        second = self.q.claim("worker_b", now=1030, lease_seconds=20)
        self.assertEqual(second["task_id"], "task_b")
        before = self.path.read_bytes()
        stat_before = self.path.stat()
        report = status.snapshot(self.path, now=1060)
        self.assertEqual(report["source"], "real_durable_queue_sqlite_metadata")
        self.assertEqual(report["total_tasks"], 3)
        self.assertEqual(report["queued"], 1)
        self.assertEqual(report["leased_active"], 0)
        self.assertEqual(report["leased_expired_pending_review"], 1)
        self.assertEqual(report["needs_review_quarantined"], 1)
        self.assertEqual(report["manual_attention_total"], 2)
        self.assertEqual(report["cancellation_support"], "REQUEST_ONLY_NO_PROCESS_TERMINATION")
        self.assertEqual(report["qwen_candidate_status"], "QUARANTINED_NOT_EXECUTED")
        self.assertFalse(report["automatic_retry_authorized"])
        self.assertFalse(report["queue_modified"])
        self.assertFalse(report["worker_executed"])
        self.assertFalse(report["release_authorized"])
        self.assertEqual(report["paid_calls"], 0)
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(stat_before.st_mtime_ns, self.path.stat().st_mtime_ns)
        self.assertEqual(self.q.read("task_a")["status"], "needs_review")
        self.assertEqual(self.q.read("task_b")["status"], "leased")
        self.assertEqual(self.q.read("task_c")["status"], "queued")

    def test_exact_expiry_boundary_and_other_terminal_states(self):
        self.enqueue("task_x")
        lease = self.q.claim("worker_x", now=100, lease_seconds=10)
        self.assertEqual(status.snapshot(self.path, now=110)["leased_expired_pending_review"], 0)
        self.assertEqual(status.snapshot(self.path, now=110)["leased_active"], 1)
        self.assertEqual(status.snapshot(self.path, now=110.001)["leased_expired_pending_review"], 1)
        self.q.finish("task_x", lease["lease_token"], "blocked", now=109)
        r = status.snapshot(self.path, now=130)
        self.assertEqual(r["blocked"], 1)
        self.assertEqual(r["leased_expired_pending_review"], 0)
        self.assertEqual(r["manual_attention_total"], 0)

    def test_never_exposes_lease_secrets_worker_identifiers_or_task_ids(self):
        self.enqueue("private_looking_task")
        self.q.claim("secret_worker", now=100, lease_seconds=20)
        receipt = json.dumps(status.snapshot(self.path, now=140), sort_keys=True)
        self.assertNotIn("private_looking_task", receipt)
        self.assertNotIn("secret_worker", receipt)
        self.assertNotIn("lease_token", receipt)
        self.assertNotIn(HASH, receipt)
        self.assertNotIn(SHA, receipt)
        self.assertEqual(status.snapshot(self.path, now=140)["manual_attention_total"], 1)

    def test_rejects_symlink_missing_db_unsupported_schema_and_unknown_state(self):
        sym = self.root / "link.sqlite3"
        sym.symlink_to(self.path)
        with self.assertRaises(ValueError):
            status.snapshot(sym, now=100)
        with self.assertRaises(ValueError):
            status.snapshot(self.root / "missing.sqlite3", now=100)
        self.assertFalse((self.root / "missing.sqlite3").exists())
        wrong = self.root / "wrong.sqlite3"
        with sqlite3.connect(wrong) as db:
            db.execute("CREATE TABLE tasks (id INTEGER)")
        with self.assertRaises(ValueError):
            status.snapshot(wrong, now=100)
        self.enqueue("task_unknown")
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE tasks SET status='cancel_requested'")
        with self.assertRaises(ValueError):
            status.snapshot(self.path, now=100)

    def test_bad_lease_metadata_and_nonfinite_times_fail_closed(self):
        self.enqueue("task_one")
        self.q.claim("worker", now=100, lease_seconds=20)
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE tasks SET lease_until=NULL WHERE task_id='task_one'")
        with self.assertRaises(ValueError):
            status.snapshot(self.path, now=125)
        for bad in (True, "now", -1, float("nan"), float("inf")):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                status.snapshot(self.path, now=bad)

    def test_cli_reports_real_read_only_queue_and_never_recovers_automatically(self):
        self.enqueue("cli_task")
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = status.main(["--db", str(self.path), "--now", "200", "--json"])
        self.assertEqual(exit_code, 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["queued"], 1)
        self.assertEqual(result["manual_attention_total"], 0)
        self.assertFalse(result["queue_modified"])
        self.assertEqual(self.q.read("cli_task")["status"], "queued")


if __name__ == "__main__":
    unittest.main()
