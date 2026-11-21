"""OpenHands output acceptance: multi-file source is data until verified.

No OpenHands agent/service is installed or run in CI; the workspace files
stand in for an upstream SDK sandbox export.
"""
import json
import os
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


if __name__ == "__main__":
    unittest.main()
