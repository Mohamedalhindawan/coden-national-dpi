"""End-to-end, offline, synthetic-only queue → checkpoint → project worker tests."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ai_factory import checkpoint, durable_queue, project, reconcile
from ai_factory import offline_worker

SHA = "d" * 40


class OfflineWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.tasks = self.root / "tasks"
        self.tasks.mkdir()
        self.logs = self.root / "operator" / "journal"
        self.queue = durable_queue.DurableQueue(self.root / "operator" / "queue.sqlite3")
        self.out = self.root / "outputs"
        self.out.mkdir()
        self.task = json.loads(project.EXAMPLE.read_text(encoding="utf-8"))
        self.id = self.task["id"]
        self.path = self.tasks / (self.id + ".json")
        self.write_task()

    def write_task(self):
        self.path.write_text(json.dumps(self.task, ensure_ascii=False), encoding="utf-8")

    def submit(self):
        return offline_worker.submit(self.queue, self.logs, self.tasks, self.id,
                                     branch="feat/demo", commit=SHA)

    def work(self, **kwargs):
        return offline_worker.work_once(self.queue, self.logs, self.tasks, self.out,
                                        worker_id="localworker", lease_seconds=60, **kwargs)

    def test_submit_persists_hash_and_checkpoint_without_executing(self):
        state = self.submit()
        self.assertEqual(state["status"], "queued")
        self.assertEqual(checkpoint.read(self.logs, self.id)["status"], "prepared")
        self.assertFalse(state["execution_authorized"])
        self.assertEqual(self.queue.read(self.id)["attempts"], 0)

    def test_worker_executes_existing_offline_pilot_once_for_human_review(self):
        self.submit()
        with patch.object(project, "run", return_value=(self.out / "synthetic-run", "awaiting_human_review")) as mocked:
            result = self.work()
        mocked.assert_called_once()
        self.assertEqual(result["status"], "awaiting_human_review")
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(self.queue.read(self.id)["status"], "awaiting_human_review")
        self.assertEqual(checkpoint.read(self.logs, self.id)["status"], "awaiting_human_review")
        self.assertIsNone(self.work())

    def test_task_changed_after_enqueuing_is_blocked_pre_execution(self):
        self.submit()
        self.task["description"] = "Edited after original hash"
        self.write_task()
        with patch.object(project, "run") as runner:
            result = self.work()
        runner.assert_not_called()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(self.queue.read(self.id)["status"], "blocked")
        self.assertEqual(checkpoint.read(self.logs, self.id)["status"], "blocked")

    def test_missing_task_file_is_blocked_pre_execution(self):
        self.submit()
        self.path.unlink()
        with patch.object(project, "run") as runner:
            result = self.work()
        runner.assert_not_called()
        self.assertEqual(result["status"], "blocked")

    def test_duplicate_submission_denied(self):
        self.submit()
        with self.assertRaises((ValueError, FileExistsError)):
            self.submit()
        self.assertEqual(self.queue.read(self.id)["attempts"], 0)

    def test_checkpoint_fingerprint_mismatch_is_blocked(self):
        self.submit()
        checkpoint.record(self.logs, self.id, event="checkpoint", commit="b"*40)
        with patch.object(project, "run") as runner:
            result = self.work()
        runner.assert_not_called()
        self.assertEqual(result["status"], "blocked")

    def test_non_synthetic_and_bad_duplicate_json_are_rejected_on_submit(self):
        self.task["data_classification"] = "private"
        self.write_task()
        with self.assertRaises(ValueError):
            self.submit()
        self.assertFalse(self.logs.exists())
        self.path.write_text('{"id":"one","id":"two"}')
        with self.assertRaises(ValueError):
            self.submit()

    def test_broken_or_poisoned_journal_blocks_run(self):
        self.submit()
        self.journal_path = self.logs / f"{self.id}.jsonl"
        self.journal_path.write_text(self.journal_path.read_text().replace("feat/demo", "evil"))
        with patch.object(project, "run") as runner:
            result = self.work()
        runner.assert_not_called()
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(self.queue.read(self.id)["status"], "blocked")

    def test_worker_result_failed_is_blocked(self):
        self.submit()
        with patch.object(project, "run", return_value=(self.out / "synthetic-run", "failed")):
            result = self.work()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(self.queue.read(self.id)["status"], "blocked")

    def test_crash_during_project_execution_never_auto_replays(self):
        self.submit()
        with patch.object(project, "run", side_effect=KeyboardInterrupt()):
            with self.assertRaises(KeyboardInterrupt):
                self.work()
        self.assertEqual(self.queue.read(self.id)["status"], "leased")
        self.assertEqual(self.queue.recover_expired(now=10**12), 1)
        self.assertEqual(self.queue.read(self.id)["status"], "needs_review")
        with patch.object(project, "run") as runner:
            self.assertIsNone(self.work())
        runner.assert_not_called()

    def test_crash_after_project_started_requires_manual_review_not_terminal_block(self):
        self.submit()
        with patch.object(project, "run", side_effect=RuntimeError("simulated crash after artifact write")) as runner:
            result = self.work()
        runner.assert_called_once()
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(self.queue.read(self.id)["status"], "leased")
        self.assertEqual(checkpoint.read(self.logs, self.id)["status"], "checkpointed")
        self.assertEqual(self.queue.recover_expired(now=10**12), 1)
        self.assertEqual(self.queue.read(self.id)["status"], "needs_review")
        with patch.object(project, "run") as no_replay:
            self.assertIsNone(self.work())
        no_replay.assert_not_called()

    def test_failed_review_journal_write_after_execution_preserves_uncertain_state(self):
        self.submit()
        original_record = checkpoint.record

        def journal_fault(*args, **kwargs):
            if kwargs.get("event") == "review_requested":
                raise OSError("simulated full disk after project produced artifacts")
            return original_record(*args, **kwargs)

        with patch.object(project, "run", return_value=(self.out / "candidate", "awaiting_human_review")) as runner:
            with patch.object(checkpoint, "record", side_effect=journal_fault):
                result = self.work()
        runner.assert_called_once()
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(self.queue.read(self.id)["status"], "leased")
        self.assertEqual(checkpoint.read(self.logs, self.id)["status"], "checkpointed")
        self.assertEqual(self.queue.recover_expired(now=10**12), 1)
        with patch.object(project, "run") as no_replay:
            self.assertIsNone(self.work())
        no_replay.assert_not_called()

    def test_failed_queue_finish_after_review_record_requires_reconciliation(self):
        self.submit()
        with patch.object(project, "run", return_value=(self.out / "candidate", "awaiting_human_review")) as runner:
            with patch.object(self.queue, "finish", side_effect=OSError("simulated sqlite commit fault")) as finish:
                result = self.work()
        runner.assert_called_once()
        finish.assert_called_once()
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(checkpoint.read(self.logs, self.id)["status"], "awaiting_human_review")
        self.assertEqual(self.queue.read(self.id)["status"], "leased")
        self.assertEqual(self.queue.recover_expired(now=10**12), 1)
        with patch.object(project, "run") as no_replay:
            self.assertIsNone(self.work())
        no_replay.assert_not_called()

    def test_reconciliation_flags_cross_store_divergence_without_unsafe_replay(self):
        self.submit()
        with patch.object(project, "run", return_value=(self.out / "candidate", "awaiting_human_review")):
            with patch.object(self.queue, "finish", side_effect=OSError("simulated lost queue commit")):
                result = self.work()
        self.assertEqual(result["status"], "needs_review")
        report = reconcile.scan(self.queue.path, self.logs, task_dir=self.tasks)
        self.assertTrue(report["needs_attention"])
        self.assertFalse(report["safe_to_auto_retry"])
        self.assertFalse(report["execution_authorized"])
        self.assertEqual(report["conditions"], {"journal_ahead_of_queue": 1})

        self.assertEqual(self.queue.recover_expired(now=10**12), 1)
        quarantined = reconcile.scan(self.queue.path, self.logs, task_dir=self.tasks)
        self.assertTrue(quarantined["needs_attention"])
        self.assertEqual(quarantined["conditions"], {"manual_review_required": 1})
        with patch.object(project, "run") as no_replay:
            self.assertIsNone(self.work())
        no_replay.assert_not_called()

    def test_clean_run_with_real_sandbox(self):
        if not project.supported_host() and os.getenv("CODEN_REQUIRE_SANDBOX") != "1":
            self.skipTest("requires pinned Linux sandbox")
        self.submit()
        result = self.work()
        self.assertEqual(result["status"], "awaiting_human_review")
        self.assertTrue((result["directory"] / "review.json").exists())
        self.assertFalse(result["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
