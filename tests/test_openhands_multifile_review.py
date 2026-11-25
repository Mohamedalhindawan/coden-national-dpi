"""OpenHands output acceptance: multi-file source is data until verified.

No OpenHands agent/service is installed or run in CI; the workspace files
stand in for an upstream SDK sandbox export.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ai_factory import openhands_multifile_review, project


SOURCE = """def transform(value):
    counts = {}
    for item in value:
        counts[item] = counts.get(item, 0) + 1
    return counts
"""

class OpenHandsMultiFileReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "agent_export"
        (self.source / "app").mkdir(parents=True)
        (self.source / "tests").mkdir()
        (self.source / "app" / "logic.py").write_text(SOURCE)
        (self.source / "README.md").write_text("# Synthetic counts\n", encoding="utf-8")
        (self.source / "tests" / "test_logic.py").write_text(
            "def test_example():\n    assert True\n", encoding="utf-8")
        self.outputs = self.root / "outputs"
        self.outputs.mkdir()
        self.task = json.loads(project.EXAMPLE.read_text(encoding="utf-8"))
        self.task["recipe"] = "python-transform"

    def assess(self, task=None):
        return openhands_multifile_review.review(
            task if task is not None else self.task, self.source, self.outputs)

    def test_reviewable_checked_in_synthetic_fixture(self):
        repo_root = Path(__file__).resolve().parents[1]
        tracked = repo_root / "ai_factory" / "examples" / "openhands-multifile"
        task = json.loads(
            (repo_root / "ai_factory" / "examples" / "openhands-multifile-task.json").read_text()
        )
        self.assertTrue(project.valid(task))
        if not project.supported_host():
            if os.getenv("CODEN_REQUIRE_SANDBOX") == "1":
                self.fail("pinned Linux sandbox required")
            self.skipTest("requires pinned Linux bubblewrap")
        result = openhands_multifile_review.review(task, tracked, self.outputs)
        self.assertEqual(result["status"], "awaiting_human_review")
        self.assertEqual(project.execute(result["directory"] / "candidate.pyz", ["a", "a"]),
                         {"a": 2})

    def test_cli_is_inert_without_explicit_sandbox_review_switch(self):
        cmd = [
            sys.executable, "-m", "ai_factory.openhands_multifile_review",
            "--task", "/unavailable-task.json",
            "--candidate-dir", "/unavailable-candidate",
            "--output-root", "/unavailable-output",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "disabled")
        self.assertFalse(data["agent_execution_performed"])
        self.assertFalse(data["execution_authorized"])

    def test_rejects_non_synthetic_task_before_artifacts(self):
        for changed in ({"data_classification": "private"},
                        {"estimated_cost_usd": 1},
                        {"recipe": "status-counts"},
                        {"requested_actions": ["deploy"]}):
            with self.subTest(changed=changed):
                with self.assertRaises(ValueError):
                    self.assess(dict(self.task, **changed))
        self.assertEqual(list(self.outputs.iterdir()), [])

    def test_rejects_extra_files_or_symlinked_source(self):
        (self.source / "private.env").write_text("SECRET=not-a-real-secret")
        with self.assertRaises(ValueError):
            self.assess()
        (self.source / "private.env").unlink()
        (self.source / "app" / "logic.py").unlink()
        (self.source / "app" / "logic.py").symlink_to(self.source / "README.md")
        with self.assertRaises(ValueError):
            self.assess()
        self.assertEqual(list(self.outputs.iterdir()), [])

    def test_hardlinked_export_is_rejected_before_review(self):
        outside = self.root / "operator-fixture.txt"
        outside.write_text("synthetic external fixture")
        target = self.source / "README.md"
        target.unlink()
        os.link(outside, target)
        with patch.object(project, "lint") as lint, \
             patch.object(project, "verify") as verify, self.assertRaises(ValueError):
            self.assess()
        lint.assert_not_called()
        verify.assert_not_called()
        self.assertEqual(list(self.outputs.iterdir()), [])

    def test_review_output_must_be_disjoint_from_agent_export(self):
        with patch.object(project, "supported_host", return_value=True), \
             patch.object(project, "lint"), \
             patch.object(project, "verify", return_value=1) as verify:
            with self.assertRaises(ValueError):
                openhands_multifile_review.review(self.task, self.source, self.source)
        verify.assert_not_called()
        self.assertEqual({p.name for p in self.source.iterdir()}, {"app", "tests", "README.md"})

    def test_export_parent_swap_never_reads_external_fixture(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "logic.py").write_text(SOURCE)
        app = self.source / "app"
        original = openhands_multifile_review._read_regular
        called = False

        def swap(*args, **kwargs):
            nonlocal called
            if not called:
                called = True
                app.rename(self.source / "old-app")
                app.symlink_to(outside, target_is_directory=True)
            return original(*args, **kwargs)

        with patch.object(openhands_multifile_review, "_read_regular", side_effect=swap), \
             patch.object(project, "supported_host", return_value=True), \
             patch.object(project, "lint") as lint, \
             patch.object(project, "verify", return_value=1) as verify:
            with self.assertRaises((ValueError, OSError)):
                self.assess()
        self.assertTrue(called)
        lint.assert_not_called()
        verify.assert_not_called()
        self.assertEqual(list(self.outputs.iterdir()), [])

    def test_rejects_unsafe_generated_python_without_executing_it(self):
        (self.source / "app" / "logic.py").write_text(
            "import os\ndef transform(value):\n    os.system('true')\n    return {}\n")
        with patch.object(project, "execute") as execute, self.assertRaises(ValueError):
            self.assess()
        execute.assert_not_called()

    def test_rejects_oversized_docs_and_test_files(self):
        for path in (self.source / "README.md", self.source / "tests" / "test_logic.py"):
            old = path.read_text()
            path.write_text("x" * 17000)
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.assess()
            path.write_text(old)

    def test_untrusted_tests_are_not_executed_or_bundled(self):
        marker = self.root / "should-not-exist"
        (self.source / "tests" / "test_logic.py").write_text(
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('oops')\n"
        )
        # Agent-generated tests are retained for human review, never executed
        # as part of CODEN acceptance or shipped inside the runnable archive.
        with patch.object(project, "supported_host", return_value=True), \
             patch.object(project, "lint"), \
             patch.object(project, "verify", return_value=2):
            result = self.assess()
        self.assertEqual(result["status"], "awaiting_human_review")
        self.assertFalse(marker.exists())
        import zipfile
        with zipfile.ZipFile(result["directory"] / "candidate.pyz") as archive:
            self.assertEqual(set(archive.namelist()),
                             {"__main__.py", "app/__init__.py", "app/logic.py"})
        self.assertFalse(result["release_authorized"])

    def test_missing_sandbox_fails_closed_without_artifact(self):
        with patch.object(project, "supported_host", return_value=False):
            with self.assertRaises(RuntimeError):
                self.assess()
        self.assertEqual(list(self.outputs.iterdir()), [])

    def test_failed_independent_review_cannot_request_approval(self):
        with patch.object(project, "supported_host", return_value=True), \
             patch.object(project, "lint"), \
             patch.object(project, "verify", side_effect=[2, ValueError("hidden check failed")]):
            result = self.assess()
        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["release_authorized"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse((result["directory"] / "review.json").exists())

    def test_actual_multifile_zipapp_acceptance_inside_pinned_linux_sandbox(self):
        if not project.supported_host():
            if os.getenv("CODEN_REQUIRE_SANDBOX") == "1":
                self.fail("pinned Linux sandbox required")
            self.skipTest("needs pinned Linux bubblewrap sandbox")
        result = self.assess()
        self.assertEqual(result["status"], "awaiting_human_review")
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["release_authorized"])
        root = result["directory"]
        self.assertTrue((root / "candidate.pyz").is_file())
        receipt = json.loads((root / "review.json").read_text())
        self.assertEqual(receipt["review_cases"], len(self.task["review_cases"]))
        self.assertFalse(receipt["release_authorized"])
        self.assertEqual(project.execute(root / "candidate.pyz", ["x", "x", "y"]),
                         {"x": 2, "y": 1})


    def test_review_receipt_binds_all_three_original_files_and_task(self):
        with patch.object(project, "supported_host", return_value=True), \
             patch.object(project, "lint"), \
             patch.object(project, "verify", side_effect=[2, 1]):
            result = self.assess()
        receipt = json.loads((result["directory"] / "review.json").read_text())
        expected = {name: hashlib.sha256((self.source / name).read_bytes()).hexdigest()
                    for name in sorted(openhands_multifile_review.EXPECTED_FILES)}
        self.assertEqual(receipt["source_files_sha256"], expected)
        self.assertEqual(receipt["task_sha256"],
                         hashlib.sha256(project.encoded(self.task).encode("utf-8")).hexdigest())
        self.assertFalse(receipt["agent_authored_tests_executed"])
        self.assertFalse(receipt["release_authorized"])

    def test_independent_timeout_keeps_evidence_without_review_receipt(self):
        with patch.object(project, "supported_host", return_value=True), \
             patch.object(project, "lint"), \
             patch.object(project, "verify", side_effect=[2, subprocess.TimeoutExpired("fixture", 5)]):
            result = self.assess()
        self.assertEqual(result["status"], "failed")
        self.assertTrue((result["directory"] / "candidate.pyz").is_file())
        self.assertFalse((result["directory"] / "review.json").exists())
        self.assertFalse(result["automatic_retry_allowed"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["release_authorized"])


if __name__ == "__main__":
    unittest.main()
