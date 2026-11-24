"""TDD contract: pinned REAL actionlint CLI on GitHub's CPU runner.

A test-only syntax scanner does not count as activation. CI MUST download the
official SHA-256 verified binary, run it, and prove it rejects an invalid file.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "factory-actionlint-p0.yml"
GUIDE = ROOT / "docs" / "FACTORY_ACTIONLINT_ACTIVATION.md"
PIN = "8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8"


class ActionlintP0ActivationTests(unittest.TestCase):
    def test_pinned_binary_is_official_verified_and_never_piped_to_shell(self):
        s = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("actionlint_1.7.12_linux_amd64.tar.gz", s)
        self.assertIn("https://github.com/rhysd/actionlint/releases/download/v1.7.12/", s)
        self.assertIn(PIN, s)
        self.assertIn("sha256sum --check", s)
        self.assertIn("actionlint -version", s)
        self.assertNotRegex(s, r"curl[^\n]*\|\s*(?:bash|sh)")
        self.assertNotIn("go install github.com/rhysd/actionlint", s)
        self.assertNotIn("continue-on-error: true", s)

    def test_real_actionlint_lints_repo_and_negative_fixture(self):
        s = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(".github/workflows/ai-factory-intake-dry-run.yml", s)
        self.assertIn(".github/workflows/factory-actionlint-p0.yml", s)
        self.assertIn("actionlint -oneline", s)
        self.assertIn("bad-workflow.yml", s)
        self.assertIn("expected invalid workflow to fail", s)
        self.assertIn("github.event.pull_request.head.repo.full_name == github.repository", s)
        self.assertIn("permissions:", s)
        self.assertIn("contents: read", s)
        self.assertIn("persist-credentials: false", s)
        self.assertIn("timeout-minutes:", s)
        self.assertNotIn("pull_request_target:", s)

    def test_actionlint_is_present_in_existing_adopt_first_index_not_duplicate(self):
        from ai_factory import factory_84_registry
        row = factory_84_registry.select(factory_84_registry.load(), source_id="source-061")
        self.assertEqual(len(row), 1)
        self.assertEqual(row[0]["upstream_repo"], "rhysd/actionlint")
        self.assertFalse(row[0]["enabled"])
        self.assertFalse(row[0]["approved"])
        self.assertFalse(row[0]["installed"])

    def test_guide_tracks_bounded_proof_not_factory_or_source_approval(self):
        s = GUIDE.read_text(encoding="utf-8")
        self.assertIn("v1.7.12", s)
        self.assertIn(PIN, s)
        self.assertIn("Human review", s)
        self.assertIn("not", s.lower())
        self.assertIn("Draft PR", s)
        self.assertIn("84", s)
        self.assertIn("negative", s.lower())


if __name__ == "__main__":
    unittest.main()
