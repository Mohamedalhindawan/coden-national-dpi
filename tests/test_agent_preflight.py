"""Tests for the local agent preflight tool; uses synthetic strings only."""
import unittest

from tools.agent_preflight import (
    CheckResult,
    is_disallowed_env_file,
    is_skipped_path,
    scan_text,
    summarise,
)


class SecretScannerTests(unittest.TestCase):
    def test_clean_text_has_no_findings(self):
        text = "Synthetic demo data only.\nNo credentials here.\n"
        self.assertEqual(scan_text(text, "docs/example.md"), [])

    def test_common_key_shapes_are_reported_without_the_value(self):
        token = "sk-" + ("a" * 24)
        findings = scan_text(f"first line\nkey = {token}\n", "app/config.js")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].path, "app/config.js")
        self.assertEqual(findings[0].line, 2)
        self.assertEqual(findings[0].label, "OpenAI-style API key")
        self.assertNotIn(token, str(findings[0]))

    def test_multiple_secret_shapes_and_line_numbers(self):
        github_token = "ghp_" + ("b" * 30)
        aws_key = "AKIA" + "C" * 16
        text = f"{github_token}\n\naws={aws_key}\n"
        findings = scan_text(text, ".github/workflows/example.yml")
        self.assertEqual([finding.line for finding in findings], [1, 3])
        self.assertEqual(
            [finding.label for finding in findings],
            ["GitHub personal access token", "AWS access key ID"],
        )
        rendered = "\n".join(str(finding) for finding in findings)
        self.assertNotIn(github_token, rendered)
        self.assertNotIn(aws_key, rendered)

    def test_private_key_header_is_detected(self):
        header = "-----BEGIN " + "RSA PRIVATE KEY-----"
        findings = scan_text(header, "notes.txt")
        self.assertEqual([finding.label for finding in findings], ["private key block"])

    def test_generated_and_dependency_directories_are_skipped(self):
        for path in ("node_modules/pkg/index.js", ".venv/lib/python3.12/x.py", "artifacts/shot.png"):
            with self.subTest(path=path):
                self.assertTrue(is_skipped_path(path))
        for path in ("tools/agent_preflight.py", "tests/test_agent_preflight.py", "docs/artifacts.md"):
            with self.subTest(path=path):
                self.assertFalse(is_skipped_path(path))

    def test_tracked_env_files_are_rejected_except_templates(self):
        for path in (".env", ".env.local", "app/.env", ".env.production"):
            with self.subTest(path=path):
                self.assertTrue(is_disallowed_env_file(path))
        for path in (".env.example", ".env.sample", ".env.template", "config/.env.example"):
            with self.subTest(path=path):
                self.assertFalse(is_disallowed_env_file(path))

    def test_summary_reports_overall_status(self):
        passed = [
            CheckResult("Secret scan", True, "0 findings"),
            CheckResult("Tests", True, "22 tests"),
        ]
        failed = passed + [CheckResult("OpenAPI", False, "validator missing")]
        self.assertTrue(summarise(passed).startswith("PASS"))
        self.assertIn("2/2", summarise(passed))
        self.assertTrue(summarise(failed).startswith("FAIL"))
        self.assertIn("2/3", summarise(failed))
        self.assertIn("OpenAPI", summarise(failed))


if __name__ == "__main__":
    unittest.main()
