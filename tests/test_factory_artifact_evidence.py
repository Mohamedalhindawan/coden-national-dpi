"""Independent, filesystem-backed artifact evidence checks for synthetic CODEN tasks."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from ai_factory import artifact_evidence

def digest(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False).encode("utf-8")).hexdigest()


def request():
    return {
        "schema": "coden.runtime.request.v1",
        "task_id": "demo_1",
        "task_sha256": "a" * 64,
        "classification": "synthetic",
        "required_capabilities": ["coding"],
        "allowed_providers": ["local_qwen"],
        "allow_external_api": False,
        "max_tokens_total": 1000,
        "max_duration_seconds": 90,
        "max_cost_usd": "0",
    }


def report(manifest, **changes):
    result = {
        "schema": "coden.runtime.report.v1",
        "task_id": "demo_1",
        "provider_id": "local_qwen",
        "model_id": "qwen_local",
        "transport": "local",
        "status": "completed",
        "error_code": None,
        "artifact_sha256": digest(manifest),
        "input_tokens": 10,
        "output_tokens": 20,
        "duration_ms": 100,
        "cost_usd": "0",
    }
    return {**result, **changes}


class ArtifactEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "artifacts"
        self.root.mkdir()
        (self.root / "docs").mkdir()
        (self.root / "app.py").write_bytes(b"def main():\n    return 7\n")
        (self.root / "docs" / "README.md").write_bytes(b"# synthetic demo\n")

    def manifest(self):
        files = []
        for name in ("app.py", "docs/README.md"):
            content = (self.root / name).read_bytes()
            files.append({"path": name, "sha256": hashlib.sha256(content).hexdigest(),
                          "bytes": len(content)})
        return {"schema": "coden.artifact.bundle.v1", "task_id": "demo_1", "files": files}

    def check(self, manifest=None, report_overrides=None, root=None):
        manifest = manifest if manifest is not None else self.manifest()
        return artifact_evidence.verify_bundle(
            request(), report(manifest, **(report_overrides or {})),
            manifest, root if root is not None else self.root)

    def test_two_file_real_bundle_verified_without_approval(self):
        verified = self.check()
        self.assertTrue(verified["artifact_verified"])
        self.assertEqual(verified["files_verified"], 2)
        self.assertFalse(verified["acceptance_tests_verified"])
        self.assertFalse(verified["execution_authorized"])
        self.assertFalse(verified["release_approved"])
        self.assertFalse(verified["provider_approved"])

    def test_declared_file_content_changed_after_manifest_is_rejected(self):
        manifest = self.manifest()
        (self.root / "app.py").write_text("changed")
        with self.assertRaises(ValueError):
            self.check(manifest)

    def test_missing_or_extra_output_files_are_rejected(self):
        manifest = self.manifest()
        (self.root / "app.py").unlink()
        with self.assertRaises(ValueError):
            self.check(manifest)
        (self.root / "app.py").write_bytes(b"def main():\n    return 7\n")
        (self.root / "extra.txt").write_text("unlisted")
        with self.assertRaises(ValueError):
            self.check(manifest)

    def test_symlinked_file_or_directory_never_followed(self):
        manifest = self.manifest()
        (self.root / "app.py").unlink()
        (self.root / "app.py").symlink_to("/etc/passwd")
        with self.assertRaises(ValueError):
            self.check(manifest)
        (self.root / "app.py").unlink()
        (self.root / "app.py").write_bytes(b"def main():\n    return 7\n")
        (self.root / "docs" / "README.md").unlink()
        (self.root / "docs").rmdir()
        (self.root / "docs").symlink_to(Path(self.temp.name))
        with self.assertRaises(ValueError):
            self.check(manifest)

    def test_parent_root_symlink_fails_closed(self):
        manifest = self.manifest()
        link = Path(self.temp.name) / "alias"
        link.symlink_to(self.root)
        with self.assertRaises(ValueError):
            self.check(manifest, root=link)

    def test_manifest_path_traversal_absolute_and_hidden_names_rejected(self):
        for candidate in ("../app.py", "/etc/passwd", "docs/../../secret",
                          "docs//README.md", "./app.py", ".ssh/key",
                          "docs\\README.md", "folder/.", "docs/.secret"):
            manifest = self.manifest()
            manifest["files"][0]["path"] = candidate
            with self.subTest(path=candidate), self.assertRaises(ValueError):
                self.check(manifest)

    def test_duplicate_or_unsorted_manifest_is_rejected(self):
        manifest = self.manifest()
        manifest["files"].reverse()
        with self.assertRaises(ValueError):
            self.check(manifest)
        manifest = self.manifest()
        manifest["files"][1] = dict(manifest["files"][0])
        with self.assertRaises(ValueError):
            self.check(manifest)

    def test_manifest_digest_mismatch_and_wrong_task_identity(self):
        manifest = self.manifest()
        with self.assertRaises(ValueError):
            self.check(manifest, report_overrides={"artifact_sha256": "0" * 64})
        manifest["task_id"] = "someone_else"
        with self.assertRaises(ValueError):
            self.check(manifest)

    def test_runtime_failed_status_never_treated_as_verified_artifact(self):
        manifest = self.manifest()
        with self.assertRaises(ValueError):
            self.check(manifest, report_overrides={
                "status": "failed", "error_code": "worker_failed",
                "artifact_sha256": None,
            })

    def test_unrecognized_manifest_fields_and_invalid_sizes_rejected(self):
        manifest = self.manifest()
        manifest["oauth_token"] = "secret"
        with self.assertRaises(ValueError):
            self.check(manifest)
        manifest = self.manifest()
        manifest["files"][0]["bytes"] = True
        with self.assertRaises(ValueError):
            self.check(manifest)
        manifest = self.manifest()
        manifest["files"][0]["bytes"] = 2**31
        with self.assertRaises(ValueError):
            self.check(manifest)

    def test_empty_manifest_and_empty_bundle_rejected(self):
        manifest = self.manifest()
        manifest["files"] = []
        with self.assertRaises(ValueError):
            self.check(manifest)

    def test_untrusted_artifact_contents_not_echoed_in_evidence(self):
        manifest = self.manifest()
        result = self.check(manifest)
        self.assertNotIn("synthetic demo", json.dumps(result))
        self.assertNotIn("def main", json.dumps(result))

    def test_validated_sha_is_not_model_correctness_or_signing_proof(self):
        result = self.check()
        self.assertFalse(result["acceptance_tests_verified"])
        self.assertFalse(result["independent_security_review_passed"])
        self.assertFalse(result["cryptographically_signed"])
        self.assertFalse(result["release_approved"])

    def test_nested_regular_files_are_counted_exactly(self):
        (self.root / "docs" / "README.md").write_bytes(b"")
        manifest = self.manifest()
        r = self.check(manifest)
        self.assertEqual(r["files_verified"], 2)
        self.assertEqual(r["total_verified_bytes"], len((self.root / "app.py").read_bytes()))


if __name__ == "__main__":
    unittest.main()
