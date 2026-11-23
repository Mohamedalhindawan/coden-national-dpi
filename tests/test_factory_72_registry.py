"""Acceptance tests for 72 GitHub-source *candidates* inside CODEN AI Factory.

An indexed component is NOT installed, approved, or executable.
"""
import json
from pathlib import Path
import unittest
from urllib.parse import urlsplit

from ai_factory import adopt_first_registry

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "configs" / "factory_72_adopt_first.json"


class Factory72RegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.items = adopt_first_registry.load_catalog(CATALOG)

    def test_all_72_entries_are_imported_once(self):
        self.assertEqual(len(self.items), 72)
        self.assertEqual(len({row["id"] for row in self.items}), 72)
        self.assertEqual([x["id"] for x in self.items],
                         [f"source-{i:03d}" for i in range(1, 73)])

    def test_every_entry_is_fail_closed_with_no_execution_grants(self):
        self.assertEqual(self.data["registry_status"], "proposed_only")
        self.assertEqual(self.data["manifest_version"], "v2.0")
        self.assertFalse(self.data["auto_install"])
        self.assertFalse(self.data["production_deploy_enabled"])
        self.assertFalse(self.data["paid_usage_enabled"])
        self.assertFalse(self.data["run_unreviewed_components"])
        for row in self.items:
            with self.subTest(row=row["id"]):
                self.assertFalse(row["installed_by_registry"])
                self.assertFalse(row["approved"])
                self.assertFalse(row["enabled"])
                self.assertIsNone(row["pinned_commit"])
                self.assertEqual(row["license_review"], "pending")
                self.assertEqual(row["security_review"], "pending")

    def test_priorities_and_unverified_upstream_provenance(self):
        from collections import Counter
        self.assertEqual(Counter(row["priority"] for row in self.items),
                         {"P0": 23, "P1": 33, "P2": 16})
        for row in self.items:
            parsed = urlsplit(row["source_url"])
            self.assertEqual(parsed.scheme, "https")
            self.assertEqual(parsed.netloc, "github.com")
            self.assertFalse(parsed.username or parsed.password or parsed.query or parsed.fragment)
            self.assertIn(row["upstream_repo"], row["source_url"])
            self.assertEqual(row["source_verification"], "unverified_at_pin")

    def test_requested_projects_are_present_from_correct_upstream(self):
        items = {x["name"] : x for x in self.items}
        expected = {
            "Hermes Agent": "NousResearch/hermes-agent",
            "Hermes Self-Evolution": "NousResearch/hermes-agent-self-evolution",
            "OmniRoute": "cheaper-inference/OmniRoute",
            "FreeLLMAPI — original upstream": "tashfeenahmed/freellmapi",
        }
        for name, repo in expected.items():
            self.assertEqual(items[name]["upstream_repo"], repo)
        self.assertEqual(items["Hermes Self-Evolution"]["priority"], "P2")
        self.assertNotIn("valorisa/FreeLLMAPI", [x["upstream_repo"] for x in self.items])

    def test_query_is_read_only_and_does_not_promote(self):
        p0 = adopt_first_registry.select(self.items, priority="P0")
        self.assertEqual(len(p0), 23)
        hermes = adopt_first_registry.select(self.items, text="hermes")
        self.assertEqual(len(hermes), 2)
        self.assertTrue(all(not x["approved"] for x in hermes))
        with self.assertRaises(ValueError):
            adopt_first_registry.select(self.items, priority="approved")

    def test_rejects_tampered_approval_and_duplicate_ids(self):
        copied = json.loads(json.dumps(self.data))
        copied["candidates"][0]["enabled"] = True
        with self.assertRaises(ValueError):
            adopt_first_registry.validate(copied)
        copied = json.loads(json.dumps(self.data))
        copied["candidates"][1]["id"] = copied["candidates"][0]["id"]
        with self.assertRaises(ValueError):
            adopt_first_registry.validate(copied)

    def test_rejects_unsafe_or_unpinned_auto_install_metadata(self):
        copied = json.loads(json.dumps(self.data))
        copied["candidates"][0]["source_url"] = "https://evil.example.com/tool"
        with self.assertRaises(ValueError):
            adopt_first_registry.validate(copied)
        copied = json.loads(json.dumps(self.data))
        copied["auto_install"] = True
        with self.assertRaises(ValueError):
            adopt_first_registry.validate(copied)


if __name__ == "__main__":
    unittest.main()
