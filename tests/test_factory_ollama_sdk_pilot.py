"""Ollama official-SDK integration -> existing CODEN isolated Python review pilot.

Only a trusted operator may opt in. CI injects a synthetic SDK client; no
models, credentials, external endpoints or hosted inference are used.
"""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from ai_factory import ollama_sdk_pilot, project

MODEL = "qwen2.5-coder:1.5b"
ENDPOINT = "http://127.0.0.1:11434"


class OllamaSDKFactoryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.output = Path(tmp.name) / "review"
        self.output.mkdir()
        self.task = json.loads(project.EXAMPLE.read_text(encoding="utf-8"))
        self.task["recipe"] = "python-transform"
        self.sdk_client = MagicMock()
        self.sdk_client.generate.return_value = {"response": project.DEMO}
        self.sdk_factory = MagicMock(return_value=self.sdk_client)
        self.discovery = MagicMock(return_value={
            "probe_status": "available", "model_available": True,
            "provider_approved": False, "execution_authorized": False,
        })

    def run_pilot(self, **kwargs):
        params = {
            "task": self.task,
            "output_root": self.output,
            "endpoint": ENDPOINT,
            "model": MODEL,
            "allow_local_inference": True,
            "client_factory": self.sdk_factory,
            "discovery": self.discovery,
        }
        params.update(kwargs)
        return ollama_sdk_pilot.run_once(**params)

    def test_disabled_by_default_never_contacts_sdk_or_model_discovery(self):
        outcome = self.run_pilot(allow_local_inference=False)
        self.assertEqual(outcome["status"], "disabled")
        self.assertFalse(outcome["execution_authorized"])
        self.sdk_factory.assert_not_called()
        self.discovery.assert_not_called()

    def test_invalid_remote_and_non_boolean_options_fail_before_inference(self):
        inputs = (
            {"endpoint": "https://remote.provider.example"},
            {"endpoint": "http://localhost:11434"},
            {"endpoint": "http://user:secret@127.0.0.1:11434"},
            {"model": "qwen:cloud"},
            {"model": "qwen-remote-cloud"},
            {"model": "bad model"},
            {"allow_local_inference": "yes"},
        )
        for values in inputs:
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.run_pilot(**values)
        self.sdk_factory.assert_not_called()
        self.discovery.assert_not_called()

    def test_task_must_be_reviewable_synthetic_transform(self):
        for changes in ({"data_classification": "private"},
                        {"recipe": "status-counts"},
                        {"requested_actions": ["deploy"]}):
            task = {**self.task, **changes}
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.run_pilot(task=task)
        self.sdk_factory.assert_not_called()

    def test_missing_isolation_blocks_before_sdk_or_discovery(self):
        with patch.object(project, "supported_host", return_value=False):
            result = self.run_pilot()
        self.assertEqual(result["status"], "sandbox_unavailable")
        self.sdk_factory.assert_not_called()
        self.discovery.assert_not_called()

    def test_offline_only_environment_guard_rejects_cloud_auth(self):
        with patch.dict(os.environ, {"OLLAMA_API_KEY": "secret-external-key"}):
            result = self.run_pilot()
        self.assertEqual(result["status"], "unsafe_environment")
        self.assertNotIn("secret-external-key", repr(result))
        self.sdk_factory.assert_not_called()
        self.discovery.assert_not_called()

    def test_model_absent_blocks_before_sdk_inference(self):
        self.discovery.return_value = {
            "probe_status": "model_absent", "model_available": False,
        }
        with patch.object(project, "supported_host", return_value=True):
            result = self.run_pilot()
        self.assertEqual(result["status"], "model_unavailable")
        self.discovery.assert_called_once_with(ENDPOINT, MODEL, allow_loopback=True)
        self.sdk_factory.assert_not_called()

    def test_calls_official_client_once_with_no_redirects_proxies_or_tools(self):
        task = json.loads(json.dumps(self.task))
        task["review_cases"] = [{"input": ["HIDDEN_CASE"], "expected": {"HIDDEN_CASE": 1}}]
        with patch.object(project, "supported_host", return_value=True), \
             patch.object(project, "run", return_value=(self.output / "receipt", "awaiting_human_review")) as original_run:
            result = self.run_pilot(task=task)
        self.assertEqual(result["status"], "awaiting_human_review")
        self.assertFalse(result["release_authorized"])
        self.assertFalse(result["execution_authorized"])
        self.sdk_factory.assert_called_once_with(
            host=ENDPOINT, timeout=90, follow_redirects=False, trust_env=False,
        )
        self.sdk_client.generate.assert_called_once()
        kw = self.sdk_client.generate.call_args.kwargs
        self.assertEqual(kw["model"], MODEL)
        self.assertFalse(kw["stream"])
        self.assertEqual(kw["keep_alive"], 0)
        self.assertEqual(kw["options"]["temperature"], 0)
        self.assertNotIn("HIDDEN_CASE", kw["prompt"])
        self.assertNotIn("tools", kw)
        self.sdk_client.close.assert_called_once()
        original_run.assert_called_once()
        self.assertEqual(original_run.call_args.args[:2], (task, self.output))
        self.assertEqual(list(self.output.glob(".model-source-*")), [])

    def test_invalid_model_output_never_reaches_project_runner(self):
        for raw in ({"response": "print('not a function')"},
                    {"response": "x" * 17000},
                    {"response": None},
                    {"wrong": project.DEMO}):
            self.sdk_client.generate.return_value = raw
            with self.subTest(raw_type=type(raw)), \
                 patch.object(project, "supported_host", return_value=True), \
                 patch.object(project, "run") as runner:
                result = self.run_pilot()
            self.assertEqual(result["status"], "invalid_model_output")
            runner.assert_not_called()
        self.assertEqual(list(self.output.glob(".model-source-*")), [])

    def test_sdk_error_sanitized_and_no_hidden_retry(self):
        self.sdk_client.generate.side_effect = OSError("SECRET provider exception")
        with patch.object(project, "supported_host", return_value=True):
            result = self.run_pilot()
        self.assertEqual(result["status"], "inference_failed")
        self.assertNotIn("SECRET", repr(result))
        self.sdk_client.generate.assert_called_once()

    def test_actual_bubblewrap_acceptance_uses_fake_sdk_not_real_model(self):
        if not project.supported_host():
            if os.getenv("CODEN_REQUIRE_SANDBOX") == "1":
                self.fail("pinned sandbox required in CI")
            self.skipTest("requires verified Linux bubblewrap")
        outcome = self.run_pilot()
        self.assertEqual(outcome["status"], "awaiting_human_review")
        review = Path(outcome["directory"])
        self.assertTrue((review / "candidate.pyz").exists())
        self.assertTrue((review / "review.json").exists())
        self.assertFalse(json.loads((review / "review.json").read_text())["release_authorized"])
        self.assertEqual(list(self.output.glob(".model-source-*")), [])
        self.sdk_client.generate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
