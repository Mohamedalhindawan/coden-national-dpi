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


    def _integrated_broker_fixture(self, *, wrong_peer=False, cancel=False):
        """Actual local socket framing + durable queue; no SDK/model calls."""
        import socket
        import struct
        import threading
        from ai_factory import factory_qwen_tool_benchmark as bench

        if not hasattr(socket, "SO_PEERCRED"):
            self.skipTest("Linux peer credentials required")
        token = b"synthetic-integration-grant"
        broker = bench.PreflightBroker(token_sha256=hashlib.sha256(token).hexdigest(),
                                       case_id="count")
        client, peer = socket.socketpair()
        self.addCleanup(client.close)
        self.addCleanup(peer.close)
        identity = (os.getpid() + int(wrong_peer), os.getuid(), os.getgid())
        peer.settimeout(2)
        evidence, requests, errors = [], [], []

        def exact(stream, size):
            raw = bytearray()
            while len(raw) < size:
                block = stream.recv(size - len(raw))
                if not block:
                    raise EOFError("incomplete fixture frame")
                raw.extend(block)
            return bytes(raw)

        def server():
            try:
                with peer:
                    if wrong_peer:
                        self.assertEqual(peer.recv(1), b"")
                        return
                    size = struct.unpack("!I", exact(peer, 4))[0]
                    self.assertTrue(0 < size <= 16384)
                    requests.append(json.loads(exact(peer, size)))
                    self.assertEqual(peer.recv(1), b"")
                    case = bench.CASES["count"]
                    raw = json.dumps({"model": "local-qwen",
                        "choices": [{"finish_reason": "tool_calls", "message": {
                            "role": "assistant", "content": None, "tool_calls": [{
                                "id": "call_fixture", "type": "function", "function": {
                                    "name": case["expected_tool"],
                                    "arguments": json.dumps(case["expected_args"])}}]}}],
                        "usage": {"completion_tokens": 22}}).encode()
                    peer.sendall(struct.pack("!HI", 200, len(raw)) + raw)
            except Exception as exc:
                errors.append(type(exc).__name__)

        worker = self

        class Adapter:
            def execute(self, request):
                worker.assertEqual(request["source_identity"]["commit"], worker.commit)
                worker.assertEqual(request["allowed_files"],
                                   ["README.md", "app/logic.py", "tests/test_logic.py"])
                worker.assertFalse(request["external_network_allowed"])
                worker.assertFalse(request["release_authorized"])
                result = broker.execute_ipc(token=token, channel=client,
                    expected_peer=identity, fixture_only=True, deadline_seconds=2)
                evidence.append(result)
                if result["status"] != "fixture_preflight_match":
                    raise ValueError("broker fixture rejected")
                if cancel:
                    worker.queue.request_cancel(worker.task_id)
                return worker.acknowledge(request)

            def close(self):
                closed = client.fileno() == -1
                client.close()
                return {"fixture_cleanup": closed}

        self.adapter = Adapter()
        thread = threading.Thread(target=server, daemon=True)
        thread.start()
        try:
            self.enqueue()
            result = self.work()
        finally:
            client.close()
            thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(len(evidence), 1)
        self.assertFalse(evidence[0]["qwen_connected"])
        self.assertFalse(evidence[0]["tool_executed"])
        self.assertFalse(result["release_authorized"])
        self.assertEqual(requests, [] if wrong_peer else [bench.request_for("count")])
        self.assertEqual(client.fileno(), -1)
        if wrong_peer or cancel:
            self.assertEqual(result["status"], "needs_review")
            self.assertEqual(self.queue.recover_expired(now=10**12), 1)
            self.assertEqual(self.queue.read(self.task_id)["status"], "needs_review")
        else:
            self.assertEqual(result["status"], "fixture_completed_review_required")
            self.assertEqual(self.queue.read(self.task_id)["status"], "awaiting_human_review")
        self.assertEqual(evidence[0]["status"],
                         "fixture_peer_rejected" if wrong_peer else "fixture_preflight_match")
        self.assertIsNone(self.work())
        self.assertEqual(self.queue.read(self.task_id)["attempts"], 1)

    def test_integrated_queue_bridge_broker_and_review_only_skill(self):
        from ai_factory import factory_skill_catalog, factory_84_registry
        rows = factory_84_registry.load_v1_1()
        self.assertEqual(len(rows), 128)
        self.assertTrue(all(not row["enabled"] for row in rows))
        skill = factory_skill_catalog.choose("multifile")
        source = Path(offline_worker.__file__).resolve().parents[1] / skill["skill_path"]
        workspace = Path(self.tmp.name) / "skill-review"
        workspace.mkdir(mode=0o700)
        staged = factory_skill_catalog.stage_reviewed(
            "multifile", workspace, hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertFalse(staged["execution_authorized"])
        self.assertFalse(staged["runtime_invoked"])
        self._integrated_broker_fixture()

    def test_integrated_broker_wrong_peer_quarantines_worker(self):
        self._integrated_broker_fixture(wrong_peer=True)

    def test_integrated_broker_success_then_cancel_quarantines_worker(self):
        self._integrated_broker_fixture(cancel=True)


    def _journal_fixture(self, *, wrong_identity=False, missing=False):
        self.enqueue()
        journal = Path(self.tmp.name) / "journal"
        journal.mkdir()
        if not missing:
            checkpoint.create(journal, self.task_id, branch="review/fixture",
                              commit="a"*40 if wrong_identity else self.commit)
        tasks = Path(self.tmp.name) / "diagnostic-tasks"
        tasks.mkdir()
        (tasks / (self.task_id + ".json")).write_bytes(self.raw)
        return journal, tasks

    def test_modeb_journal_and_health_consistent_after_fixture_success(self):
        from ai_factory import queue_health
        journal, tasks = self._journal_fixture()
        self.assertEqual(queue_health.snapshot(self.queue.path, journal, tasks)["queue_depth"], 1)
        receipt = self.work(checkpoint_root=journal)
        self.assertEqual(receipt["status"], "fixture_completed_review_required")
        self.assertTrue(receipt["journal_linked"])
        self.assertFalse(receipt["release_authorized"])
        state = checkpoint.read(journal, self.task_id)
        self.assertEqual(state["status"], "awaiting_human_review")
        self.assertEqual(state["event_count"], 3)
        health = queue_health.snapshot(self.queue.path, journal, tasks)
        self.assertEqual(health["conditions"], {"consistent_review": 1})
        self.assertEqual(health["awaiting_human_review"], 1)
        self.assertFalse(health["execution_authorized"])
        self.assertIsNone(self.work(checkpoint_root=journal))
        self.adapter.execute.assert_called_once()

    def test_modeb_missing_or_mismatched_journal_never_dispatches(self):
        journal, tasks = self._journal_fixture(wrong_identity=True)
        receipt = self.work(checkpoint_root=journal)
        self.assertEqual(receipt["status"], "needs_review")
        self.assertFalse(receipt["journal_linked"])
        self.adapter.execute.assert_not_called()
        self.adapter.close.assert_not_called()
        self.assertEqual(self.queue.recover_expired(now=10**12), 1)
        self.assertIsNone(self.work(checkpoint_root=journal))
        self.assertEqual(reconcile.scan(self.queue.path, journal, tasks)["conditions"],
                         {"identity_mismatch": 1})

    def test_modeb_failed_journal_write_after_dispatch_preserves_lease(self):
        journal, tasks = self._journal_fixture()
        record = checkpoint.record
        def fail_review(*args, **kwargs):
            if kwargs.get("event") == "review_requested":
                raise OSError("synthetic journal write failure")
            return record(*args, **kwargs)
        with patch.object(checkpoint, "record", side_effect=fail_review):
            receipt = self.work(checkpoint_root=journal)
        self.assertEqual(receipt["status"], "needs_review")
        self.assertEqual(checkpoint.read(journal, self.task_id)["status"], "checkpointed")
        self.assertEqual(self.queue.read(self.task_id)["status"], "leased")
        self.assertEqual(self.queue.recover_expired(now=10**12), 1)
        self.assertEqual(reconcile.scan(self.queue.path, journal, tasks)["conditions"],
                         {"manual_review_required": 1})
        self.assertIsNone(self.work(checkpoint_root=journal))
        self.adapter.execute.assert_called_once()

    def test_modeb_cancel_retains_journal_and_requires_manual_reconciliation(self):
        from ai_factory import queue_health
        journal, tasks = self._journal_fixture()
        def cancel_then_reply(request):
            self.queue.request_cancel(self.task_id)
            return self.acknowledge(request)
        self.adapter.execute.side_effect = cancel_then_reply
        receipt = self.work(checkpoint_root=journal)
        self.assertEqual(receipt["status"], "needs_review")
        self.assertEqual(checkpoint.read(journal, self.task_id)["status"], "checkpointed")
        health = queue_health.snapshot(self.queue.path, journal, tasks)
        self.assertEqual(health["conditions"], {"cancel_stop_reconciliation_required": 1})
        self.assertTrue(health["needs_attention"])
        self.assertEqual(self.queue.recover_expired(now=10**12), 1)
        self.assertIsNone(self.work(checkpoint_root=journal))
        self.adapter.execute.assert_called_once()


    def _run_bound_metadata_fixture(self, *, tamper=False):
        from ai_factory import runtime_contract, queue_health
        journal, tasks = self._journal_fixture()
        assessments = []

        def review_metadata_then_acknowledge(adapter_request):
            # Test-local adapter only. The report explicitly says the
            # real runtime is blocked; no inference or artifact is claimed.
            request = {
                "schema": runtime_contract.REQ_SCHEMA,
                "task_id": adapter_request["task_id"],
                "task_sha256": adapter_request["task_sha256"],
                "classification": "synthetic",
                "required_capabilities": ["coding", "tool_calls"],
                "allowed_providers": ["local_qwen"],
                "allow_external_api": False,
                "max_tokens_total": 2048,
                "max_duration_seconds": adapter_request["limits"]["seconds"],
                "max_cost_usd": "0",
            }
            digest = hashlib.sha256(json.dumps(request, sort_keys=True,
                separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()
            evidence = {
                "schema": "coden.runtime.bound_report.v1",
                "request_sha256": "0"*64 if tamper else digest,
                "task_id": request["task_id"], "provider_id": "local_qwen",
                "model_id": "local-qwen", "transport": "local",
                "status": "blocked", "error_code": "policy_denied",
                "artifact_sha256": None, "input_tokens": 0, "output_tokens": 0,
                "duration_ms": 0, "cost_usd": "0",
            }
            assessed = runtime_contract.assess_bound_local_json(
                request, json.dumps(evidence).encode("utf-8"),
                expected_model_id="local-qwen")
            assessments.append(assessed)
            return self.acknowledge(adapter_request)

        self.adapter.execute.side_effect = review_metadata_then_acknowledge
        receipt = self.work(checkpoint_root=journal)
        self.assertFalse(receipt["release_authorized"])
        self.assertFalse(receipt["automatic_retry_allowed"])
        self.adapter.execute.assert_called_once()
        self.adapter.close.assert_called_once()
        if tamper:
            self.assertEqual(assessments, [])
            self.assertEqual(receipt["status"], "needs_review")
            self.assertEqual(self.queue.recover_expired(now=10**12), 1)
            self.assertEqual(self.queue.read(self.task_id)["status"], "needs_review")
        else:
            self.assertEqual(len(assessments), 1)
            self.assertEqual(assessments[0]["status"], "blocked")
            self.assertFalse(assessments[0]["execution_authorized"])
            self.assertFalse(assessments[0]["artifact_verified"])
            self.assertEqual(receipt["status"], "fixture_completed_review_required")
            self.assertFalse(receipt["qwen_connected"])
        health = queue_health.snapshot(self.queue.path, journal, tasks)
        self.assertTrue(health["snapshot_task_states_consistent"])
        self.assertEqual(health["conditions"],
            {"manual_review_required": 1} if tamper else {"consistent_review": 1})
        self.assertIsNone(self.work(checkpoint_root=journal))
        self.assertEqual(self.queue.read(self.task_id)["attempts"], 1)

    def test_bound_runtime_metadata_fixture_integrates_with_worker_and_health(self):
        self._run_bound_metadata_fixture()

    def test_bound_runtime_metadata_tamper_quarantines_without_retry(self):
        self._run_bound_metadata_fixture(tamper=True)


if __name__ == "__main__":
    unittest.main()
