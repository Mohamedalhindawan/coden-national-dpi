"""A standalone, opt-in CODEN golden Python template, not deployed."""
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "golden-python-service"


class GoldenTemplateTests(unittest.TestCase):
    def test_minimum_self_contained_files_present(self):
        for path in (
            "README.md", "AGENTS.md", "pyproject.toml",
            "coden_service/__init__.py", "coden_service/summary.py",
            "tests/test_summary.py", "docs/PROJECT_SPEC.md",
            "docs/SECURITY_REQUIREMENTS.md", ".github/workflows/ci.yml",
        ):
            with self.subTest(path=path):
                self.assertTrue((TEMPLATE / path).is_file(), path)

    def test_generated_template_ignores_secret_files_and_python_artifacts(self):
        ignore_path = TEMPLATE / ".gitignore"
        self.assertTrue(ignore_path.is_file(), "generated template needs a .gitignore")
        patterns = {
            line.strip() for line in ignore_path.read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        for pattern in (".env", ".env.*", ".venv/", "__pycache__/",
                        "*.py[cod]", ".pytest_cache/", ".coverage", "dist/", "build/"):
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, patterns)

    def test_standalone_template_tests_run_with_stdlib_only(self):
        process = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=TEMPLATE, text=True, capture_output=True, timeout=30, check=False,
        )
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertIn("Ran 6 tests", process.stderr)

    def test_example_import_and_synthetic_task_counts(self):
        command = (
            "from coden_service.summary import summarize;"
            "print(summarize([{'task_id':'demo_1','status':'queued','classification':'synthetic'}]))"
        )
        p = subprocess.run([sys.executable, "-c", command], cwd=TEMPLATE,
                           capture_output=True, text=True, timeout=15)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("'total': 1", p.stdout)
        self.assertIn("'queued': 1", p.stdout)

    def test_ci_is_read_only_and_sha_pinned(self):
        workflow = (TEMPLATE / ".github/workflows/ci.yml").read_text()
        self.assertIn("contents: read", workflow)
        self.assertIn("pull_request:", workflow)
        self.assertNotIn("pull_request_target:", workflow)
        self.assertNotIn("workflow_dispatch:", workflow)
        self.assertNotIn("secrets.", workflow)
        actions = re.findall(r"uses:\s*actions/(?:checkout|setup-python)@([^\s#]+)", workflow)
        self.assertEqual(len(actions), 2)
        self.assertTrue(all(re.fullmatch("[0-9a-f]{40}", action) for action in actions))

    def test_no_external_dependency_or_live_deploy_by_default(self):
        contents = (TEMPLATE / "pyproject.toml").read_text()
        self.assertIn("dependencies = []", contents)
        self.assertNotIn("https://", contents)
        self.assertFalse((TEMPLATE / ".env").exists())
        self.assertFalse((TEMPLATE / "LICENSE").exists())


if __name__ == "__main__":
    unittest.main()
