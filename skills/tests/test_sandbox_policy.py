import tempfile
import unittest
from pathlib import Path

from skills.orchestration.sandbox import SandboxPolicy, SandboxViolation, redact_secrets

class SandboxPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        (self.root / "src").mkdir()
        (self.root / "reports").mkdir()
        (self.root / "src" / "input.txt").write_text("synthetic", encoding="utf-8")
        self.policy = SandboxPolicy(
            workspace_root=self.root,
            read_scope=["workspace://src/"],
            write_scope=["workspace://reports/"],
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_allows_read_inside_read_scope(self):
        self.assertEqual(self.policy.authorize("workspace://src/input.txt", "read"), self.root / "src" / "input.txt")

    def test_rejects_read_outside_read_scope(self):
        with self.assertRaises(SandboxViolation):
            self.policy.authorize("workspace://reports/out.txt", "read")

    def test_allows_write_inside_write_scope(self):
        self.assertEqual(self.policy.authorize("workspace://reports/out.txt", "write"), self.root / "reports" / "out.txt")

    def test_rejects_path_traversal(self):
        with self.assertRaises(SandboxViolation):
            self.policy.authorize("workspace://src/../../secrets.txt", "read")

    def test_rejects_absolute_and_unknown_uri(self):
        for uri in ["/etc/passwd", "file:///etc/passwd", "workspace://../secret"]:
            with self.subTest(uri=uri), self.assertRaises(SandboxViolation):
                self.policy.authorize(uri, "read")

    def test_rejects_symlink_escape(self):
        outside = Path(self.tmp.name).parent / (Path(self.tmp.name).name + "-outside")
        outside.mkdir(exist_ok=True)
        link = self.root / "src" / "escape"
        try:
            link.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(SandboxViolation):
                self.policy.authorize("workspace://src/escape/file.txt", "write")
        finally:
            link.unlink(missing_ok=True)
            outside.rmdir()

    def test_redacts_common_secret_patterns(self):
        value = "api_key=sk-abcdefghijklmnopqrstuvwxyz123456 and password: hunter2"
        cleaned = redact_secrets(value)
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz123456", cleaned)
        self.assertNotIn("hunter2", cleaned)
        self.assertIn("[REDACTED]", cleaned)

if __name__ == "__main__":
    unittest.main()
