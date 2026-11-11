"""Test isolated, allowlisted synthetic file edits."""
import tempfile
import unittest
from pathlib import Path
from ai_factory.patch_preview import preview_synthetic_patch


class PatchPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_creates_demo_file_only_in_workspace(self):
        result = preview_synthetic_patch(self.root, "DEMO-123")
        self.assertEqual(result["status"], "preview_created")
        self.assertEqual(result["path"], "output/demo-task.txt")
        self.assertEqual((self.root / "output" / "demo-task.txt").read_text(), "CODEN demo task: DEMO-123\n")

    def test_rejects_path_like_identifiers(self):
        for value in ("../oops", "a/b", "", "x" * 65, "hello world"):
            with self.subTest(value=value):
                self.assertEqual(preview_synthetic_patch(self.root, value)["status"], "blocked")

    def test_rejects_existing_file_to_prevent_overwrite(self):
        folder = self.root / "output"
        folder.mkdir()
        (folder / "demo-task.txt").write_text("original")
        self.assertEqual(preview_synthetic_patch(self.root, "DEMO-1")["status"], "blocked")
        self.assertEqual((folder / "demo-task.txt").read_text(), "original")

    def test_rejects_symlinked_output_directory(self):
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        (self.root / "output").symlink_to(elsewhere, target_is_directory=True)
        self.assertEqual(preview_synthetic_patch(self.root, "DEMO-1")["status"], "blocked")
        self.assertFalse((elsewhere / "demo-task.txt").exists())
