"""Operator CLI is opt-in; no agent starts from a dry-run command."""
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from ai_factory import openhands_sdk_operator


class OpenHandsManagedCLITests(unittest.TestCase):
    def test_no_flag_does_not_read_files_or_import_sdk(self):
        args = [
            sys.executable, "-m", "ai_factory.openhands_sdk_operator",
            "--task", "/path/that/does/not/exist.json",
            "--candidate-dir", "/missing/export",
            "--output-root", "/missing/output",
            "--model", "ollama/qwen2.5-coder:1.5b",
            "--server-image", "ghcr.io/openhands/agent-server@sha256:"+"a"*64,
            "--network", "coden_internal",
        ]
        result = subprocess.run(args, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        outcome = json.loads(result.stdout)
        self.assertEqual(outcome["status"], "disabled")
        self.assertFalse(outcome["agent_session_attempted"])
        self.assertFalse(outcome["execution_authorized"])
        self.assertEqual(result.stderr, "")

    def test_opt_in_with_missing_task_returns_sanitized_failure(self):
        args = [
            sys.executable, "-m", "ai_factory.openhands_sdk_operator",
            "--task", "/missing/task.json",
            "--candidate-dir", "/missing/export",
            "--output-root", "/missing/output",
            "--model", "ollama/qwen2.5-coder:1.5b",
            "--server-image", "ghcr.io/openhands/agent-server@sha256:"+"a"*64,
            "--network", "coden_internal",
            "--allow-agent",
        ]
        result = subprocess.run(args, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        outcome = json.loads(result.stdout)
        self.assertEqual(outcome["status"], "invalid_config")
        self.assertFalse(outcome["automatic_retry_allowed"])
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_read_only_cli_preflight_never_starts_sdk(self):
        import tempfile
        from ai_factory import project
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            export = root / "export"
            export.mkdir()
            output = root / "output"
            output.mkdir()
            task_file = project.EXAMPLE
            argv = [
                "--task", str(task_file),
                "--candidate-dir", str(export),
                "--output-root", str(output),
                "--model", "ollama/qwen2.5-coder:1.5b",
                "--server-image", "ghcr.io/openhands/agent-server@sha256:" + "a" * 64,
                "--network", "coden_internal",
                "--preflight-only",
            ]
            with patch.object(openhands_sdk_operator, "launch_isolated",
                              return_value={"status": "preflight_passed",
                                            "agent_session_attempted": False,
                                            "execution_authorized": False,
                                            "release_authorized": False,
                                            "automatic_retry_allowed": False}) as gate:
                with patch("builtins.print") as printed:
                    code = openhands_sdk_operator.main(argv)
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(printed.call_args.args[0])["status"], "preflight_passed")
            self.assertTrue(gate.call_args.kwargs["preflight_only"])
            self.assertFalse(gate.call_args.kwargs["allow_agent"])

    def test_docker_inspect_context_is_read_only(self):
        valid = [{"Name": "default", "Endpoints": {"docker": {"Host": "unix:///var/run/docker.sock"}}}]
        with patch.object(openhands_sdk_operator.subprocess, "run",
                          return_value=SimpleNamespace(returncode=0, stdout=json.dumps(valid))) as cmd:
            context = openhands_sdk_operator._inspect_local_docker("context", "current")
        self.assertEqual(context["Name"], "default")
        cmd.assert_called_once()
        self.assertEqual(cmd.call_args.args[0], ["docker", "context", "inspect"])

    def test_docker_inspect_read_only_and_metadata_constrained(self):
        valid = [{"Internal": True, "Driver": "bridge", "Name": "coden_internal"}]
        with patch.object(openhands_sdk_operator.subprocess, "run",
                          return_value=SimpleNamespace(returncode=0, stdout=json.dumps(valid))) as command:
            result = openhands_sdk_operator._inspect_local_docker("network", "coden_internal")
        self.assertTrue(result["Internal"])
        command.assert_called_once()
        args = command.call_args.args[0]
        self.assertEqual(args, ["docker", "network", "inspect", "coden_internal"])
        self.assertNotIn("run", args)
        self.assertNotIn("pull", args)
        for bad in ([], [{}, {}], {"bad": "shape"}):
            with self.subTest(bad=bad):
                with patch.object(openhands_sdk_operator.subprocess, "run",
                                  return_value=SimpleNamespace(returncode=0, stdout=json.dumps(bad))):
                    with self.assertRaises(ValueError):
                        openhands_sdk_operator._inspect_local_docker("network", "coden_internal")


if __name__ == "__main__":
    unittest.main()
