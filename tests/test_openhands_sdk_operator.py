"""Official OpenHands SDK wiring contract: never run a host-local agent in CI."""
import json
import os
import subprocess
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

    def test_overlapping_review_path_rejected_before_conversation(self):
        with self.assertRaises(ValueError):
            self.run_pilot(allow_agent=True, output_root=self.export)
        self.assertFalse(FakeConversation.seen)
        self.assertFalse(FakeLLM.seen)
        self.assertEqual(list(self.export.iterdir()), [])

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

    def test_real_sdk_default_blocked_before_import_pending_admission(self):
        with patch.object(openhands_sdk_operator, "_official_sdk") as real_sdk:
            result = self.run_pilot(allow_agent=True, sdk=None)
        self.assertEqual(result["status"], "blocked_runtime_admission")
        self.assertFalse(result["agent_session_attempted"])
        self.assertFalse(result["release_authorized"])
        real_sdk.assert_not_called()

    def test_close_failure_blocks_artifact_review_and_retry(self):
        with patch.object(FakeConversation, "close", side_effect=RuntimeError("private cleanup detail")), \
             patch.object(openhands_multifile_review, "review") as verifier:
            result = self.run_pilot(allow_agent=True)
        self.assertEqual(result["status"], "cleanup_unverified_review_required")
        self.assertTrue(result["agent_session_attempted"])
        self.assertFalse(result["automatic_retry_allowed"])
        self.assertFalse(result["release_authorized"])
        self.assertNotIn("private cleanup detail", repr(result))
        verifier.assert_not_called()

    def test_independent_lint_timeout_requires_manual_review(self):
        with patch.object(project, "supported_host", return_value=True), \
             patch.object(project, "lint", side_effect=subprocess.TimeoutExpired("private lint", 8)):
            result = self.run_pilot(allow_agent=True)
        self.assertEqual(result["status"], "artifact_review_required")
        self.assertTrue(result["agent_session_attempted"])
        self.assertFalse(result["automatic_retry_allowed"])
        self.assertFalse(result["release_authorized"])
        self.assertEqual(list(self.output.iterdir()), [])
        self.assertNotIn("private lint", repr(result))

    def test_invalid_generated_test_syntax_requires_manual_review(self):
        original = FakeConversation.run
        def malformed(conversation):
            original(conversation)
            (self.export / "tests" / "test_logic.py").write_text("def private_fixture(:\n")
        with patch.object(FakeConversation, "run", new=malformed):
            result = self.run_pilot(allow_agent=True)
        self.assertEqual(result["status"], "artifact_review_required")
        self.assertTrue(result["agent_session_attempted"])
        self.assertFalse(result["automatic_retry_allowed"])
        self.assertFalse(result["release_authorized"])
        self.assertTrue(FakeConversation.seen[0].closed)
        self.assertNotIn("private_fixture", repr(result))
        self.assertEqual(list(self.output.iterdir()), [])

    def test_qwen_pilot_uses_reviewed_options_with_fixture_only(self):
        with patch.object(project, "supported_host", return_value=True), \
             patch.object(openhands_multifile_review, "review",
                          return_value={"status": "awaiting_human_review"}):
            result = self.run_pilot(allow_agent=True, model="openai/local-qwen",
                                    base_url="http://qwen3:11434/v1")
        self.assertEqual(result["status"], "awaiting_human_review")
        expected = openhands_sdk_operator.review_qwen_route(
            model="openai/local-qwen", base_url="http://qwen3:11434/v1")["llm_options"]
        self.assertEqual(FakeLLM.seen, [dict(expected, api_key="fixture-only")])
        self.assertFalse(result["release_authorized"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["automatic_retry_allowed"])

    def test_qwen_fixture_rejects_mixed_routes_and_preserves_real_gate(self):
        for model, url in (
            ("openai/local-qwen", "http://ollama:11434"),
            (MODEL, "http://qwen3:11434/v1"),
            ("openai/local-qwen", "http://qwen3:11434/v1/"),
            ("openai/local-qwen", "https://api.openai.com/v1"),
        ):
            with self.subTest(model=model,url=url), self.assertRaises(ValueError):
                self.run_pilot(allow_agent=True, model=model, base_url=url)
        with patch.object(openhands_sdk_operator, "_official_sdk") as official:
            result=self.run_pilot(allow_agent=True, sdk=None,
                                  model="openai/local-qwen",base_url="http://qwen3:11434/v1")
            self.assertEqual(result["status"], "blocked_runtime_admission")
            official.assert_not_called()
        self.assertFalse(FakeLLM.seen)
        self.assertFalse(FakeConversation.seen)

    def test_qwen_failure_fixtures_do_not_retry_or_review_and_redact_errors(self):
        class ProviderFailure(RuntimeError):
            def __init__(self, status):
                super().__init__("fixture-private-credential")
                self.status_code = status
        for failure in (ProviderFailure(401), ProviderFailure(403),
                        ProviderFailure(429), TimeoutError("fixture-private-credential")):
            with self.subTest(failure=type(failure).__name__,
                              status=getattr(failure,"status_code",None)):
                FakeConversation.seen = []
                FakeLLM.seen = []
                with patch.object(project,"supported_host",return_value=True), \
                     patch.object(FakeConversation,"run",side_effect=failure) as run, \
                     patch.object(openhands_multifile_review,"review") as review:
                    result=self.run_pilot(allow_agent=True,model="openai/local-qwen",
                                          base_url="http://qwen3:11434/v1")
                self.assertEqual(result["status"],"agent_failed_review_required")
                self.assertTrue(result["agent_session_attempted"])
                self.assertFalse(result["automatic_retry_allowed"])
                self.assertFalse(result["execution_authorized"])
                self.assertFalse(result["release_authorized"])
                self.assertNotIn("fixture-private-credential",repr(result))
                self.assertEqual(len(FakeLLM.seen),1)
                self.assertEqual(len(FakeConversation.seen),1)
                self.assertTrue(FakeConversation.seen[0].closed)
                run.assert_called_once_with()
                review.assert_not_called()

    def test_qwen_cancelled_fixture_closes_conversation_without_review(self):
        import asyncio
        with patch.object(project,"supported_host",return_value=True), \
             patch.object(FakeConversation,"run",side_effect=asyncio.CancelledError()) as run, \
             patch.object(openhands_multifile_review,"review") as review:
            with self.assertRaises(asyncio.CancelledError):
                self.run_pilot(allow_agent=True,model="openai/local-qwen",
                               base_url="http://qwen3:11434/v1")
        self.assertEqual(len(FakeConversation.seen),1)
        self.assertTrue(FakeConversation.seen[0].closed)
        run.assert_called_once_with()
        review.assert_not_called()

    def test_qwen_route_review_has_no_secret_or_execution(self):
        result = openhands_sdk_operator.review_qwen_route(
            model="openai/local-qwen", base_url="http://qwen3:11434/v1")
        options = result["llm_options"]
        self.assertEqual(options["model"], "openai/local-qwen")
        self.assertEqual(options["base_url"], "http://qwen3:11434/v1")
        self.assertEqual(options["api_mode"], "chat")
        self.assertEqual(options["num_retries"], 1)
        self.assertEqual(options["timeout"], 35)
        self.assertFalse(options["drop_params"])
        self.assertIsNone(options["fallback_strategy"])
        self.assertNotIn("api_key", options)
        self.assertFalse(result["credentials_bound"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["release_authorized"])
        self.assertFalse(FakeLLM.seen)

    def test_qwen_route_review_rejects_unapproved_endpoints(self):
        for model, url in (
            ("openai/gpt-5.6", "http://qwen3:11434/v1"),
            ("openai/local-qwen", "https://api.openai.com/v1"),
            ("openai/local-qwen", "http://qwen3:11434/v1?proxy=cloud"),
            ("openai/local-qwen", "http://qwen3:11434@external.example/v1"),
            ("openai/local-qwen", "http://127.0.0.1:11434/v1"),
        ):
            with self.subTest(model=model, url=url), self.assertRaises(ValueError):
                openhands_sdk_operator.review_qwen_route(model=model, base_url=url)
        self.assertFalse(FakeLLM.seen)

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


class ManagedWorkspace(FakeDockerWorkspace):
    started = 0
    closed = 0
    def __init__(self, **kwargs):
        type(self).started += 1
        self.server_image = kwargs["server_image"]
        self.volumes = kwargs["volumes"]
        self.network = kwargs["network"]
        self.forward_env = kwargs["forward_env"]
        self.extra_ports = kwargs["extra_ports"]
        self.enable_gpu = kwargs["enable_gpu"]
        self.detach_logs = kwargs["detach_logs"]

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        type(self).closed += 1


class OpenHandsManagedLaunchTests(OpenHandsSDKOperatorTests):
    # Inherits the contract fixtures; management must gate Docker startup
    # BEFORE constructing DockerWorkspace because __init__ starts containers.
    def setUp(self):
        super().setUp()
        self.sdk = SimpleNamespace(**vars(SDK))
        self.sdk.DockerWorkspace = ManagedWorkspace
        ManagedWorkspace.started = 0
        ManagedWorkspace.closed = 0
        self.image = IMAGE
        self.network = "coden_internal"
        self.inspector_calls = []

    def inspector(self, kind, name):
        self.inspector_calls.append((kind, name))
        if kind == "context":
            return {"Name": "default", "Endpoints": {"docker": {"Host": "unix:///var/run/docker.sock", "SkipTLSVerify": False}}}
        if kind == "network":
            return {"Internal": True, "Driver": "bridge", "Name": name}
        if kind == "image":
            return {"RepoDigests": [name], "Id": "sha256:" + "f" * 64}
        raise AssertionError("unexpected Docker inspect")

    def launch(self, **changes):
        kwargs = {
            "task": self.task,
            "candidate_root": self.export,
            "output_root": self.output,
            "model": MODEL,
            "base_url": "http://ollama:11434",
            "server_image": self.image,
            "network": self.network,
            "allow_agent": True,
            "sdk": self.sdk,
            "inspect_docker": self.inspector,
        }
        kwargs.update(changes)
        return openhands_sdk_operator.launch_isolated(**kwargs)

    def test_real_managed_launch_blocked_before_docker_or_sdk(self):
        with patch.object(openhands_sdk_operator, "_official_sdk") as real_sdk:
            result = self.launch(sdk=None)
        self.assertEqual(result["status"], "blocked_runtime_admission")
        self.assertFalse(result["agent_session_attempted"])
        self.assertEqual(self.inspector_calls, [])
        self.assertEqual(ManagedWorkspace.started, 0)
        real_sdk.assert_not_called()

    def test_managed_disabled_has_zero_side_effects(self):
        with patch.object(project, "supported_host") as host:
            result = self.launch(allow_agent=False)
        self.assertEqual(result["status"], "disabled")
        self.assertEqual(ManagedWorkspace.started, 0)
        self.assertEqual(self.inspector_calls, [])
        host.assert_not_called()

    def test_invalid_parameters_rejected_before_docker_and_sdk(self):
        invalid = [
            {"server_image": "ghcr.io/openhands/agent-server:latest"},
            {"network": "host"},
            {"network": "bridge"},
            {"network": "none"},
            {"base_url": "https://ollama.com"},
            {"model": "ollama/qwen2.5-coder:cloud"},
            {"task": dict(self.task, data_classification="private")},
        ]
        for params in invalid:
            with self.subTest(params=params), self.assertRaises(ValueError):
                self.launch(**params)
        self.assertEqual(ManagedWorkspace.started, 0)
        self.assertEqual(self.inspector_calls, [])

    def test_overlapping_review_path_rejected_before_docker_inspection(self):
        for path in (self.export, self.root):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.launch(output_root=path)
        self.assertEqual(self.inspector_calls, [])
        self.assertEqual(ManagedWorkspace.started, 0)
        self.assertFalse(FakeConversation.seen)
        self.assertEqual(list(self.export.iterdir()), [])

    def test_remote_docker_context_blocked_before_workspace(self):
        invalid_hosts = (
            "tcp://127.0.0.1:2375",
            "ssh://someone@remote.example",
            "unix:///tmp/untrusted/docker.sock",
            "unix:///home/ci/.docker/desktop/docker.sock",
            None,
        )
        for host in invalid_hosts:
            def fake_inspect(kind, name):
                if kind == "context":
                    return {"Name": "remote", "Endpoints": {"docker": {"Host": host}}}
                return self.inspector(kind, name)
            with self.subTest(host=host):
                result = self.launch(inspect_docker=fake_inspect)
                self.assertEqual(result["status"], "unsafe_runtime")
        self.assertEqual(ManagedWorkspace.started, 0)

    def test_preflight_only_checks_runtime_without_loading_or_starting_sdk(self):
        with patch.object(project, "supported_host", return_value=True):
            result = self.launch(allow_agent=False, preflight_only=True)
        self.assertEqual(result["status"], "preflight_passed")
        self.assertFalse(result["agent_session_attempted"])
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(self.inspector_calls, [
            ("context", "current"), ("network", self.network), ("image", self.image),
        ])
        self.assertEqual(ManagedWorkspace.started, 0)
        self.assertFalse(FakeLLM.seen)

    def test_image_or_network_inspection_failed_does_not_start_docker(self):
        for inspector in [
            lambda kind, name: {"Internal": False, "Driver": "bridge"} if kind == "network" else self.inspector(kind,name),
            lambda kind, name: {"Internal": True, "Driver": "host"} if kind == "network" else self.inspector(kind,name),
            lambda kind, name: {"RepoDigests": [], "Id": "sha256:"+"f"*64} if kind == "image" else self.inspector(kind,name),
            lambda kind, name: (_ for _ in ()).throw(OSError("sensitive docker exception")),
        ]:
            with self.subTest(inspector=inspector):
                result = self.launch(inspect_docker=inspector)
                self.assertEqual(result["status"], "unsafe_runtime")
                self.assertFalse(result["automatic_retry_allowed"])
                self.assertNotIn("sensitive", repr(result))
        self.assertEqual(ManagedWorkspace.started, 0)

    def test_model_authorization_and_sandbox_checked_before_docker_constructor(self):
        with patch.dict(os.environ, {"LLM_API_KEY": "secret"}):
            response = self.launch()
        self.assertEqual(response["status"], "unsafe_environment")
        with patch.object(project, "supported_host", return_value=False):
            response = self.launch()
        self.assertEqual(response["status"], "sandbox_unavailable")
        self.assertEqual(ManagedWorkspace.started, 0)

    def test_success_creates_single_pinned_workspace_then_uses_sdk_contract(self):
        with patch.object(project, "supported_host", return_value=True), \
             patch.object(openhands_multifile_review, "review",
                          return_value={"status": "awaiting_human_review", "release_authorized": False}) as verify:
            result = self.launch()
        self.assertEqual(result["status"], "awaiting_human_review")
        self.assertTrue(result["agent_session_attempted"])
        self.assertEqual(ManagedWorkspace.started, 1)
        self.assertEqual(ManagedWorkspace.closed, 1)
        self.assertEqual(self.inspector_calls, [
            ("context", "current"), ("network", self.network), ("image", self.image)
        ])
        verify.assert_called_once_with(self.task, self.export, self.output)

    def test_review_only_after_managed_workspace_exit(self):
        def verify(*args):
            self.assertEqual(ManagedWorkspace.closed, 1)
            return {"status": "awaiting_human_review"}
        with patch.object(project, "supported_host", return_value=True), \
             patch.object(openhands_multifile_review, "review", side_effect=verify):
            result = self.launch()
        self.assertEqual(result["status"], "awaiting_human_review")

    def test_workspace_exit_failure_never_reviews_artifacts(self):
        with patch.object(project, "supported_host", return_value=True), \
             patch.object(ManagedWorkspace, "__exit__", side_effect=RuntimeError("cleanup")), \
             patch.object(openhands_multifile_review, "review") as verify:
            result = self.launch()
        self.assertFalse(result["automatic_retry_allowed"])
        self.assertFalse(result["release_authorized"])
        verify.assert_not_called()

    def test_launch_crash_reports_manual_review_and_workspace_is_closed(self):
        FakeConversation.fail = True
        with patch.object(project, "supported_host", return_value=True):
            result = self.launch()
        self.assertEqual(result["status"], "agent_failed_review_required")
        self.assertEqual(ManagedWorkspace.started, 1)
        self.assertEqual(ManagedWorkspace.closed, 1)
        self.assertFalse(result["automatic_retry_allowed"])

    def test_constructor_failure_reports_uncertain_workspace_and_never_retries(self):
        class BrokenWorkspace(ManagedWorkspace):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                raise RuntimeError("sensitive startup failure after partial container creation")
        self.sdk.DockerWorkspace = BrokenWorkspace
        with patch.object(project, "supported_host", return_value=True):
            result = self.launch()
        self.assertEqual(result["status"], "workspace_start_failed_review_required")
        self.assertNotIn("sensitive", repr(result))
        self.assertFalse(result["automatic_retry_allowed"])


class ModeBBridgeContractTests(unittest.TestCase):
    def task(self):
        # Trusted synthetic fixture; independent cases must never be sent.
        return {"id":"OPENHANDS_SYNTHETIC_1","title":"Synthetic multi-file status-counts project",
                "description":"Build a Python 3 program that reads a JSON list of status strings and produces a frequency map. Use app/logic.py, README.md and tests/test_logic.py only.",
                "data_classification":"synthetic","requested_actions":["run_tests"],
                "estimated_cost_usd":0,"recipe":"python-transform",
                "cases":[{"input":[],"expected":{}},{"input":["ready","done","ready"],"expected":{"ready":2,"done":1}}],
                "review_cases":[{"input":["تجريبي","تجريبي","done"],"expected":{"تجريبي":2,"done":1}}]}

    def test_modeb_exact_task_request_has_no_hidden_cases_or_secret(self):
        request = openhands_sdk_operator.prepare_modeb_request(self.task())
        self.assertEqual(request["allowed_files"], sorted(["app/logic.py","README.md","tests/test_logic.py"]))
        self.assertEqual(request["workspace"], "/workspace/export")
        self.assertEqual(request["limits"], {"cpu":2,"ram_bytes":4294967296,"pids":128,"scratch_bytes":1006632960,"seconds":600})
        self.assertEqual(request["model"]["base_url"], "http://qwen3:11434/v1")
        self.assertIsNone(request["model"]["fallback_strategy"])
        self.assertNotIn("api_key", request["model"])
        self.assertNotIn("review_cases", request)
        self.assertNotIn("تجريبي", str(request))
        self.assertFalse(request["execution_authorized"])
        for key,value in (("description","different"),("estimated_cost_usd",1),("review_cases",[])):
            with self.subTest(key=key), self.assertRaises(ValueError):
                openhands_sdk_operator.prepare_modeb_request(dict(self.task(),**{key:value}))

    def test_modeb_real_path_blocked_even_with_opt_in(self):
        with patch.object(openhands_sdk_operator,"_official_sdk") as sdk:
            result=openhands_sdk_operator.run_modeb_once(task=self.task(),allow_agent=True)
        self.assertEqual(result["status"],"blocked_runtime_admission")
        self.assertFalse(result["agent_session_attempted"])
        sdk.assert_not_called()

    def test_fixture_adapter_exact_receipt_and_cleanup(self):
        calls=[]
        class Adapter:
            def execute(self, request):
                calls.append(("execute",request))
                return {"status":"fixture_completed","task_sha256":request["task_sha256"]}
            def close(self):
                calls.append(("close",None))
                return {"fixture_cleanup":True}
        result=openhands_sdk_operator.run_modeb_once(task=self.task(),allow_agent=True,fixture_only=True,fixture_adapter=Adapter())
        self.assertEqual(result["status"],"fixture_completed_review_required")
        self.assertEqual([x[0] for x in calls],["execute","close"])
        self.assertFalse(result["runtime_isolation_verified"])
        self.assertFalse(result["agent_session_attempted"])
        self.assertFalse(result["release_authorized"])
        self.assertFalse(result["automatic_retry_allowed"])

    def test_fixture_failure_cancel_and_cleanup_fail_closed(self):
        for mode in ("bad_receipt","error","cleanup","cancelled"):
            calls=[]
            class Adapter:
                def execute(self,request):
                    calls.append("execute")
                    if mode=="error": raise RuntimeError("private-provider-secret")
                    return {"status":"fixture_completed","task_sha256":request["task_sha256"] if mode!="bad_receipt" else "0"*64}
                def close(self):
                    calls.append("close")
                    if mode=="cleanup": raise RuntimeError("private-cleanup-secret")
                    return {"fixture_cleanup":True}
            with self.subTest(mode=mode):
                result=openhands_sdk_operator.run_modeb_once(task=self.task(),allow_agent=True,fixture_only=True,fixture_adapter=Adapter(),cancelled=lambda:mode=="cancelled")
                self.assertNotEqual(result["status"],"fixture_completed_review_required")
                self.assertFalse(result["release_authorized"])
                self.assertNotIn("private",repr(result))
                self.assertEqual(calls,[] if mode=="cancelled" else ["execute","close"])

    def test_static_probe_blocks_actual_sdk_import_and_rejects_wrong_digest(self):
        from ai_factory import modeb_import_probe as probe
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"contract.json"
            p.write_text("{}")
            with self.assertRaisesRegex(ValueError,"r2_contract_digest_mismatch"):
                probe.validate_r2_contract(p)
            with self.assertRaisesRegex(ValueError,"independent_r2_admission_required"):
                probe.inspect(p,"0"*64)

    def test_static_probe_checks_exact_set_and_no_admission_claim(self):
        import hashlib
        from ai_factory import modeb_import_probe as probe
        records=[{"name":"fixture-"+str(i),"version":"1"} for i in range(126)]
        data={"lock_sha256":probe.EXPECTED_LOCK_SHA,"wheel_manifest_sha256":probe.EXPECTED_MANIFEST_SHA,
              "workspace_roots":{n:"1.63.1" for n in ("openhands-sdk","openhands-tools","openhands-workspace","openhands-agent-server")},
              "runtime_external_records":126,"dependency_records":records}
        data.update({k:False for k in ("adopted","security_approved","legal_approved","installation_authorized","import_authorized","release_authorized")})
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"contract.json"
            raw=json.dumps(data).encode()
            p.write_bytes(raw)
            with patch.object(probe,"EXPECTED_CONTRACT_SHA",hashlib.sha256(raw).hexdigest()):
                result=probe.validate_r2_contract(p)
            self.assertEqual(result["runtime_external_records"],126)
            self.assertFalse(result["sdk_imported"])
            self.assertFalse(result["import_authorized"])
            data["adopted"]=True
            raw=json.dumps(data).encode();p.write_bytes(raw)
            with patch.object(probe,"EXPECTED_CONTRACT_SHA",hashlib.sha256(raw).hexdigest()):
                with self.assertRaises(ValueError): probe.validate_r2_contract(p)

    def test_worker_prepares_exact_modeb_intent_without_queue_or_lease(self):
        import hashlib
        from ai_factory import offline_worker
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            path=root/"OPENHANDS_SYNTHETIC_1.json"
            raw=json.dumps(self.task(),ensure_ascii=False).encode()
            path.write_bytes(raw)
            result=offline_worker.prepare_modeb_trial(root,"OPENHANDS_SYNTHETIC_1",branch="review/modeb",commit="a"*40)
            self.assertEqual(result["task_file_sha256"],hashlib.sha256(raw).hexdigest())
            self.assertEqual(result["branch"],"review/modeb")
            self.assertEqual(result["commit"],"a"*40)
            self.assertEqual(result["request"]["task_id"],"OPENHANDS_SYNTHETIC_1")
            self.assertFalse(result["queue_enqueued"])
            self.assertFalse(result["lease_claimed"])
            self.assertFalse(result["execution_authorized"])
            self.assertEqual(list(root.iterdir()),[path])
            # The old synthetic worker must still refuse this recipe.
            with self.assertRaises(ValueError):
                offline_worker._load_task(root,"OPENHANDS_SYNTHETIC_1")
            path.write_text(json.dumps(dict(self.task(),description="modified")))
            with self.assertRaises(ValueError):
                offline_worker.prepare_modeb_trial(root,"OPENHANDS_SYNTHETIC_1",branch="review/modeb",commit="a"*40)


    def test_worker_fixture_trial_binds_source_and_exact_request_receipt(self):
        import hashlib
        from ai_factory import offline_worker
        calls=[]
        class Adapter:
            def execute(self,request):
                calls.append(request)
                digest=hashlib.sha256(project.encoded(request).encode()).hexdigest()
                return {"status":"fixture_completed","task_sha256":request["task_sha256"],
                        "request_sha256":digest}
            def close(self):
                return {"fixture_cleanup":True}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            path=root/"OPENHANDS_SYNTHETIC_1.json"
            raw=json.dumps(self.task(),ensure_ascii=False).encode()
            path.write_bytes(raw)
            source={"branch":"review/modeb","commit":"a"*40,
                    "task_file_sha256":hashlib.sha256(raw).hexdigest()}
            result=offline_worker.run_modeb_fixture_trial(root,"OPENHANDS_SYNTHETIC_1",
                branch=source["branch"],commit=source["commit"],
                expected_task_file_sha256=source["task_file_sha256"],
                allow_agent=True,fixture_only=True,fixture_adapter=Adapter())
            self.assertEqual(result["status"],"fixture_completed_review_required")
            self.assertEqual(calls[0]["source_identity"],source)
            self.assertEqual(result["source_identity"],source)
            self.assertEqual(result["request_sha256"],hashlib.sha256(project.encoded(calls[0]).encode()).hexdigest())
            self.assertNotIn("تجريبي",repr(calls))
            self.assertFalse(result["lease_claimed"])
            self.assertFalse(result["queue_enqueued"])
            self.assertFalse(result["release_authorized"])
            self.assertEqual(list(root.iterdir()),[path])
            with self.assertRaises(ValueError):
                offline_worker.run_modeb_fixture_trial(root,"OPENHANDS_SYNTHETIC_1",
                    branch=source["branch"],commit=source["commit"],
                    expected_task_file_sha256="0"*64,allow_agent=True,fixture_only=True,fixture_adapter=Adapter())
            self.assertEqual(len(calls),1)

    def test_worker_fixture_rejects_stale_receipt_and_never_activates_real_adapter(self):
        import hashlib
        from ai_factory import offline_worker
        calls=[]
        class Adapter:
            def execute(self,request):
                calls.append("execute")
                return {"status":"fixture_completed","task_sha256":request["task_sha256"],
                        "request_sha256":"0"*64}
            def close(self):
                calls.append("close")
                return {"fixture_cleanup":True}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            raw=json.dumps(self.task()).encode()
            (root/"OPENHANDS_SYNTHETIC_1.json").write_bytes(raw)
            args={"branch":"review/modeb","commit":"a"*40,
                  "expected_task_file_sha256":hashlib.sha256(raw).hexdigest(),
                  "allow_agent":True,"fixture_adapter":Adapter()}
            with patch.object(openhands_sdk_operator,"_official_sdk") as sdk:
                self.assertEqual(offline_worker.run_modeb_fixture_trial(root,"OPENHANDS_SYNTHETIC_1",**args)["status"],"blocked_runtime_admission")
                self.assertEqual(calls,[])
                result=offline_worker.run_modeb_fixture_trial(root,"OPENHANDS_SYNTHETIC_1",fixture_only=True,**args)
            sdk.assert_not_called()
            self.assertEqual(result["status"],"fixture_receipt_rejected")
            self.assertEqual(calls,["execute","close"])
            self.assertFalse(result["automatic_retry_allowed"])
            self.assertFalse(result["release_authorized"])


if __name__ == "__main__":
    unittest.main()
