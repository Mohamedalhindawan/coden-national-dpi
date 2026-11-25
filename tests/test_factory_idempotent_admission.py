"""P1 immutable admission receipts: no task replay or orphan repair."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ai_factory import checkpoint, durable_queue, offline_worker, project


class IdempotentAdmissionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.tasks = root / "tasks"
        self.tasks.mkdir()
        self.journal = root / "journal"
        self.q = durable_queue.DurableQueue(root / "queue.sqlite3")
        self.task = json.loads(project.EXAMPLE.read_text(encoding="utf-8"))
        self.id = self.task["id"]
        self.path = self.tasks / (self.id + ".json")
        self.path.write_text(json.dumps(self.task), encoding="utf-8")

    def submit(self, branch="feat/p1", commit="d" * 40):
        return offline_worker.submit_idempotent(self.q, self.journal, self.tasks,
                                                self.id, branch=branch, commit=commit)

    def test_exact_repeated_admission_returns_receipt_without_mutation(self):
        first = self.submit()
        before = (self.journal / (self.id + ".jsonl")).read_bytes()
        with patch.object(self.q, "enqueue", side_effect=AssertionError("duplicate enqueue")):
            again = self.submit()
        self.assertEqual(first, again)
        self.assertEqual(before, (self.journal / (self.id + ".jsonl")).read_bytes())
        self.assertEqual(self.q.read(self.id)["attempts"], 0)
        self.assertFalse(again["execution_authorized"])

    def test_conflicting_identity_rejected(self):
        self.submit()
        for branch, commit in (("feat/other", "d"*40), ("feat/p1", "e"*40)):
            with self.assertRaises(ValueError):
                self.submit(branch, commit)
        self.task["description"] = "Different synthetic requirement"
        self.path.write_text(json.dumps(self.task), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.submit()

    def test_orphan_journal_never_silently_enqueued(self):
        checkpoint.create(self.journal, self.id, branch="feat/p1", commit="d"*40)
        with self.assertRaises((ValueError, FileExistsError)):
            self.submit()
        with self.assertRaises(ValueError):
            self.q.read(self.id)

    def test_missing_journal_for_existing_queue_fails_closed(self):
        self.submit()
        (self.journal / (self.id + ".jsonl")).unlink()
        with self.assertRaises((ValueError, OSError)):
            self.submit()

    def test_expired_job_never_requeued_by_duplicate_admission(self):
        self.submit()
        self.q.claim("worker", now=1000, lease_seconds=10)
        self.q.recover_expired(now=1011)
        state = self.submit()
        self.assertEqual(state["status"], "needs_review")
        self.assertFalse(state["execution_authorized"])
        self.assertEqual(self.q.read(self.id)["attempts"], 1)
        self.assertIsNone(self.q.claim("other", now=1012))

    def test_journal_identity_conflict_rejected(self):
        self.submit()
        checkpoint.record(self.journal, self.id, event="checkpoint", commit="e"*40)
        with self.assertRaises(ValueError):
            self.submit()
