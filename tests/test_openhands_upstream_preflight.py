"""Red/green checks against real pinned OpenHands SDK DockerWorkspace bytes.

This is source inspection, NOT a live agent run or Docker safety certification.
"""
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest

from ai_factory import openhands_upstream_preflight as probe


class OpenHandsPinnedUpstreamPreflightTests(unittest.TestCase):
    def test_exact_official_source_file_and_mit_license_are_present(self):
        proof = probe.inspect()
        self.assertEqual(proof["source_id"], "source-004")
        self.assertEqual(proof["upstream_commit"], "077f3fad6d31cd852be5c87176e0a93c3b446126")
        self.assertEqual(proof["upstream_blob_sha1"], "0a28fb27053f5e830b91914bdb4592aec30d3cc1")
        self.assertEqual(proof["package_version"], "1.63.1")
        self.assertEqual(proof["license"], "MIT")
        self.assertTrue(proof["source_integrity_verified"])
        self.assertFalse(proof["live_agent_execution_authorized"])
        self.assertFalse(proof["release_authorized"])
        self.assertEqual(proof["paid_calls"], 0)

    def test_real_upstream_docker_run_lacks_resource_isolation_policy(self):
        proof = probe.inspect()
        self.assertTrue(proof["upstream_workspace_starts_container"])
        self.assertEqual(proof["runtime_state"], "BLOCKED_FOR_REAL_SESSION")
        self.assertTrue({"cpu_cgroup", "memory_cgroup", "pids_limit", "capability_drop",
                         "read_only_root"} <= set(proof["missing_docker_controls"]))
        self.assertEqual(proof["sdk_install_status"], "not_installed_by_preflight")
        self.assertEqual(proof["docker_container_started"], False)

    def test_snapshot_tamper_or_symlink_always_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            for filename in probe.FILES:
                (temp / filename).write_bytes((probe.ASSETS / filename).read_bytes())
            (temp / "workspace.py").write_text("print('unexpected')", encoding="utf-8")
            with patch.object(probe, "ASSETS", temp):
                with self.assertRaises(ValueError):
                    probe.inspect()
            (temp / "workspace.py").unlink()
            (temp / "workspace.py").symlink_to(probe.ASSETS / "workspace.py")
            with patch.object(probe, "ASSETS", temp):
                with self.assertRaises(ValueError):
                    probe.inspect()

    def test_bad_license_is_not_replaced_by_a_reassuring_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            for filename in probe.FILES:
                (temp / filename).write_bytes((probe.ASSETS / filename).read_bytes())
            (temp / "LICENSE").write_text("unknown license", encoding="utf-8")
            with patch.object(probe, "ASSETS", temp):
                with self.assertRaises(ValueError):
                    probe.inspect()

    def test_cli_reports_evidence_without_claiming_agent_success(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "receipt.json"
            result = probe.write_receipt(out)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8")), result)
            self.assertEqual(result["runtime_state"], "BLOCKED_FOR_REAL_SESSION")
            self.assertFalse(result["live_agent_execution_authorized"])
            with self.assertRaises(ValueError):
                probe.write_receipt(out)


if __name__ == "__main__":
    unittest.main()
