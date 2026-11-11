"""Fail-closed review gate for synthetic PR handoff metadata."""
import unittest
from ai_factory.review_gate import assess_pr_handoff


class ReviewGateTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {
            "proposal_only": True,
            "source": "synthetic_demo",
            "files": ["demo-task.txt"],
            "github_write_permitted": False,
            "pull_request_created": False,
            "requires_human_review": True,
        }

    def test_valid_preview_remains_blocked_for_automatic_pr(self):
        result = assess_pr_handoff(self.manifest)
        self.assertEqual(result["status"], "awaiting_human_review")
        self.assertFalse(result["can_create_pr"])
        self.assertFalse(result["can_merge"])

    def test_rejects_unsafe_file(self):
        bad = dict(self.manifest, files=["../../secrets"])
        self.assertEqual(assess_pr_handoff(bad)["status"], "blocked")

    def test_rejects_claimed_write_authority(self):
        bad = dict(self.manifest, github_write_permitted=True)
        self.assertEqual(assess_pr_handoff(bad)["status"], "blocked")

    def test_rejects_missing_fields(self):
        self.assertEqual(assess_pr_handoff({})["status"], "blocked")
        self.assertEqual(assess_pr_handoff(None)["status"], "blocked")

    def test_rejects_extra_unreviewed_files(self):
        bad = dict(self.manifest, files=["demo-task.txt", ".github/workflows/evil.yml"])
        self.assertEqual(assess_pr_handoff(bad)["status"], "blocked")
