"""Guardrails for a real authenticated rootless OpenHands API trial.

The server/model integration is already proven in #181. This separate check
must deny unauthenticated and incorrect session keys before any real SDK run.
"""
import unittest
from pathlib import Path

from ai_factory import factory_rootless_session_auth as gate

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github/workflows/factory-rootless-session-auth.yml"
DOC = ROOT / "docs/FACTORY_ROOTLESS_OPENHANDS_SESSION_AUTH.md"

def good():
    return {
        "plan_version": "v1.0",
        "rootless_podman": True,
        "signed_binary_sha256": gate.OPENHANDS_BINARY_SHA,
        "qwen_weights_sha256": gate.QWEN_SHA,
        "model_private_network_tested": True,
        "no_public_ports": True,
        "no_external_http_egress": True,
        "no_key_request_rejected": True,
        "incorrect_key_request_rejected": True,
        "valid_ephemeral_key_request_accepted": True,
        "openhands_health_200": True,
        "session_key_not_logged_or_exported": True,
        "session_key_unique_per_run": True,
        "startup_encryption_key_present": True,
        "actual_sdk_conversation_run": False,
        "agent_tool_calls_authorized": False,
        "release_authorized": False,
        "production_authorized": False,
        "automatic_merge": False,
        "paid_calls": 0,
    }

class AuthGateTests(unittest.TestCase):
    def test_restricted_success_receipt(self):
        obj = gate.verify(good())
        self.assertEqual(obj["stage"], "REAL_AUTHENTICATED_ROOTLESS_SERVER_ONLY")
        self.assertFalse(obj["actual_sdk_conversation_run"])
        self.assertFalse(obj["release_authorized"])
        self.assertEqual(obj["paid_calls"], 0)

    def test_missing_or_forged_auth_or_provenance_rejected(self):
        for name in (
            "rootless_podman", "model_private_network_tested",
            "no_public_ports", "no_external_http_egress",
            "no_key_request_rejected", "incorrect_key_request_rejected",
            "valid_ephemeral_key_request_accepted", "openhands_health_200",
            "session_key_not_logged_or_exported", "session_key_unique_per_run",
            "startup_encryption_key_present",
        ):
            with self.subTest(name=name):
                bad = good()
                bad[name] = False
                with self.assertRaises(ValueError):
                    gate.verify(bad)
        for key, value in (
            ("signed_binary_sha256", "f"*64),
            ("qwen_weights_sha256", "b"*64),
            ("plan_version", "v2.0"),
            ("actual_sdk_conversation_run", True),
            ("agent_tool_calls_authorized", True),
            ("production_authorized", True),
            ("release_authorized", True),
            ("automatic_merge", True),
            ("paid_calls", 1),
        ):
            with self.subTest(key=key):
                obj = good()
                obj[key] = value
                with self.assertRaises(ValueError):
                    gate.verify(obj)

    def test_unknown_fields_never_approve(self):
        for val in (None, "", [], {}, {"success": True}):
            with self.subTest(val=val), self.assertRaises(ValueError):
                gate.verify(val)
        obj = good()
        obj["auth_bypass_allowed"] = True
        with self.assertRaises(ValueError):
            gate.verify(obj)

    def test_actual_security_test_probes_negative_and_positive_headers(self):
        s = WF.read_text(encoding="utf-8")
        for required in (
            "feat/factory-p0-rootless-session-auth-gate-20261124",
            "podman info --format json",
            "podman network create --internal",
            "podman exec",
            "X-Session-API-Key",
            "GET /api/conversations/count HTTP/1.0",
            "OH_SESSION_API_KEYS_0",
            "OH_SECRET_KEY",
            "openssl rand -hex",
            "::add-mask::",
            "no_key_request_rejected",
            "incorrect_key_request_rejected",
            "valid_ephemeral_key_request_accepted",
            "factory_rootless_session_auth",
            "sha256sum -c -",
            "gh attestation verify",
            "trap cleanup EXIT",
            "persist-credentials: false",
            "contents: read",
        ):
            self.assertIn(required, s)
        for forbidden in ("pull_request_target:", "--privileged",
                          "continue-on-error: true",
                          "gh pr merge", "--network host"):
            self.assertNotIn(forbidden, s)

    def test_workflow_has_one_artifact_step_and_complete_secret_policy(self):
        s = WF.read_text(encoding="utf-8")
        self.assertEqual(s.count("      - name: Preserve sanitized only review evidence"), 1)
        self.assertNotIn("\n  || true)\n", s)
        self.assertIn("unexpected=$(printf", s)
        self.assertIn("OH_SESSION_API_KEYS_0|OH_SECRET_KEY)
        doc = DOC.read_text(encoding="utf-8")
        for token in ("#181", "#162", "Rootless", "OpenHands",
                      "Qwen", "v1.0", "SDK Conversation", "human review",
                      "SBOM", "not"):
            self.assertIn(token, doc)

if __name__ == "__main__":
    unittest.main()
 || true)", s)
        self.assertIn("if grep -Eiq", s)
        self.assertIn("if-no-files-found: error", s)

    def test_doc_retains_auth_session_and_license_limits(self):
        doc = DOC.read_text(encoding="utf-8")
        for token in ("#181", "#162", "Rootless", "OpenHands",
                      "Qwen", "v1.0", "SDK Conversation", "human review",
                      "SBOM", "not"):
            self.assertIn(token, doc)

if __name__ == "__main__":
    unittest.main()
