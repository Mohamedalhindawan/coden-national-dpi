"""CLI regression tests: custom default branch must affect audit classification."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "pr_dependency_audit.py"


class AuditCLITests(unittest.TestCase):
    def run_cli(self, *extra):
        data = [{"number": 1, "head": {"ref": "feature"}, "base": {"ref": "develop"}}]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "pulls.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(SCRIPT), str(path), *extra],
                text=True, capture_output=True, check=False,
            )

    def test_default_main_flags_unresolved(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["independent"], [])
        self.assertEqual(report["unresolved_bases"], [{"pr": 1, "base_ref": "develop"}])

    def test_custom_default_branch_classifies_independent(self):
        result = self.run_cli("--default-branch", "develop")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["independent"], [1])
        self.assertEqual(report["unresolved_bases"], [])

    def test_invalid_default_branch_fails_closed(self):
        result = self.run_cli("--default-branch", " ")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid default branch", result.stderr)


if __name__ == "__main__":
    unittest.main()
