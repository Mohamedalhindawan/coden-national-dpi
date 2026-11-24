"""TDD RED: authentic OpenHands source binary and Qwen private rootless link.

This pilot must prove real server-to-model HTTP; it must NEVER claim an SDK
Conversation, successful autonomous software engineering, or P0 closure.
"""
import copy
from pathlib import Path
import unittest

from ai_factory import factory_rootless_openhands_qwen_link as gate
from ai_factory import factory_real_qwen_server_admission as model

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github/workflows/factory-rootless-openhands-qwen-link.yml"
DOC = ROOT / "docs/FACTORY_ROOTLESS_OPENHANDS_QWEN_LINK.md"


def valid_receipt():
    return {
        "plan_version": "v1.0",
        "upstream_source_commit": "077f3fad6d31cd852be5c87176e0a93c3b446126",
        "binary_sha256": "5ad5fa2bb86256b510df3bfbbd9653fbc60a243ea744a579d3ca4c6fd9e91cf3",
        "model_sha256": model.MODEL_SHA,
        "llama_cpp_archive_sha256": model.LLAMA_SHA,
        "rootless_podman": True,
        "cgroup_v2_cpu_memory_pids": True,
        "private_internal_bridge": True,
        "exactly_two_containers": True,
        "both_containers_nonroot_capless_readonly": True,
        "no_host_port_bindings_or_secrets": True,
        "openhands_server_health_http_200": True,
        "model_health_from_openhands_container": True,
        "real_qwen_completion_from_openhands_container": True,
        "real_qwen_tokens_predicted": 8,
        "real_qwen_response_sha256": "a" * 64,
        "outside_ip_http_denied_from_openhands": True,
        "outside_dns_http_denied_from_openhands": True,
        "temporary_storage_bytes_and_inodes_capped": True,
        "child_processes_cgroup_attested": True,
        "signed_binary_provenance_verified": True,
        "independent_high_critical_scan_gate_passed": True,
        "no_openhands_sdk_conversation": True,
        "no_agent_tool_calls": True,
        "no_three_file_candidate_generated": True,
        "openhands_live_execution_authorized": False,
        "factory_production_authorized": False,
        "automatic_merge": False,
        "release_authorized": False,
        "paid_calls": 0,
    }


class RootlessOpenHandsQwenLinkTests(unittest.TestCase):
    def test_real_link_receipt_is_strictly_scoped(self):
        output = gate.validate_receipt(valid_receipt())
        self.assertEqual(output["stage"], "REAL_ROOTLESS_MODEL_CONNECTIVITY_ONLY")
        self.assertEqual(output["binary_sha256"], valid_receipt()["binary_sha256"])
        self.assertEqual(output["model_sha256"], model.MODEL_SHA)
        self.assertEqual(output["real_qwen_tokens_predicted"], 8)
        self.assertFalse(output["openhands_live_execution_authorized"])
        self.assertFalse(output["release_authorized"])
        self.assertFalse(output["factory_production_authorized"])
        self.assertFalse(output["automatic_merge"])
        self.assertEqual(output["paid_calls"], 0)

    def test_missing_any_positive_safety_or_identity_evidence_fails_closed(self):
        case = valid_receipt()
        positive = (
            "rootless_podman", "cgroup_v2_cpu_memory_pids",
            "private_internal_bridge", "exactly_two_containers",
            "both_containers_nonroot_capless_readonly",
            "no_host_port_bindings_or_secrets",
            "openhands_server_health_http_200",
            "model_health_from_openhands_container",
            "real_qwen_completion_from_openhands_container",
            "outside_ip_http_denied_from_openhands",
            "outside_dns_http_denied_from_openhands",
            "temporary_storage_bytes_and_inodes_capped",
            "child_processes_cgroup_attested",
            "signed_binary_provenance_verified",
            "independent_high_critical_scan_gate_passed",
            "no_openhands_sdk_conversation", "no_agent_tool_calls",
            "no_three_file_candidate_generated",
        )
        for name in positive:
            with self.subTest(field=name):
                changed = case.copy()
                changed[name] = False
                with self.assertRaises(ValueError):
                    gate.validate_receipt(changed)
                del changed[name]
                with self.assertRaises(ValueError):
                    gate.validate_receipt(changed)

    def test_never_accept_unauthorized_release_or_forged_hashes(self):
        for name, val in [
            ("plan_version", "v2.0"),
            ("binary_sha256", "0" * 64),
            ("upstream_source_commit", "0" * 40),
            ("model_sha256", "0" * 64),
            ("llama_cpp_archive_sha256", "0" * 64),
            ("real_qwen_response_sha256", "not-a-hash"),
            ("real_qwen_tokens_predicted", 0),
            ("real_qwen_tokens_predicted", 100000),
            ("real_qwen_tokens_predicted", True),
            ("openhands_live_execution_authorized", True),
            ("factory_production_authorized", True),
            ("automatic_merge", True),
            ("release_authorized", True),
            ("paid_calls", 1),
        ]:
            with self.subTest(field=name):
                value = copy.deepcopy(valid_receipt())
                value[name] = val
                with self.assertRaises(ValueError):
                    gate.validate_receipt(value)

    def test_strictly_excludes_unknown_fields_or_mock_override(self):
        value = valid_receipt()
        value["mock_results_accepted"] = True
        with self.assertRaises(ValueError):
            gate.validate_receipt(value)
        for wrong in (None, [], {}, {"success": True}, "PASS"):
            with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                gate.validate_receipt(wrong)

    def test_workflow_true_rootless_private_network_proof(self):
        content = WF.read_text(encoding="utf-8")
        for required in (
            ".github/workflows/openhands-source-build.yml",
            "feat/factory-p0-rootless-openhands-qwen-link-20261124",
            "podman info --format json",
            "rootless",
            "podman network create --internal",
            "podman network inspect",
            "podman build --network none",
            "podman exec",
            "podman start",
            "gh attestation verify",
            "sha256sum -c -",
            "source-product",
            model.MODEL_SHA,
            model.LLAMA_SHA,
            "http://ollama:11434/health",
            "http://ollama:11434/completion",
            "outside_ip_http_denied_from_openhands",
            "outside_dns_http_denied_from_openhands",
            "child_processes_cgroup_attested",
            "factory_rootless_openhands_qwen_link",
            "trap cleanup EXIT",
            "contents: read",
            "persist-credentials: false",
        ):
            self.assertIn(required, content)
        for unsafe in ("pull_request_target:", "--privileged", "--network host",
                       "continue-on-error: true", "release_authorized: true",
                       "gh pr merge", "OPENAI_API_KEY"):
            self.assertNotIn(unsafe, content)

    def test_docs_explicitly_block_real_agent_session(self):
        content = DOC.read_text(encoding="utf-8")
        for required in ("v1.0", "#162", "#180", "Rootless", "Qwen", "OpenHands",
                         "SDK Conversation", "not", "human review", "SBOM"):
            self.assertIn(required, content)


if __name__ == "__main__":
    unittest.main()
