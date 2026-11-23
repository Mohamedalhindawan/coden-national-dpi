"""TDD for supervised STOP of a **specific** operator-owned child process.

A requested cancellation is never an assertion that the entire process tree
ceased; only the group SIGKILL attempt + reaped leader are directly observed.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

from ai_factory import checkpoint, worker_supervisor
from ai_factory.durable_queue import DurableQueue

SHA = "c" * 40
HASH = "f" * 64


class MonitoredSupervisorCancellationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.db = self.root / "operator" / "queue.sqlite3"
        self.journal = self.root / "operator" / "journal"
        self.journal.mkdir(parents=True)
        self.tasks = self.root / "tasks"
        self.tasks.mkdir()
        self.out = self.root / "outputs"
        self.out.mkdir()
        self.q = DurableQueue(self.db)
        self.worker = "operator_1"

    def create(self, name="target"):
        self.q.enqueue(name, "feat/synthetic", SHA, HASH)
        checkpoint.create(self.journal, name, branch="feat/synthetic", commit=SHA)

    def run_target(self, task_id="target", **kwargs):
        args = dict(queue_db=self.db, journal=self.journal,
                    task_dir=self.tasks, output_root=self.out,
                    worker_id=self.worker, task_id=task_id,
                    timeout_seconds=5, lease_seconds=30)
        args.update(kwargs)
        return worker_supervisor.run_once(**args)

    def test_exact_queue_claim_does_not_steal_another_task(self):
        self.create("first")
        self.create("second")
        leased = self.q.claim("worker", task_id="second", now=100, lease_seconds=30)
        self.assertEqual(leased["task_id"], "second")
        self.assertEqual(self.q.read("first")["status"], "queued")
        self.assertIsNone(self.q.claim("other", task_id="second", now=100))
        self.assertEqual(self.q.claim("worker", task_id="first", now=100)["task_id"], "first")

    def test_stale_cancelled_or_unknown_target_cannot_launch_any_child(self):
        self.create()
        self.q.request_cancel("target")
        with patch.object(worker_supervisor.subprocess, "Popen") as start:
            with self.assertRaises(ValueError):
                self.run_target()
            with self.assertRaises(ValueError):
                self.run_target(task_id="unknown")
        start.assert_not_called()
        self.assertEqual(self.q.read("target")["status"], "cancelled")

    def test_target_cli_and_child_command_bind_only_selected_task(self):
        parser = worker_supervisor.make_parser()
        args = parser.parse_args([
            "--queue-db", str(self.db), "--journal", str(self.journal),
            "--task-dir", str(self.tasks), "--output-root", str(self.out),
            "--task-id", "target", "work-once"
        ])
        self.assertEqual(args.task_id, "target")
        self.create("target")
        self.create("other")
        result_json = b'{"task_id":"target","status":"blocked","execution_authorized":false}'
        process = MagicMock()
        process.returncode = 0
        process.wait.return_value = 0
        def begin(cmd, **kwargs):
            self.assertEqual(cmd[-2:], ["--task-id", "target"])
            kwargs["stdout"].write(result_json)
            self.assertTrue(kwargs["start_new_session"])
            return process
        with patch.object(worker_supervisor.subprocess, "Popen", side_effect=begin) as spawner:
            result = self.run_target()
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["automatic_retry_allowed"])
        self.assertEqual(spawner.call_count, 1)
        self.assertEqual(self.q.read("other")["status"], "queued")

    @unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux process-group semantics")
    def test_real_cancel_request_kills_owned_child_group_and_records_uncertainty(self):
        self.create()
        marker = self.root / "synthetic-child.pid"
        fixture = (
            "import os, subprocess, sys, time\n"
            "from ai_factory.durable_queue import DurableQueue\n"
            "queue = DurableQueue(sys.argv[1])\n"
            "lease = queue.claim('fixture_worker',task_id='target',lease_seconds=30)\n"
            "assert lease['task_id'] == 'target'\n"
            "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'], "
            "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n"
            "with open(sys.argv[2],'w',encoding='ascii') as f:\n"
            "    f.write(str(child.pid)); f.flush(); os.fsync(f.fileno())\n"
            "time.sleep(30)\n"
        )
        compile(fixture, "<synthetic-operator-cancel-fixture>", "exec")
        real_popen = subprocess.Popen
        spawned = []
        errors = []
        output = []
        descendant_pid = None

        def launch(cmd, **kwargs):
            self.assertEqual(cmd[-2:], ["--task-id", "target"])
            proc = real_popen([sys.executable, "-c", fixture, str(self.db), str(marker)], **kwargs)
            spawned.append(proc)
            return proc

        def issue_cancel():
            deadline = time.monotonic() + 4
            while not marker.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            if not marker.exists():
                errors.append("fixture never claimed selected task")
                return
            try:
                output.append(self.q.request_cancel("target"))
            except Exception as exc:
                errors.append(type(exc).__name__)

        thread = threading.Thread(target=issue_cancel, daemon=True)
        try:
            thread.start()
            with patch.object(worker_supervisor.subprocess, "Popen", side_effect=launch):
                result = self.run_target()
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
            self.assertFalse(errors, errors)
            self.assertEqual(output[0]["status"], "cancel_requested")
            self.assertEqual(result["status"], "cancel_stop_review_required")
            self.assertTrue(result["owned_process_leader_reaped"])
            self.assertFalse(result["process_tree_absence_verified"])
            self.assertFalse(result["execution_authorized"])
            self.assertFalse(result["automatic_retry_allowed"])
            self.assertEqual(self.q.read("target")["status"], "cancel_requested")
            self.assertEqual(checkpoint.read(self.journal, "target")["status"], "blocked")
            self.assertEqual(checkpoint.read(self.journal, "target")["next_action"], "inspect_cancel_stop")
            self.assertIsNotNone(spawned[0].poll())
            descendant_pid = int(marker.read_text(encoding="ascii"))
            # Process descendants may linger briefly as zombies after SIGKILL.
            def running(pid):
                stat_path = Path("/proc") / str(pid) / "stat"
                if not stat_path.exists():
                    return False
                return stat_path.read_text().split(") ",1)[1][:1] not in ("Z","X")
            for _ in range(20):
                if not running(descendant_pid):
                    break
                time.sleep(0.05)
            self.assertFalse(running(descendant_pid))
            self.assertIsNone(self.q.claim("later_worker"))
        finally:
            thread.join(timeout=1)
            for proc in spawned:
                if proc.poll() is None:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait(timeout=5)
            if descendant_pid is None and marker.is_file():
                descendant_pid = int(marker.read_text(encoding="ascii"))
            if descendant_pid and Path("/proc", str(descendant_pid)).exists():
                try:
                    os.kill(descendant_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_unverifiable_kill_fails_closed_with_lease_still_pending(self):
        self.create()
        process = MagicMock()
        process.pid = 41000
        process.returncode = None

        def wait_side_effect(*args, **kwargs):
            self.q.claim("child", task_id="target", lease_seconds=30)
            self.q.request_cancel("target")
            raise subprocess.TimeoutExpired(cmd="worker", timeout=0.05)

        process.wait.side_effect = wait_side_effect
        with patch.object(worker_supervisor.subprocess, "Popen", return_value=process):
            with patch.object(worker_supervisor, "_terminate_process_group",
                              side_effect=worker_supervisor.SupervisorError("synthetic unverifiable")):
                with self.assertRaises(worker_supervisor.SupervisorError):
                    self.run_target()
        self.assertEqual(self.q.read("target")["status"], "cancel_requested")
        self.assertEqual(checkpoint.read(self.journal, "target")["status"], "prepared")
        self.assertIsNone(self.q.claim("new_worker"))

    def test_no_automatic_recovery_or_approval_even_after_leader_exit(self):
        self.create()
        p = MagicMock()
        p.returncode = 0
        p.wait.return_value = 0
        def begin(_cmd, **kwargs):
            self.q.claim("fixture", task_id="target", lease_seconds=30)
            self.q.request_cancel("target")
            kwargs["stdout"].write(
                b'{"task_id":"target","status":"awaiting_human_review",'
                b'"execution_authorized":false}'
            )
            return p
        with patch.object(worker_supervisor.subprocess, "Popen", side_effect=begin):
            outcome = self.run_target()
        self.assertEqual(outcome["status"], "cancel_stop_review_required")
        self.assertFalse(outcome["execution_authorized"])
        self.assertFalse(outcome["automatic_retry_allowed"])
        self.assertFalse(outcome["process_tree_absence_verified"])
        self.assertEqual(self.q.read("target")["status"], "cancel_requested")
        self.assertEqual(checkpoint.read(self.journal, "target")["next_action"], "inspect_cancel_stop")


if __name__ == "__main__":
    unittest.main()
