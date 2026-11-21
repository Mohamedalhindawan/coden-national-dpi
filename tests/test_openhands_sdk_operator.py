"""Official OpenHands SDK wiring contract: never run a host-local agent in CI."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from ai_factory import openhands_sdk_operator, openhands_multifile_review, project


MODEL = "ollama/qwen2.5-coder:1.5b"
IMAGE = "ghcr.io/openhands/agent-server@sha256:" + "a" * 64


class FakeDockerWorkspace:
    def __init__(self, directory, **changes):
        self.server_image = IMAGE
        self.volumes = [f"{directory}:/workspace/export:rw"]
        self.forward_env = []
        self.network = "coden_internal"
        self.extra_ports = False
        self.enable_gpu = False
        for key, value in changes.items():
            setattr(self, key, value)


class FakeLLM:
    seen = []
    def __init__(self, **kwargs):
        type(self).seen.append(kwargs)


class FakeTool:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class FakeTerminal:
    name = "terminal"


class FakeFileEditor:
    name = "file_editor"


class FakeAgent:
    seen = []
    def __init__(self, **kwargs):
        type(self).seen.append(kwargs)


class FakeConversation:
    seen = []
    export = None
    prompt = None
    closed = False
    fail = False

    def __init__(self, *, agent, workspace):
        self.agent = agent
        self.workspace = workspace
        type(self).seen.append(self)

    def send_message(self, prompt):
        type(self).prompt = prompt

    def run(self):
        if type(self).fail:
            raise RuntimeError("provider raw SECRET failure")
        root = type(self).export
        (root / "app").mkdir()
        (root / "tests").mkdir()
        (root / "app" / "logic.py").write_text(
            "def transform(value):\n    counts = {}\n    for item in value:\n"
            "        counts[item] = counts.get(item, 0) + 1\n    return counts\n"
        )
        (root / "README.md").write_text("# Candidate\n")
        (root / "tests" / "test_logic.py").write_text("def test_sample():\n    assert True\n")

    def close(self):
        self.closed = True


SDK = SimpleNamespace(
    DockerWorkspace=FakeDockerWorkspace,
    LLM=FakeLLM, Agent=FakeAgent, Conversation=FakeConversation,
    Tool=FakeTool, TerminalTool=FakeTerminal, FileEditorTool=FakeFileEditor,
)


class OpenHandsSDKOperatorTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.export = self.root / "export"
        self.export.mkdir()
        self.output = self.root / "output"
        self.output.mkdir()
        self.task = json.loads(project.EXAMPLE.read_text())
        self.task["recipe"] = "python-transform"
        self.task["review_cases"] = [{"input": ["HIDDEN_SECRET_CASE"], "expected": {"HIDDEN_SECRET_CASE": 1}}]
        self.workspace = FakeDockerWorkspace(self.export)
        FakeLLM.seen = []
        FakeAgent.seen = []
        FakeConversation.seen = []
        FakeConversation.prompt = None
        FakeConversation.export = self.export
        FakeConversation.fail = False

    def run_pilot(self, **kwargs):
        params = dict(
            task=self.task, candidate_root=self.export,
            output_root=self.output, workspace=self.workspace,
            model=MODEL, base_url="http://ollama:11434",
            allow_agent=False, sdk=SDK,
        )
        params.update(kwargs)
        return openhands_sdk_operator.run_once(**params)

    def test_disabled_default_does_not_touch_sdk_or_workspace(self):
        result = self.run_pilot()
        self.assertEqual(result["status"], "disabled")
        self.assertFalse(result["agent_session_attempted"])
        self.assertFalse(FakeLLM.seen)
        self.assertFalse(FakeConversation.seen)

    def test_invalid_workspace_security_fields_fail_closed(self):
        invalid = [
            {"volumes": []}, {"volumes": ["/host/secrets:/workspace:rw"]},
            {"server_image": "ghcr.io/openhands/agent-server:latest"},
            {"network": "host"}, {"network": "bridge"},
            {"forward_env": ["OPENAI_API_KEY"]}, {"extra_ports": True},
            {"enable_gpu": True},
        ]
        for item in invalid:
            with self.subTest(item=item):
                ws = FakeDockerWorkspace(self.export, **item)
                with self.assertRaises(ValueError):
                    self.run_pilot(workspace=ws, allow_agent=True)
        self.assertFalse(FakeConversation.seen)

    def test_rejects_nonlocal_model_and_untrusted_tasks(self):
        bad = [{"model": "gpt-5.5"}, {"model": "ollama/qwen-cloud"},
               {"base_url": "https://provider.example/v1"},
               {"task": dict(self.task, data_classification="private")},
               {"allow_agent": "yes"}]
        for obj in bad:
            with self.subTest(obj=obj), self.assertRaises(ValueError):
                self.run_pilot(**({"allow_agent": True} | obj))
        self.assertFalse(FakeLLM.seen)

    def test_rejects_stale_export_before_running(self):
        (self.export / "stale.log").write_text("previous run")
        with self.assertRaises(ValueError):
            self.run_pilot(allow_agent=True)
        self.assertFalse(FakeLLM.seen)

    def test_cloud_credentials_do_not_leak_into_local_agent(self):
        with patch.dict(os.environ, {"LLM_API_KEY": "PRIVATE_KEY"}):
            result = self.run_pilot(allow_agent=True)
        self.assertEqual(result["status"], "unsafe_environment")
        self.assertNotIn("PRIVATE_KEY", repr(result))
        self.assertFalse(FakeLLM.seen)

    def test_uses_upstream_conversation_api_and_withheld_review_cases(self):
        with patch.object(openhands_multifile_review, "review",
                          return_value={"status": "awaiting_human_review",
                                        "execution_authorized": False,
                                        "release_authorized": False}) as verifier:
            result = self.run_pilot(allow_agent=True)
        self.assertEqual(result["status"], "awaiting_human_review")
        self.assertTrue(result["agent_session_attempted"])
        self.assertFalse(result["release_authorized"])
        self.assertEqual(len(FakeLLM.seen), 1)
        self.assertEqual(FakeLLM.seen[0]["model"], MODEL)
        self.assertEqual(FakeLLM.seen[0]["base_url"], "http://ollama:11434")
        self.assertEqual(len(FakeConversation.seen), 1)
        self.assertTrue(FakeConversation.seen[0].closed)
        self.assertNotIn("HIDDEN_SECRET_CASE", FakeConversation.prompt)
        self.assertIn("app/logic.py", FakeConversation.prompt)
        self.assertIn("tests/test_logic.py", FakeConversation.prompt)
        verifier.assert_called_once_with(self.task, self.export, self.output)

    def test_upstream_error_requires_manual_review_and_closes_conversation(self):
        FakeConversation.fail = True
        with patch.object(openhands_multifile_review, "review") as verifier:
            result = self.run_pilot(allow_agent=True)
        self.assertEqual(result["status"], "agent_failed_review_required")
        self.assertTrue(result["agent_session_attempted"])
        self.assertFalse(result["automatic_retry_allowed"])
        self.assertNotIn("SECRET", repr(result))
        self.assertTrue(FakeConversation.seen[0].closed)
        verifier.assert_not_called()

    def test_fake_sdk_to_real_multifile_sandbox_acceptance(self):
        if not project.supported_host():
            if os.getenv("CODEN_REQUIRE_SANDBOX") == "1":
                self.fail("pinned Linux bubblewrap unavailable")
            self.skipTest("requires Linux pinned sandbox")
        result = self.run_pilot(allow_agent=True)
        self.assertEqual(result["status"], "awaiting_human_review")
        self.assertTrue(result["agent_session_attempted"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["release_authorized"])
        archive = Path(result["directory"]) / "candidate.pyz"
        self.assertEqual(project.execute(archive, ["a", "a", "b"]),
                         {"a": 2, "b": 1})


if __name__ == "__main__":
    unittest.main()
