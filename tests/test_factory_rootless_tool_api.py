"""TDD: real OpenHands bash command API with ephemeral authenticated synthetic command."""
import unittest
from pathlib import Path
from ai_factory import factory_rootless_tool_api_proof as gate

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github/workflows/factory-rootless-authenticated-tool-api.yml"
DOC = ROOT / "docs/FACTORY_ROOTLESS_AUTHENTICATED_TOOL_API.md"

def sample():
    return {
        "plan_version": "v1.0",
        "source_commit": "077f3fad6d31cd852be5c87176e0a93c3b446126",
        "openhands_binary_sha256": gate.OPENHANDS_SHA,
        "qwen_gguf_sha256": gate.QWEN_SHA,
        "rootless_cgroup_and_network_pass": True,
        "signed_source_build_verified": True,
        "strict_temporary_workspace_caps_verified": True,
        "real_model_link_verified": True,
        "no_key_post_denied": True,
        "wrong_key_post_denied": True,
        "correct_key_post_succeeded": True,
        "real_tool_exit_zero": True,
        "exact_synthetic_stdout_verified": True,
        "auth_key_never_forwarded_to_qwen": True,
        "actual_api_bash_command_ran": True,
        "model_generated_this_command": False,
        "openhands_sdk_conversation_ran": False,
        "independent_three_file_acceptance_passed": False,
        "production_authorized": False,
        "release_authorized": False,
        "automatic_merge": False,
        "paid_calls": 0,
    }

class RootlessAuthenticatedToolApiTests(unittest.TestCase):
    def test_synthetic_real_tool_receipt_acceptance_not_release(self):
        result=gate.verify(sample())
        self.assertEqual(result["stage"], "REAL_AUTHENTICATED_OPERATOR_TOOL_API_ONLY")
        self.assertFalse(result["openhands_sdk_conversation_ran"])
        self.assertFalse(result["release_authorized"])
        self.assertEqual(result["paid_calls"], 0)

    def test_each_missing_or_false_proof_rejected(self):
        source=sample()
        for k, val in source.items():
            if val is True:
                with self.subTest(field=k):
                    t=source.copy();t[k]=False
                    with self.assertRaises(ValueError):gate.verify(t)
                    del t[k]
                    with self.assertRaises(ValueError):gate.verify(t)

    def test_mismatched_hashes_unauthorized_claims_and_unknowns_rejected(self):
        source=sample()
        for k,v in (
            ("openhands_binary_sha256","f"*64),
            ("qwen_gguf_sha256","0"*64),
            ("source_commit","0"*40),
            ("plan_version","v2.0"),
            ("model_generated_this_command",True),
            ("openhands_sdk_conversation_ran",True),
            ("independent_three_file_acceptance_passed",True),
            ("production_authorized",True),
            ("release_authorized",True),
            ("automatic_merge",True),
            ("paid_calls",1),
            ("paid_calls",True),
        ):
            with self.subTest(k=k):
                t=source.copy();t[k]=v
                with self.assertRaises(ValueError):gate.verify(t)
        for val in (None,0,[],{},{"approved":True}):
            with self.subTest(val=val),self.assertRaises(ValueError):
                gate.verify(val)
        source["token"]="secret"
        with self.assertRaises(ValueError):gate.verify(source)

    def test_real_workflow_requires_ordered_negative_and_positive_post(self):
        text=WF.read_text(encoding="utf-8")
        for required in (
            "feat/factory-p0-authenticated-tool-api-probe-20261124",
            "gh attestation verify", "sha256sum -c -",
            "podman info --format json",
            "podman network create --internal",
            "OH_SESSION_API_KEYS_0",
            "OH_SECRET_KEY",
            "openssl rand -hex",
            "POST /api/bash/execute_bash_command HTTP/1.0",
            "X-Session-API-Key",
            "CODEN_FACTORY_TOOL_EXECUTION_OK",
            "no_key_post_denied",
            "wrong_key_post_denied",
            "correct_key_post_succeeded",
            "factory_rootless_tool_api_proof",
            "test_factory_rootless_tool_api.py",
            "model_generated_this_command",
            "podman exec -i \"$agent\" bash -eu -s",
            "podman exec -i \"$model\" /bin/sh -eu -s",
            "trap cleanup EXIT",
            "persist-credentials: false",
            "contents: read",
        ):
            self.assertIn(required,text)
        for forbidden in (
            "pull_request_target:", "continue-on-error: true",
            "--privileged", "--network host", "gh pr merge",
            "CODEN_AUTH_TEST_KEY", "--env-file", "set -x",
        ):
            self.assertNotIn(forbidden,text)
        self.assertEqual(text.count("      - name: Preserve sanitized only review evidence"),1)

    def test_immutable_documentation_marks_limitations(self):
        doc=DOC.read_text(encoding="utf-8")
        for term in ("v1.0","#162","#182","OpenHands","Qwen","Rootless",
                     "SDK Conversation","not","human review","SBOM"):
            self.assertIn(term,doc)

if __name__=="__main__":
    unittest.main()
