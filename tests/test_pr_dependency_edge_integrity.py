"""Regression tests for ambiguous PR dependencies and overlap references."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validator", ROOT / "enterprise/governance/pr_dependency_validator.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def inventory():
    return {"merge_policy": "human_review_only", "items": [
        {"pr": n, "url": f"https://github.com/Mohamedalhindawan/coden-national-dpi/pull/{n}", "review": "required", "decision": "pending", "ci": "not_verified_in_this_snapshot", "depends_on": deps}
        for n, deps in ((37, []), (38, [37]))
    ], "overlap_reviews": [{"prs": [37, 38], "topic": "schema review"}]}


class EdgeIntegrityTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(module.validate_inventory(inventory()), [])

    def test_duplicate_dependency(self):
        data = inventory(); data["items"][1]["depends_on"] = [37, 37]
        self.assertTrue(any("duplicate dependency" in e for e in module.validate_inventory(data)))

    def test_invalid_overlap_pr(self):
        data = inventory(); data["overlap_reviews"][0]["prs"] = [37, 999]
        self.assertTrue(any("unknown PR" in e for e in module.validate_inventory(data)))

    def test_duplicate_overlap_pr(self):
        data = inventory(); data["overlap_reviews"][0]["prs"] = [37, 37]
        self.assertTrue(any("duplicate PR" in e for e in module.validate_inventory(data)))

    def test_noncanonical_overlap_id(self):
        data = inventory(); data["overlap_reviews"][0]["prs"] = [37, True]
        self.assertTrue(any("invalid PR" in e for e in module.validate_inventory(data)))

    def test_invalid_overlap_structure(self):
        data = inventory(); data["overlap_reviews"] = "not-a-list"
        self.assertTrue(any("overlap_reviews" in e for e in module.validate_inventory(data)))

    def test_missing_overlap_topic(self):
        data = inventory(); data["overlap_reviews"][0]["topic"] = " "
        self.assertTrue(any("topic" in e for e in module.validate_inventory(data)))


if __name__ == "__main__":
    unittest.main()
