"""Fail-closed integrity checks for the PR inventory snapshot; synthetic mutations only.

Run: python -m unittest discover -s tests -p 'test_v4_pr_inventory_integrity.py' -v
"""
import copy
import json
import re
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "docs/reviews/v4-pr-inventory-20261111.json"
SHA40 = re.compile(r"[0-9a-f]{40}\Z")


def validate_inventory(data):
    prs = data["pull_requests"]
    numbers = [p["number"] for p in prs]
    if len(numbers) != len(set(numbers)) or set(numbers) != {26, *range(37, 55)}:
        raise ValueError("missing or duplicate PR number")
    by_number = {p["number"]: p for p in prs}
    heads = {}
    for p in prs:
        if not isinstance(p.get("head_sha"), str) or not SHA40.fullmatch(p["head_sha"]):
            raise ValueError("invalid commit SHA")
        if p["state"] not in ("open", "closed") or p["merged"] and p["state"] != "closed":
            raise ValueError("inconsistent PR state")
        if not p.get("head_ref") or not p.get("base_ref"):
            raise ValueError("missing branch")
        if p["state"] == "open" and p["head_ref"] in heads and heads[p["head_ref"]] != p["number"]:
            raise ValueError("duplicate head branch")
        if p["state"] == "open":
            heads[p["head_ref"]] = p["number"]
    for n in range(38, 48):
        if by_number[n]["base_ref"] != by_number[n-1]["head_ref"]:
            raise ValueError("broken stacked dependency")
    if data.get("status") != "metadata-only-not-merge-approval":
        raise ValueError("inventory cannot grant merge approval")


class PRInventoryIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(FILE.read_text(encoding="utf-8"))

    def test_real_snapshot_contract(self):
        validate_inventory(self.snapshot)

    def test_reject_non_hex_sha(self):
        bad = copy.deepcopy(self.snapshot)
        bad["pull_requests"][0]["head_sha"] = "z" * 40
        with self.assertRaisesRegex(ValueError, "invalid commit SHA"):
            validate_inventory(bad)

    def test_reject_duplicate_head_branch(self):
        bad = copy.deepcopy(self.snapshot)
        bad["pull_requests"][1]["head_ref"] = bad["pull_requests"][0]["head_ref"]
        with self.assertRaisesRegex(ValueError, "duplicate head branch"):
            validate_inventory(bad)

    def test_allow_historical_merged_and_open_pr_sharing_head(self):
        # PR #48 is merged and PR #49 remains open on the same historical head.
        validate_inventory(self.snapshot)

    def test_reject_broken_stacked_parent(self):
        bad = copy.deepcopy(self.snapshot)
        bad["pull_requests"][2]["base_ref"] = "main"
        with self.assertRaisesRegex(ValueError, "broken stacked dependency"):
            validate_inventory(bad)

    def test_reject_false_merge_approval(self):
        bad = copy.deepcopy(self.snapshot)
        bad["status"] = "approved"
        with self.assertRaisesRegex(ValueError, "cannot grant merge approval"):
            validate_inventory(bad)


if __name__ == "__main__":
    unittest.main()
