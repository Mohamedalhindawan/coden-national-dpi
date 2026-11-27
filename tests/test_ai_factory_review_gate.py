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


class SelfDevelopmentReviewTests(unittest.TestCase):
    def setUp(self):
        import hashlib
        self.original = b"import unittest\n\nclass QueueAlertTests(unittest.TestCase):\n    def test_existing(self):\n        self.assertTrue(True)\n"
        self.candidate = self.original + b"\n    def test_combined(self):\n        self.assertEqual(2, 2)\n"
        self.digest = hashlib.sha256(self.original).hexdigest()

    def assess(self, files, **overrides):
        from ai_factory.review_gate import assess_self_development
        args = dict(task_id="CODEN-SELF-001", base_commit="b"*40,
                    expected_base_commit="b"*40, original=self.original,
                    expected_original_sha256=self.digest, files=files)
        args.update(overrides)
        return assess_self_development(**args)

    def test_single_append_only_test_is_review_candidate_not_execution_permission(self):
        import hashlib
        r = self.assess({"tests/test_factory_queue_alerts.py": self.candidate})
        self.assertEqual(r["status"], "awaiting_human_review")
        self.assertEqual(r["added_test_methods"], 1)
        self.assertEqual(r["candidate_sha256"], hashlib.sha256(self.candidate).hexdigest())
        for key in ("agent_origin_verified", "tests_executed", "execution_authorized",
                    "can_create_pr", "can_merge", "release_authorized"):
            self.assertIs(r[key], False)

    def test_rejects_wrong_scope_and_base_identity(self):
        files = {"tests/test_factory_queue_alerts.py": self.candidate}
        for override in (dict(task_id="OTHER"), dict(base_commit="c"*40),
                         dict(expected_original_sha256="0"*64)):
            with self.subTest(override=override):
                self.assertEqual(self.assess(files, **override)["status"], "blocked")
        for bad in ({}, {"ai_factory/queue_alerts.py": self.candidate},
                    {**files, ".github/workflows/a.yml": b"x"}):
            self.assertEqual(self.assess(bad)["status"], "blocked")

    def test_rejects_removing_tests_or_executable_top_level_and_duplicate_methods(self):
        for candidate in (self.original, self.candidate.replace(b"True", b"False"),
                          self.original + b"\nprint('side effect')\n",
                          self.original + b"\n    def test_existing(self):\n        pass\n",
                          self.original + b"\n    @decorator\n    def test_new(self):\n        pass\n",
                          self.original + b"\n    def test_new(self, x=call()):\n        pass\n",
                          self.original + b"\n    broken syntax\n", b"x"*65537):
            with self.subTest(candidate=candidate[:80]):
                r = self.assess({"tests/test_factory_queue_alerts.py": candidate})
                self.assertEqual(r["status"], "blocked")
                self.assertFalse(r["execution_authorized"])
