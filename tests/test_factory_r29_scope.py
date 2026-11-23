"""R29 source-grounded factory-only requirement/catalog acceptance tests."""
import json
from pathlib import Path
import unittest

from ai_factory import r29_factory_scope

BASE = Path(__file__).resolve().parents[1]
R29 = BASE / "configs/factory_r29_only_requirements.json"
OLD = BASE / "configs/factory_72_adopt_first.json"


class R29FactoryScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r29 = r29_factory_scope.load(R29)
        cls.old = json.loads(OLD.read_text(encoding="utf-8"))

    def test_factory_only_47_of_52_extensions_with_original_r29_waves(self):
        data = self.r29
        self.assertEqual(len(data["requirements"]), 47)
        ids = [x["id"] for x in data["requirements"]]
        self.assertEqual(len(set(ids)), 47)
        excluded = {f"ADD-{n:02d}" for n in (32, 33, 34, 36, 40)}
        self.assertFalse(excluded.intersection(ids))
        self.assertEqual(len(ids) + len(excluded), 52)
        from collections import Counter
        self.assertEqual(dict(Counter(x["wave"] for x in data["requirements"])),
                         {"W0": 19, "W1": 12, "W2": 5, "W3": 8, "W4": 3})
        self.assertEqual(data["scope"], "CODEN_AI_FACTORY_ONLY")
        self.assertEqual(data["document_status"], "UNAPPROVED")
        self.assertEqual(data["execution_status"], "not_proven_by_blueprint")

    def test_requirements_link_only_recorded_existing_source_ids(self):
        baseline = {x["id"] for x in self.old["candidates"]}
        additions = {x["id"] for x in self.r29["extra_sources"]}
        for req in self.r29["requirements"]:
            self.assertTrue(req["title"])
            self.assertIsInstance(req["acceptance"], str)
            self.assertTrue(req["acceptance"].strip())
            self.assertTrue(req["linked_sources"])
            self.assertTrue(set(req["linked_sources"]) <= baseline | additions)
            self.assertFalse(req["implemented_by_import"])
            self.assertFalse(req["tested_by_blueprint"])
        self.assertEqual(len(self.old["candidates"]), 72)

    def test_only_12_additive_missing_git_sources_and_no_install(self):
        extra = self.r29["extra_sources"]
        self.assertEqual(len(extra), 12)
        self.assertEqual([x["id"] for x in extra], [f"r29-{i:02d}" for i in range(1, 13)])
        existing_repos = {x["upstream_repo"].lower() for x in self.old["candidates"]}
        for item in extra:
            self.assertNotIn(item["upstream_repo"].lower(), existing_repos)
            self.assertEqual(item["url"], "https://github.com/" + item["upstream_repo"])
            self.assertFalse(item["installed"])
            self.assertFalse(item["enabled"])
            self.assertFalse(item["approved"])
            self.assertIsNone(item["pinned_commit"])
            self.assertEqual(item["license_review"], "pending")
        self.assertEqual(72 + len(extra), 84)

    def test_blueprint_gates_and_evidence_pilots(self):
        self.assertEqual([x["id"] for x in self.r29["gates"]],
                         ["G0","G1","G2","G3","G4","G5","G6","G8"])
        self.assertEqual([x["id"] for x in self.r29["reference_tests"]],
                         [f"T{i:02d}" for i in range(1, 11)] + ["T12"])
        self.assertEqual([x["id"] for x in self.r29["pilots"]],
                         [f"PILOT-{i:02d}" for i in range(1, 6)])
        self.assertEqual(self.r29["excluded_scenario"], "T11")
        self.assertEqual(self.r29["excluded_gate"], "G7")

    def test_can_only_query_read_only_inventory_and_no_spend(self):
        subset = r29_factory_scope.filter_requirements(self.r29["requirements"], wave="W2")
        self.assertEqual(len(subset), 5)
        self.assertTrue(all(x["wave"] == "W2" for x in subset))
        self.assertFalse(self.r29["auto_install"])
        self.assertFalse(self.r29["automatic_merge"])
        self.assertFalse(self.r29["paid_calls"])
        with self.assertRaises(ValueError):
            r29_factory_scope.filter_requirements(self.r29["requirements"], wave="W9")

    def test_tampering_with_permissions_is_denied(self):
        for field in ("auto_install", "automatic_merge", "paid_calls"):
            bad = json.loads(json.dumps(self.r29))
            bad[field] = True
            with self.assertRaises(ValueError):
                r29_factory_scope.validate(bad, baseline=self.old)
        bad = json.loads(json.dumps(self.r29))
        bad["requirements"][0]["implemented_by_import"] = True
        with self.assertRaises(ValueError):
            r29_factory_scope.validate(bad, baseline=self.old)


if __name__ == "__main__":
    unittest.main()
