"""End-to-end, offline, synthetic-only queue → checkpoint → project worker tests."""
import hashlib
import json
import os
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

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

    def test_submit_rejects_symlinked_task_directory_ancestor(self):
        alias = self.root / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises((OSError, ValueError)):
            offline_worker.submit(self.queue, self.logs, alias / "tasks",
                                  self.id, branch="feat/demo", commit=SHA)
        self.assertFalse(self.logs.exists())
        with self.assertRaises(ValueError):
            self.queue.read(self.id)

    def test_worker_blocks_linked_ancestor_even_with_matching_task_bytes(self):
        self.submit()
        alias = self.root / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with patch.object(project, "run") as runner:
            result = offline_worker.work_once(
                self.queue, self.logs, alias / "tasks", self.out,
                worker_id="localworker", lease_seconds=60)
        runner.assert_not_called()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(self.queue.read(self.id)["status"], "blocked")
        self.assertEqual(checkpoint.read(self.logs, self.id)["status"], "blocked")

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


class LeasedModeBFixtureTests(unittest.TestCase):
    task_id = "OPENHANDS_SYNTHETIC_1"
    task_path = Path("ai_factory/examples/openhands-multifile-task.json")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.checkout = root / "checkout"
        self.checkout.mkdir()
        self.git("init", "-b", "review/fixture")
        self.path = self.checkout / self.task_path
        self.path.parent.mkdir(parents=True)
        self.raw = (Path(offline_worker.__file__).resolve().parents[1] / self.task_path).read_bytes()
        self.path.write_bytes(self.raw)
        self.git("add", "--", str(self.task_path))
        self.git("-c", "user.name=Fixture", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-m", "synthetic fixture")
        self.commit = self.git("rev-parse", "HEAD")
        self.queue = durable_queue.DurableQueue(root / "queue.db")
        self.adapter = Mock()
        self.adapter.execute.side_effect = self.acknowledge
        self.adapter.close.return_value = {"fixture_cleanup": True}

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.checkout,
                                       stderr=subprocess.DEVNULL, text=True).strip()

    def acknowledge(self, request):
        return {"status": "fixture_completed", "task_sha256": request["task_sha256"],
                "request_sha256": hashlib.sha256(project.encoded(request).encode()).hexdigest()}

    def enqueue(self, *, branch="review/fixture", commit=None, raw=None):
        digest = hashlib.sha256(self.raw if raw is None else raw).hexdigest()
        self.queue.enqueue(self.task_id, branch, commit or self.commit, digest)

    def work(self, **kwargs):
        return offline_worker.work_modeb_fixture_once(
            self.queue, self.checkout, worker_id="synthetic_worker",
            fixture_adapter=self.adapter, **kwargs)

    def test_verified_task_is_claimed_once_and_receipt_matches_adapter_request(self):
        self.enqueue()
        receipt = self.work()
        self.assertEqual(receipt["status"], "fixture_completed_review_required")
        self.assertTrue(receipt["lease_claimed"])
        self.assertTrue(receipt["source_checkout_verified"])
        request, = self.adapter.execute.call_args.args
        self.assertEqual(request["source_identity"]["commit"], self.commit)
        self.assertEqual(receipt["request_sha256"], self.acknowledge(request)["request_sha256"])
        self.assertFalse(receipt["qwen_connected"])
        self.assertFalse(receipt["release_authorized"])
        self.queue = durable_queue.DurableQueue(self.queue.path)
        self.assertIsNone(self.work())
        self.assertEqual(self.queue.read(self.task_id)["attempts"], 1)
        self.assertEqual(self.queue.read(self.task_id)["status"], "awaiting_human_review")
        self.adapter.execute.assert_called_once()
        self.adapter.close.assert_called_once()

    def test_second_worker_cannot_dispatch_while_first_adapter_is_active(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event

        self.enqueue()
        entered, resume = Event(), Event()
        def pause_then_reply(request):
            entered.set()
            if not resume.wait(5):
                raise TimeoutError()
            return self.acknowledge(request)

        self.adapter.execute.side_effect = pause_then_reply
        with ThreadPoolExecutor(max_workers=1) as executor:
            running = executor.submit(self.work)
            try:
                self.assertTrue(entered.wait(5))
                self.assertIsNone(self.work())
            finally:
                resume.set()
            self.assertEqual(running.result()["status"], "fixture_completed_review_required")
        self.adapter.execute.assert_called_once()

    def assert_blocked_before_dispatch(self):
        self.assertEqual(self.work()["status"], "blocked")
        self.assertEqual(self.queue.read(self.task_id)["status"], "blocked")
        self.adapter.execute.assert_not_called()

    def test_rejects_different_checked_out_branch_at_same_commit(self):
        self.enqueue()
        self.git("switch", "-c", "review/other")
        self.assert_blocked_before_dispatch()

    def test_rejects_wrong_commit(self):
        self.enqueue(commit="a"*40)
        self.assert_blocked_before_dispatch()

    def test_rejects_modified_file_even_if_queue_hash_matches_modified_bytes(self):
        self.path.write_bytes(self.raw + b" ")
        self.enqueue(raw=self.path.read_bytes())
        self.assert_blocked_before_dispatch()

    def test_rejects_wrong_queue_digest_with_clean_git_file(self):
        self.enqueue(raw=b"other")
        self.assert_blocked_before_dispatch()

    def test_rejects_symlink_to_file_with_same_bytes(self):
        self.enqueue()
        copy = self.checkout / "copy.json"
        self.path.rename(copy)
        self.path.symlink_to(copy)
        self.assert_blocked_before_dispatch()

    def test_committed_unapproved_task_is_blocked_before_dispatch(self):
        task = json.loads(self.raw)
        task["description"] = "Unapproved replacement intent"
        raw = json.dumps(task).encode()
        self.path.write_bytes(raw)
        self.git("add", "--", str(self.task_path))
        self.git("-c", "user.name=Fixture", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-m", "changed intent")
        self.enqueue(commit=self.git("rev-parse", "HEAD"), raw=raw)
        self.assert_blocked_before_dispatch()
        self.adapter.close.assert_not_called()

    def test_committed_deeply_nested_json_is_blocked_before_dispatch(self):
        raw = b"[" * 10000 + b"0" + b"]" * 10000
        self.path.write_bytes(raw)
        self.git("add", "--", str(self.task_path))
        self.git("-c", "user.name=Fixture", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-m", "nested JSON")
        self.enqueue(commit=self.git("rev-parse", "HEAD"), raw=raw)
        self.assert_blocked_before_dispatch()
        self.adapter.close.assert_not_called()

    def test_cancel_during_fixture_quarantines_without_replay(self):
        self.enqueue()
        def cancel_then_reply(request):
            self.queue.request_cancel(self.task_id)
            return self.acknowledge(request)
        self.adapter.execute.side_effect = cancel_then_reply
        self.assertEqual(self.work()["status"], "needs_review")
        self.assertEqual(self.queue.read(self.task_id)["status"], "cancel_requested")
        self.assertEqual(self.queue.recover_expired(now=10**12), 1)
        self.assertIsNone(self.work())
        self.adapter.execute.assert_called_once()

    def test_bad_receipt_requires_review_after_lease_expiry(self):
        self.enqueue()
        self.adapter.execute.side_effect = None
        self.adapter.execute.return_value = {}
        self.assertEqual(self.work()["status"], "needs_review")
        self.assertEqual(self.queue.recover_expired(now=10**12), 1)
        self.assertIsNone(self.work())
        self.assertEqual(self.queue.read(self.task_id)["status"], "needs_review")


if __name__ == "__main__":
    unittest.main()
