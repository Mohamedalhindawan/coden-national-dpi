"""Offline metadata contract tests. Run: python -m unittest discover -s tests -p 'test_v4_pr_inventory.py'"""
import json
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "docs/reviews/v4-pr-inventory-20261111.json"

class PRInventoryContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(FILE.read_text(encoding="utf-8"))
        cls.prs = {p["number"]: p for p in cls.data["pull_requests"]}

    def test_required_scope_and_uniqueness(self):
        numbers = [p["number"] for p in self.data["pull_requests"]]
        self.assertEqual(len(numbers), len(set(numbers)))
        self.assertEqual(set(numbers), {26, *range(37, 55)})

    def test_metadata_shape(self):
        for p in self.prs.values():
            self.assertIn(p["state"], {"open", "closed"})
            self.assertEqual(len(p["head_sha"]), 40)
            self.assertTrue(p["base_ref"] and p["head_ref"])

    def test_merged_state(self):
        self.assertEqual([n for n, p in self.prs.items() if p["merged"]], [48])

    def test_stacked_base_dependencies(self):
        for n in range(38, 48):
            self.assertEqual(self.prs[n]["base_ref"], self.prs[n - 1]["head_ref"])

    def test_no_unverified_approval(self):
        self.assertEqual(self.data["status"], "metadata-only-not-merge-approval")

if __name__ == "__main__":
    unittest.main()
