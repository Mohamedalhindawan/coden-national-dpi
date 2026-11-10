"""Regression tests for the PR inventory graph validator."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pr_dependency_validator", ROOT / "enterprise/governance/pr_dependency_validator.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
validate_inventory = MODULE.validate_inventory


def fixture():
    return {"merge_policy": "human_review_only", "items": [
        {"pr": 37, "url": "https://github.com/Mohamedalhindawan/coden-national-dpi/pull/37", "review": "required", "decision": "pending", "ci": "not_verified_in_this_snapshot", "depends_on": []},
        {"pr": 38, "url": "https://github.com/Mohamedalhindawan/coden-national-dpi/pull/38", "review": "required", "decision": "pending", "ci": "not_verified_in_this_snapshot", "depends_on": [37]},
    ]}


class ValidatorTests(unittest.TestCase):
    def test_repository_inventory(self):
        data = json.loads((ROOT / "enterprise/governance/pr_dependency_review.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_inventory(data), [])

    def test_valid(self):
        self.assertEqual(validate_inventory(fixture()), [])

    def test_non_object(self):
        self.assertTrue(validate_inventory([]))

    def test_duplicate(self):
        x = fixture(); x["items"].append(copy.deepcopy(x["items"][0]))
        self.assertTrue(any("duplicate" in e for e in validate_inventory(x)))

    def test_cycle(self):
        x = fixture(); x["items"][0]["depends_on"] = [38]
        self.assertTrue(any("cycle" in e for e in validate_inventory(x)))

    def test_unknown(self):
        x = fixture(); x["items"][1]["depends_on"] = [999]
        self.assertTrue(any("unknown" in e for e in validate_inventory(x)))

    def test_boolean_id(self):
        x = fixture(); x["items"][0]["pr"] = True
        self.assertTrue(validate_inventory(x))

    def test_implicit_approval(self):
        x = fixture(); x["items"][0]["decision"] = "approved"
        self.assertTrue(any("approval" in e for e in validate_inventory(x)))

    def test_ci_claim(self):
        x = fixture(); x["items"][0]["ci"] = "passed"
        self.assertTrue(any("CI assertion" in e for e in validate_inventory(x)))

    def test_malformed_dependency(self):
        x = fixture(); x["items"][0]["depends_on"] = "38"
        self.assertTrue(validate_inventory(x))


if __name__ == "__main__":
    unittest.main()
