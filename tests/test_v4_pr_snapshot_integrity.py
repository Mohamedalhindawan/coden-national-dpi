"""Additional fail-closed integrity checks for issue #55's PR inventory.

This is a point-in-time metadata contract, not proof of mergeability or V4 delivery.
"""
import copy
import json
import re
import unittest
from pathlib import Path

SNAPSHOT = Path(__file__).resolve().parents[1] / "docs/evidence/v4_pr_dependency_snapshot_20261109.json"
REPO = "Mohamedalhindawan/coden-national-dpi"
SHA = re.compile(r"[0-9a-f]{40}\Z")


def validate_inventory(data):
    if not isinstance(data, dict):
        raise ValueError("inventory root must be an object")
    if data.get("repository") != REPO or data.get("schema_version") != 1:
        raise ValueError("unexpected inventory provenance")
    rows = data.get("pull_requests")
    if not isinstance(rows, list):
        raise ValueError("pull_requests must be a list")
    if any(not isinstance(row, dict) or not isinstance(row.get("number"), int) or isinstance(row.get("number"), bool) for row in rows):
        raise ValueError("PR rows must be objects with integer numbers")
    numbers = [row["number"] for row in rows]
    if len(numbers) != len(set(numbers)):
        raise ValueError("duplicate PR numbers")
    by_number = {row["number"]: row for row in rows}
    if set(by_number) != {26, *range(37, 55), 56}:
        raise ValueError("incomplete inventory scope")
    active_heads = {}
    for row in rows:
        required = ("state", "draft", "head_sha", "url", "head", "base", "depends_on_pr")
        if any(field not in row for field in required):
            raise ValueError("incomplete PR row")
        if not isinstance(row["head"], str) or not row["head"] or not isinstance(row["base"], str) or not row["base"]:
            raise ValueError("invalid branch name")
        if row["depends_on_pr"] is not None and (not isinstance(row["depends_on_pr"], int) or isinstance(row["depends_on_pr"], bool)):
            raise ValueError("invalid dependency number")
        n = row["number"]
        if row["state"] not in ("open", "closed"):
            raise ValueError("unknown PR state")
        if not isinstance(row["draft"], bool):
            raise ValueError("draft must be boolean")
        if not isinstance(row["head_sha"], str) or not SHA.fullmatch(row["head_sha"]):
            raise ValueError("invalid head SHA")
        if row["url"] != f"https://github.com/{REPO}/pull/{n}":
            raise ValueError("PR URL does not match inventory")
        if row["state"] == "open":
            if row["head"] in active_heads:
                raise ValueError("ambiguous active head branch")
            active_heads[row["head"]] = n
    for row in rows:
        expected_parent = None if row["base"] == "main" else active_heads.get(row["base"])
        if row["depends_on_pr"] != expected_parent:
            raise ValueError("dependency does not match active base branch")
        if row["base"] != "main" and expected_parent is None:
            raise ValueError("unresolved base branch")
        if row["depends_on_pr"] == row["number"]:
            raise ValueError("self dependency")
    for row in rows:
        visited = set()
        current = row
        while current["depends_on_pr"] is not None:
            if current["number"] in visited:
                raise ValueError("dependency cycle")
            visited.add(current["number"])
            current = by_number[current["depends_on_pr"]]


class SnapshotIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))

    def test_rejects_malformed_root(self):
        for payload in (None, [], "invalid", 0, True):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                validate_inventory(payload)

    def test_current_snapshot_integrity(self):
        validate_inventory(self.snapshot)

    def test_rejects_non_object_row(self):
        changed = copy.deepcopy(self.snapshot)
        changed["pull_requests"][0] = None
        with self.assertRaises(ValueError):
            validate_inventory(changed)

    def test_rejects_boolean_pr_number(self):
        changed = copy.deepcopy(self.snapshot)
        changed["pull_requests"][0]["number"] = True
        with self.assertRaises(ValueError):
            validate_inventory(changed)

    def test_rejects_missing_dependency_field(self):
        changed = copy.deepcopy(self.snapshot)
        del changed["pull_requests"][0]["depends_on_pr"]
        with self.assertRaises(ValueError):
            validate_inventory(changed)

    def test_rejects_boolean_dependency(self):
        changed = copy.deepcopy(self.snapshot)
        changed["pull_requests"][1]["depends_on_pr"] = False
        with self.assertRaises(ValueError):
            validate_inventory(changed)

    def test_rejects_forged_pr_url(self):
        changed = copy.deepcopy(self.snapshot)
        changed["pull_requests"][0]["url"] = "https://example.invalid/pull/26"
        with self.assertRaises(ValueError):
            validate_inventory(changed)

    def test_rejects_unresolved_parent(self):
        changed = copy.deepcopy(self.snapshot)
        changed["pull_requests"][1]["base"] = "missing-parent"
        with self.assertRaises(ValueError):
            validate_inventory(changed)

    def test_rejects_duplicate_active_branch(self):
        changed = copy.deepcopy(self.snapshot)
        changed["pull_requests"][1]["head"] = changed["pull_requests"][0]["head"]
        with self.assertRaises(ValueError):
            validate_inventory(changed)

    def test_rejects_mismatched_dependency(self):
        changed = copy.deepcopy(self.snapshot)
        changed["pull_requests"][2]["depends_on_pr"] = None
        with self.assertRaises(ValueError):
            validate_inventory(changed)


if __name__ == "__main__":
    unittest.main()
