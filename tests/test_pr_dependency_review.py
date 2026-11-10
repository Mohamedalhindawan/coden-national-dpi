"""Fail-closed structural tests for the issue #55 PR review inventory."""
import json
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "enterprise" / "governance" / "pr_dependency_review.json"

class DependencyReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(FILE.read_text(encoding="utf-8"))

    def test_unique_prs_and_required_scope(self):
        ids = [x["pr"] for x in self.data["items"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue({26, 29, *range(37, 48), *range(49, 55), *range(80, 87)}.issubset(set(ids)))

    def test_dependencies_are_acyclic_and_present(self):
        nodes = {x["pr"]: x for x in self.data["items"]}
        for n, x in nodes.items():
            for parent in x["depends_on"]:
                self.assertIn(parent, nodes)
                self.assertLess(parent, n)

    def test_no_implicit_approvals(self):
        self.assertEqual(self.data["merge_policy"], "human_review_only")
        for x in self.data["items"]:
            self.assertEqual(x["review"], "required")
            self.assertEqual(x["decision"], "pending")
            self.assertNotEqual(x["ci"], "passed")

    def test_links_and_overlap_coverage(self):
        ids = {x["pr"] for x in self.data["items"]}
        for x in self.data["items"]:
            self.assertEqual(x["url"], f"https://github.com/Mohamedalhindawan/coden-national-dpi/pull/{x['pr']}")
        for x in self.data["overlap_reviews"]:
            self.assertTrue(set(x["prs"]).issubset(ids))

if __name__ == "__main__":
    unittest.main()
