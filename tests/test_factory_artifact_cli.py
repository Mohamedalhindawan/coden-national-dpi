"""Offline operator CLI evidence verification tests (no model/API calls)."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


def _hash(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False).encode()).hexdigest()


class ArtifactCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.files = self.root / "files"
        self.files.mkdir()
        (self.files / "module.py").write_text("VALUE = 7\n", encoding="utf-8")
        data = (self.files / "module.py").read_bytes()
        self.manifest = {
            "schema": "coden.artifact.bundle.v1", "task_id": "pilot_1",
            "files": [{"path": "module.py", "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}],
        }
        self.request = {
            "schema": "coden.runtime.request.v1", "task_id": "pilot_1",
            "task_sha256": "a"*64, "classification": "synthetic",
            "required_capabilities": ["coding"], "allowed_providers": ["local_qwen"],
            "allow_external_api": False, "max_tokens_total": 100,
            "max_duration_seconds": 15, "max_cost_usd": "0",
        }
        self.report = {
            "schema": "coden.runtime.report.v1", "task_id": "pilot_1",
            "provider_id": "local_qwen", "model_id": "qwen_local",
            "transport": "local", "status": "completed", "error_code": None,
            "artifact_sha256": _hash(self.manifest), "input_tokens": 1,
            "output_tokens": 2, "duration_ms": 90, "cost_usd": "0",
        }
        self.req = self.root / "request.json"
        self.rep = self.root / "report.json"
        self.man = self.root / "manifest.json"

    def call(self):
        self.req.write_text(json.dumps(self.request), encoding="utf-8")
        self.rep.write_text(json.dumps(self.report), encoding="utf-8")
        self.man.write_text(json.dumps(self.manifest), encoding="utf-8")
        return subprocess.run([sys.executable, "-m", "ai_factory.artifact_cli",
                               "--request", str(self.req), "--report", str(self.rep),
                               "--manifest", str(self.man), "--root", str(self.files)],
                              text=True, capture_output=True)

    def test_valid_bundle_reports_files_verified_but_no_release(self):
        result = self.call()
        self.assertEqual(result.returncode, 0, result.stderr)
        result_json = json.loads(result.stdout)
        self.assertTrue(result_json["artifact_verified"])
        self.assertFalse(result_json["release_approved"])
        self.assertFalse(result_json["execution_authorized"])
        self.assertEqual(result_json["files_verified"], 1)

    def test_file_tamper_returns_error_without_exposing_file_data(self):
        (self.files / "module.py").write_text("SECRET_UNTRUSTED", encoding="utf-8")
        result = self.call()
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("SECRET_UNTRUSTED", result.stdout + result.stderr)

    def test_manifest_tamper_rejected_even_if_files_untouched(self):
        self.report["artifact_sha256"] = "0"*64
        result = self.call()
        self.assertEqual(result.returncode, 2)

    def test_extra_file_is_rejected_and_never_printed(self):
        (self.files / "private.txt").write_text("secret_should_not_print", encoding="utf-8")
        result = self.call()
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("secret_should_not_print", result.stdout + result.stderr)

    def test_symlinked_request_is_rejected(self):
        self.call()
        link = self.root / "linked_request.json"
        link.symlink_to(self.req)
        result = subprocess.run([sys.executable, "-m", "ai_factory.artifact_cli",
                                 "--request", str(link), "--report", str(self.rep),
                                 "--manifest", str(self.man), "--root", str(self.files)],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)

    def test_duplicate_json_keys_rejected(self):
        self.call()
        self.req.write_text('{"schema": "coden.runtime.request.v1", "schema": "repeat"}')
        result = subprocess.run([sys.executable, "-m", "ai_factory.artifact_cli",
                                 "--request", str(self.req), "--report", str(self.rep),
                                 "--manifest", str(self.man), "--root", str(self.files)],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
