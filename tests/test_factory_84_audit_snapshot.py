"""Offline consistency checks for the *dated* 84-source GitHub availability audit.

Never interpret link reachability as admission, security approval or license clearance.
"""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Factory84AuditSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def read(name):
            return json.loads((ROOT / "configs" / name).read_text(encoding="utf-8"))
        cls.audit = read("factory_84_source_availability_audit_2026-11-23.json")
        cls.base = read("factory_72_adopt_first.json")
        cls.r29 = read("factory_r29_only_requirements.json")

    def test_snapshot_covers_every_exact_source_and_not_just_repositories(self):
        expected = {
            row["id"]: (row["upstream_repo"], row["source_url"])
            for row in self.base["candidates"]
        }
        expected.update({
            row["id"]: (row["upstream_repo"], row["url"])
            for row in self.r29["extra_sources"]
        })
        self.assertEqual(len(expected), 84)
        got = {row["id"]: (row["source"], row["url"]) for row in self.audit["entries"]}
        self.assertEqual(got, expected)
        self.assertEqual(len(self.audit["entries"]), 84)
        self.assertEqual(len({v[0].lower() for v in expected.values()}), 76)

    def test_availability_count_does_not_claim_84_integrated_services(self):
        audit = self.audit
        self.assertEqual(audit["distinct_file_links_checked"], 48)
        self.assertEqual(audit["repository_root_links_checked"], 36)
        self.assertEqual(audit["source_admitted_by_this_audit"], 0)
        self.assertEqual(audit["source_installed_by_this_audit"], 0)
        self.assertEqual(audit["source_enabled_by_this_audit"], 0)
        self.assertEqual(audit["missing_independent_license_reviews"], 84)
        self.assertEqual(audit["missing_independent_security_reviews"], 84)
        self.assertEqual(audit["un_pinned_sources"], 84)
        self.assertFalse(audit["paid_usage_authorized"])
        self.assertEqual(audit["source_priorities"], {"P0": 26, "P1": 39, "P2": 19})
        for row in audit["entries"]:
            self.assertTrue(row["reachable_on_date"])
            self.assertIsNone(row["pinned_revision"])
            self.assertFalse(row["installed_by_this_catalog"])
            self.assertFalse(row["approved"])
            self.assertFalse(row["enabled"])

    def test_fixed_links_have_correct_canonical_paths(self):
        by_id = {row["id"]: row for row in self.audit["entries"]}
        self.assertEqual(by_id["source-055"]["source"],
                         "gvisor/gvisor")
        self.assertEqual(by_id["source-062"]["url"],
                         "https://github.com/renovatebot/renovate/blob/HEAD/readme.md")

    def test_all_root_or_file_links_have_bounded_types(self):
        for row in self.audit["entries"]:
            with self.subTest(id=row["id"]):
                self.assertIn(row["link_kind"], {"repository", "file_at_moving_HEAD"})
                if row["link_kind"] == "file_at_moving_HEAD":
                    self.assertIn("/blob/HEAD/", row["url"])
                else:
                    self.assertEqual(row["url"], "https://github.com/" + row["source"])


if __name__ == "__main__":
    unittest.main()
