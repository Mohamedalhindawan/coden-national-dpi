"""Allowlisted, read-only cloud runner tests."""
import tempfile
import unittest
from pathlib import Path
from ai_factory.safe_runner import run_read_only


class SafeRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "README.md").write_text("synthetic demo", encoding="utf-8")

    def test_reads_only_allowlisted_file(self):
        order = {"ready_for_review": True, "execution_authorized": False,
                 "allowed_actions": ["read_repository"]}
        result = run_read_only(order, self.root)
        self.assertEqual(result["status"], "completed_read_only")
        self.assertEqual(result["files_checked"], ["README.md"])

    def test_rejects_unreviewed_order(self):
        result = run_read_only({"ready_for_review": False, "allowed_actions": ["read_repository"]}, self.root)
        self.assertEqual(result["status"], "blocked")

    def test_rejects_write_or_test_actions(self):
        order = {"ready_for_review": True, "allowed_actions": ["read_repository", "write_branch"]}
        self.assertEqual(run_read_only(order, self.root)["status"], "blocked")

    def test_rejects_missing_file(self):
        (self.root / "README.md").unlink()
        order = {"ready_for_review": True, "allowed_actions": ["read_repository"]}
        self.assertEqual(run_read_only(order, self.root)["status"], "blocked")
