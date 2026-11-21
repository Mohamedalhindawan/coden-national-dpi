"""Durable, offline, non-executing factory checkpoint journal tests."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ai_factory import checkpoint


COMMIT = "a" * 40


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "journals"

    def create(self, task="task_1"):
        return checkpoint.create(self.root, task, branch="feat/factory", commit=COMMIT)

    def test_new_checkpoint_is_prepared_not_approved(self):
        state = self.create()
        self.assertEqual(state["status"], "prepared")
        self.assertFalse(state["execution_authorized"])
        self.assertEqual(state["last_commit"], COMMIT)
        self.assertEqual(state["event_count"], 1)
        self.assertTrue(state["verified"])

    def test_quota_exhaustion_records_pause_and_resume_request_only(self):
        self.create()
        paused = checkpoint.record(self.root, "task_1", event="quota_exceeded", next_action="try_approved_fallback")
        self.assertEqual(paused["status"], "paused")
        self.assertEqual(paused["pause_reason"], "quota_exceeded")
        self.assertEqual(paused["next_action"], "try_approved_fallback")
        with self.assertRaises(ValueError):
            checkpoint.record(self.root, "task_1", event="checkpoint")
        waiting = checkpoint.record(self.root, "task_1", event="resume_requested")
        self.assertEqual(waiting["status"], "pending_human_resume")
        self.assertFalse(waiting["execution_authorized"])
        resumed_record = checkpoint.record(self.root, "task_1", event="checkpoint", commit="b" * 40)
        self.assertEqual(resumed_record["last_commit"], "b" * 40)
        self.assertEqual(resumed_record["status"], "checkpointed")

    def test_context_provider_budget_worker_are_paused(self):
        for kind in ("context_exceeded", "provider_unavailable", "budget_exceeded", "worker_failed"):
            with self.subTest(kind=kind):
                task = kind
                self.create(task)
                result = checkpoint.record(self.root, task, event=kind)
                self.assertEqual(result["status"], "paused")
                self.assertEqual(result["pause_reason"], kind)

    def test_blocked_and_review_requested_are_not_approvals(self):
        self.create()
        reviewed = checkpoint.record(self.root, "task_1", event="review_requested")
        self.assertEqual(reviewed["status"], "awaiting_human_review")
        self.assertFalse(reviewed["execution_authorized"])
        with self.assertRaises(ValueError):
            checkpoint.record(self.root, "task_1", event="resume_requested")

    def test_bad_id_branch_commit_and_next_action_fail_closed(self):
        for task in ("../etc", "x/y", "", "x" * 65):
            with self.subTest(task=task), self.assertRaises(ValueError):
                checkpoint.create(self.root, task, branch="feat/factory", commit=COMMIT)
        with self.assertRaises(ValueError):
            checkpoint.create(self.root, "ok", branch="../oops", commit=COMMIT)
        with self.assertRaises(ValueError):
            checkpoint.create(self.root, "ok", branch="feat/factory", commit="unknown")
        self.create()
        with self.assertRaises(ValueError):
            checkpoint.record(self.root, "task_1", event="checkpoint", next_action=";rm -rf /")
        with self.assertRaises(ValueError):
            checkpoint.record(self.root, "task_1", event="approved")

    def test_reopen_persisted_journal_and_hash_chain(self):
        self.create()
        checkpoint.record(self.root, "task_1", event="checkpoint", event_key="first")
        data = checkpoint.read(self.root, "task_1")
        self.assertEqual(data["status"], "checkpointed")
        self.assertEqual(data["event_count"], 2)
        lines = [json.loads(x) for x in (self.root / "task_1.jsonl").read_text().splitlines()]
        self.assertEqual(lines[1]["prev_sha256"], lines[0]["sha256"])

    def test_same_event_key_idempotent_but_conflicting_replay_rejected(self):
        self.create()
        before = checkpoint.record(self.root, "task_1", event="checkpoint", event_key="checkpoint_one")
        same = checkpoint.record(self.root, "task_1", event="checkpoint", event_key="checkpoint_one")
        self.assertEqual(before["event_count"], same["event_count"])
        with self.assertRaises(ValueError):
            checkpoint.record(self.root, "task_1", event="worker_failed", event_key="checkpoint_one")

    def test_corrupted_journal_is_detected_not_silently_repaired(self):
        self.create()
        file = self.root / "task_1.jsonl"
        file.write_text(file.read_text().replace("feat/factory", "feat/changed"))
        with self.assertRaises(ValueError):
            checkpoint.read(self.root, "task_1")
        with self.assertRaises(ValueError):
            checkpoint.record(self.root, "task_1", event="checkpoint")

    def test_truncated_journal_fails_closed(self):
        self.create()
        with (self.root / "task_1.jsonl").open("ab") as log:
            log.write(b'{"truncated":')
        with self.assertRaises(ValueError):
            checkpoint.read(self.root, "task_1")

    def test_refuse_existing_checkpoint_and_symlink(self):
        self.create()
        with self.assertRaises(FileExistsError):
            self.create()
        (self.root / "bad.jsonl").symlink_to(self.root / "task_1.jsonl")
        with self.assertRaises(OSError):
            checkpoint.read(self.root, "bad")

    def test_absent_journal_errors(self):
        with self.assertRaises(FileNotFoundError):
            checkpoint.read(self.root, "missing")

    def test_cli_offline_round_trip(self):
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]))
        base = [sys.executable, "-m", "ai_factory.checkpoint", "--store", str(self.root)]
        def call(*args):
            return subprocess.run(base + list(args), cwd=Path(__file__).resolve().parents[1], env=env, text=True, capture_output=True)
        first = call("create", "task_2", "--branch", "feat/safe", "--commit", COMMIT)
        self.assertEqual(first.returncode, 0, first.stderr)
        record = call("record", "task_2", "--event", "quota_exceeded", "--next-action", "approved_alternative")
        self.assertEqual(record.returncode, 0, record.stderr)
        state = json.loads(call("show", "task_2").stdout)
        self.assertEqual(state["status"], "paused")
        self.assertFalse(state["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
