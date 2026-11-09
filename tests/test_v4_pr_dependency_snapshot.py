"""Offline regression checks for the point-in-time issue #55 PR inventory."""
import json
import re
import unittest
from pathlib import Path

SNAPSHOT = Path(__file__).resolve().parents[1] / "docs/evidence/v4_pr_dependency_snapshot_20261109.json"

class DependencySnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        cls.rows = cls.data["pull_requests"]
        cls.by_number = {r["number"]: r for r in cls.rows}

    def test_unique_numbers(self):
        self.assertEqual(len(self.rows), len(self.by_number))

    def test_sha_format(self):
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{40}", r["head_sha"]) for r in self.rows))

    def test_required_scope(self):
        self.assertEqual(set(self.by_number), {26, *range(37, 55), 56})

    def test_stacked_chain(self):
        self.assertIsNone(self.by_number[37]["depends_on_pr"])
        for number in range(38, 48):
            self.assertEqual(self.by_number[number]["depends_on_pr"], number - 1)

    def test_closed_pr_not_dependency(self):
        self.assertEqual(self.by_number[48]["state"], "closed")
        self.assertFalse(any(r["depends_on_pr"] == 48 for r in self.rows))

    def test_dependencies_resolve_to_active_branch(self):
        for row in self.rows:
            parent = row["depends_on_pr"]
            if parent is not None:
                self.assertEqual(self.by_number[parent]["head"], row["base"])
                self.assertEqual(self.by_number[parent]["state"], "open")

    def test_no_dependency_cycles(self):
        for row in self.rows:
            visited = set()
            current = row
            while current["depends_on_pr"] is not None:
                self.assertNotIn(current["number"], visited)
                visited.add(current["number"])
                current = self.by_number[current["depends_on_pr"]]

if __name__ == "__main__":
    unittest.main()
