"""Supervisor is a bounded *operator-invoked* wrapper, never a service."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from ai_factory import durable_queue
from ai_factory import worker_supervisor


class WorkerSupervisorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root / "operator" / "tasks.sqlite3"
        self.journal = self.root / "operator" / "journals"
        self.journal.mkdir(parents=True)
        self.tasks = self.root / "tasks"
        self.tasks.mkdir()
        self.outputs = self.root / "outputs"
        self.outputs.mkdir()
        durable_queue.DurableQueue(self.db)

    def invoke(self, **kwargs):
        params = dict(queue_db=self.db, journal=self.journal, task_dir=self.tasks,
                      output_root=self.outputs, worker_id="operator_01",
                      timeout_seconds=5, lease_seconds=30)
        params.update(kwargs)
        return worker_supervisor.run_once(**params)

    def test_no_tasks_returns_idle_without_any_authorization(self):
        result = self.invoke()
        self.assertEqual(result["status"], "idle")
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["automatic_retry_allowed"])

    def test_invalid_deadlines_rejected_before_spawning(self):
        for timeout, lease in ((0, 30), (-1, 30), (5, 5), (5, 10), (901, 1000), (5, 3601)):
            with self.subTest(timeout=timeout, lease=lease):
                with patch.object(worker_supervisor.subprocess, "Popen") as proc, self.assertRaises(ValueError):
                    self.invoke(timeout_seconds=timeout, lease_seconds=lease)
                proc.assert_not_called()

    def test_untrusted_workspace_and_output_paths_are_rejected(self):
        symlink = self.root / "tasklink"
        symlink.symlink_to(self.tasks)
        with patch.object(worker_supervisor.subprocess, "Popen") as proc:
            with self.assertRaises(ValueError):
                self.invoke(task_dir=symlink)
            with self.assertRaises(ValueError):
                self.invoke(output_root=self.root / "missing")
            proc.assert_not_called()

    def test_environment_does_not_expose_model_credentials(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "dont-share",
                                    "ANTHROPIC_API_KEY": "dont-share",
                                    "SECRET_PASSWORD": "dont-share"}):
            result = self.invoke()
        self.assertEqual(result["status"], "idle")

    def test_worker_does_not_auto_retry_a_failed_task(self):
        self.assertFalse(self.invoke()["automatic_retry_allowed"])
        self.assertFalse(worker_supervisor.RETRY_ENABLED)

    def test_timeout_terminates_entire_session_and_never_auto_requeues(self):
        process = MagicMock()
        process.pid = 424242
        process.communicate.side_effect = subprocess.TimeoutExpired(cmd="worker", timeout=5)
        process.wait.return_value = 0
        with patch.object(worker_supervisor.subprocess, "Popen", return_value=process) as popen:
            with patch.object(worker_supervisor.os, "killpg") as killpg:
                outcome = self.invoke()
        killpg.assert_called_once()
        self.assertEqual(killpg.call_args.args[0], 424242)
        self.assertEqual(outcome["status"], "timed_out_review_required")
        self.assertFalse(outcome["automatic_retry_allowed"])
        self.assertFalse(outcome["execution_authorized"])
        self.assertEqual(popen.call_args.kwargs["start_new_session"], True)

    def test_communication_failure_terminates_child_process_group(self):
        process = MagicMock()
        process.pid = 424243
        process.communicate.side_effect = OSError("simulated broken pipe with worker still running")
        process.wait.return_value = -9
        with patch.object(worker_supervisor.subprocess, "Popen", return_value=process):
            with patch.object(worker_supervisor.os, "killpg") as killpg:
                with self.assertRaises(worker_supervisor.SupervisorError):
                    self.invoke()
        killpg.assert_called_once_with(424243, worker_supervisor.signal.SIGKILL)
        process.wait.assert_called_once_with(timeout=5)

    def test_exit_nonzero_requires_review_without_raw_stderr(self):
        process = MagicMock()
        process.pid = 12121
        process.communicate.return_value = (None, None)
        process.returncode = 2
        with patch.object(worker_supervisor.subprocess, "Popen", return_value=process):
            result = self.invoke()
        self.assertEqual(result["status"], "worker_failed_review_required")
        self.assertNotIn("secret", json.dumps(result))

    def test_redacts_environment_passed_to_child(self):
        process = MagicMock()
        process.pid = 12122
        process.returncode = 0
        process.communicate.return_value = (None, None)
        with patch.dict(os.environ, {"OPENAI_API_KEY":"secret",
                                    "CODEX_AUTH_TOKEN":"secret",
                                    "PYTHONPATH":"/tmp/untrusted",
                                    "PATH":os.environ.get("PATH", "/usr/bin")}):
            with patch.object(worker_supervisor.subprocess, "Popen", return_value=process) as popen:
                self.invoke()
        env = popen.call_args.kwargs["env"]
        self.assertNotIn("OPENAI_API_KEY", env)
        self.assertNotIn("CODEX_AUTH_TOKEN", env)
        self.assertNotEqual(env["PYTHONPATH"], "/tmp/untrusted")
        self.assertNotIn("shell", popen.call_args.kwargs)
        self.assertEqual(popen.call_args.kwargs["start_new_session"], True)

    def test_failure_to_launch_reports_safe_error_not_raw_exception(self):
        with patch.object(worker_supervisor.subprocess, "Popen", side_effect=OSError("secret")), self.assertRaises(worker_supervisor.SupervisorError):
            self.invoke()

    def _fake_worker_response(self, raw_response):
        process = MagicMock()
        process.pid = 12346
        process.returncode = 0
        process.communicate.return_value = (None, None)

        def spawn(_cmd, **kwargs):
            kwargs["stdout"].write(raw_response)
            return process

        with patch.object(worker_supervisor.subprocess, "Popen", side_effect=spawn):
            return self.invoke()

    def test_child_result_malformed_metadata_fails_closed(self):
        # The child output is a low-trust IPC boundary. A status is not
        # sufficient evidence of a completed or authorized task.
        malformed = (
            b'{"status":"awaiting_human_review","execution_authorized":false}',
            b'{"task_id":"SIM_1","status":"awaiting_human_review",'
            b'"execution_authorized":false,"approved":true}',
            b'{"task_id":"SIM_1","status":[],"execution_authorized":false}',
            b'{"task_id":"SIM_1","status":"blocked",'
            b'"status":"awaiting_human_review","execution_authorized":false}',
            b'{"task_id":"../escape","status":"awaiting_human_review",'
            b'"execution_authorized":false}',
        )
        for payload in malformed:
            with self.subTest(payload=payload):
                result = self._fake_worker_response(payload)
                self.assertEqual(result["status"], "untrusted_worker_result")
                self.assertFalse(result["execution_authorized"])

    def test_child_result_accepts_exact_synthetic_metadata_only(self):
        result = self._fake_worker_response(
            b'{"task_id":"SIM_1","status":"awaiting_human_review",'
            b'"execution_authorized":false}'
        )
        self.assertEqual(result["status"], "awaiting_human_review")
        self.assertFalse(result["automatic_retry_allowed"])

    def test_cli_only_supports_operator_one_shot_and_no_daemon(self):
        parser = worker_supervisor.make_parser()
        args = parser.parse_args(["--queue-db", str(self.db),
                                  "--journal", str(self.journal),
                                  "--task-dir", str(self.tasks),
                                  "--output-root", str(self.outputs), "work-once"])
        self.assertEqual(args.command, "work-once")
        with self.assertRaises(SystemExit):
            parser.parse_args(["--queue-db", str(self.db),
                               "--journal", str(self.journal),
                               "--task-dir", str(self.tasks),
                               "--output-root", str(self.outputs), "serve-forever"])


if __name__ == "__main__":
    unittest.main()
