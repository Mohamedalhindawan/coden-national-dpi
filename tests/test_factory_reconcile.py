"""Read-only cross-store recovery snapshot tests: no automatic replay or approvals."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ai_factory import checkpoint, durable_queue
from ai_factory import reconcile

COMMIT = "f" * 40
HASH = "a" * 64


class ReconcileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root / "owner" / "queue.sqlite3"
        self.journals = self.root / "owner" / "journals"
        self.tasks = self.root / "owner" / "tasks"
        self.tasks.mkdir(parents=True)
        self.queue = durable_queue.DurableQueue(self.db)

    def add(self, name="t_001"):
        checkpoint.create(self.journals, name, branch="feat/demo", commit=COMMIT)
        self.queue.enqueue(name, "feat/demo", COMMIT, HASH)

    def snapshot(self):
        return reconcile.scan(self.db, self.journals)

    def row(self):
        return self.snapshot()["tasks"][0]

    def test_clean_queued_records_are_review_only(self):
        self.add()
        row = self.row()
        self.assertEqual(row["condition"], "consistent_queued")
        self.assertFalse(row["execution_authorized"])
        self.assertFalse(row["safe_to_auto_retry"])
        self.assertFalse(row["needs_attention"])

    def test_leased_with_started_checkpoint_is_in_flight_unverified(self):
        self.add()
        self.queue.claim("worker_1")
        checkpoint.record(self.journals, "t_001", event="checkpoint", next_action="offline_project_run")
        row = self.row()
        self.assertEqual(row["condition"], "active_unverified")
        self.assertTrue(row["needs_attention"])

    def test_lease_claim_crash_before_journal_advance_is_flagged(self):
        self.add()
        self.queue.claim("worker_1")
        self.assertEqual(self.row()["condition"], "claim_without_start_evidence")

    def test_completed_journal_before_queue_finish_is_detected(self):
        self.add()
        lease = self.queue.claim("worker_1")
        checkpoint.record(self.journals, "t_001", event="checkpoint")
        checkpoint.record(self.journals, "t_001", event="review_requested")
        self.assertEqual(self.row()["condition"], "journal_ahead_of_queue")
        self.queue.finish("t_001", lease["lease_token"], "awaiting_human_review")
        self.assertEqual(self.row()["condition"], "consistent_review")

    def test_needs_review_remains_manual_even_when_journal_valid(self):
        self.add()
        self.queue.claim("worker_1", now=100, lease_seconds=10)
        self.queue.recover_expired(now=111)
        self.assertEqual(self.row()["condition"], "manual_review_required")

    def test_missing_and_tampered_journals_fail_closed(self):
        self.add()
        p = self.journals / "t_001.jsonl"
        p.unlink()
        self.assertEqual(self.row()["condition"], "missing_journal")
        checkpoint.create(self.journals, "t_001", branch="feat/demo", commit=COMMIT)
        p.write_text(p.read_text().replace("feat/demo", "feat/evil"))
        self.assertEqual(self.row()["condition"], "invalid_journal")

    def test_wrong_git_commit_is_flagged(self):
        self.add()
        checkpoint.record(self.journals, "t_001", event="checkpoint", commit="b" * 40)
        self.assertEqual(self.row()["condition"], "identity_mismatch")

    def test_orphan_checkpoint_created_before_queue_insert_is_found(self):
        checkpoint.create(self.journals, "orphan_task", branch="feat/demo", commit=COMMIT)
        result = self.snapshot()
        self.assertEqual(result["tasks"][0]["condition"], "orphan_journal")
        self.assertTrue(result["needs_attention"])

    def test_task_payload_integrity_when_requested(self):
        name = "t_001"
        payload = b'{"demo": true}'
        (self.tasks / (name + ".json")).write_bytes(payload)
        from hashlib import sha256
        checkpoint.create(self.journals, name, branch="feat/demo", commit=COMMIT)
        self.queue.enqueue(name, "feat/demo", COMMIT, sha256(payload).hexdigest())
        self.assertEqual(reconcile.scan(self.db, self.journals, self.tasks)["tasks"][0]["condition"], "consistent_queued")
        (self.tasks / (name + ".json")).write_bytes(b'{"demo": false}')
        self.assertEqual(reconcile.scan(self.db, self.journals, self.tasks)["tasks"][0]["condition"], "task_hash_mismatch")

    def test_nonexistent_db_fails_without_creating_it(self):
        missing = self.root / "missing.sqlite3"
        with self.assertRaises((OSError, ValueError)):
            reconcile.scan(missing, self.journals)
        self.assertFalse(missing.exists())

    def test_cli_json_output_never_approves_execution(self):
        self.add()
        result = reconcile.main(["--queue-db", str(self.db), "--journal", str(self.journals)])
        self.assertEqual(result, 0)
        self.assertEqual(self.queue.read("t_001")["status"], "queued")

    def test_reject_journal_symlink_and_untrusted_filename(self):
        self.add()
        symlink = self.journals / "bad_t.jsonl"
        symlink.symlink_to(self.journals / "t_001.jsonl")
        result = self.snapshot()
        entries = {row["task_id"]: row for row in result["tasks"]}
        self.assertEqual(entries["bad_t"]["condition"], "invalid_journal")
        self.assertTrue(result["needs_attention"])


    def test_reject_intermediate_symlinks_in_diagnostic_paths(self):
        self.add()
        alias = self.root / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        for db, journal, tasks in (
            (alias / "owner" / "queue.sqlite3", self.journals, None),
            (self.db, alias / "owner" / "journals", None),
            (self.db, self.journals, alias / "owner" / "tasks"),
        ):
            with self.subTest(db=db, journal=journal, tasks=tasks):
                with self.assertRaises(ValueError):
                    reconcile.scan(db, journal, tasks)

    def test_directory_scan_limits_nonjournal_entries(self):
        self.add()
        for index in range(10):
            (self.journals / f"unrelated-{index}.txt").touch()
        with patch.object(reconcile, "MAX_TASKS", 2):
            with self.assertRaises(ValueError):
                self.snapshot()


if __name__ == "__main__":
    unittest.main()
