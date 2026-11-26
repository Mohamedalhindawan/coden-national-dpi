"""TDD contract: query all 84 source candidates safely INSIDE CODEN ai_factory.

This is a read-only union of the existing 72 catalog, R29's 12, and the
dated availability snapshot. Passing does NOT approve or install 84 tools.
"""
import copy
import json
from collections import Counter
from pathlib import Path
import unittest

from ai_factory import factory_84_registry

ROOT = Path(__file__).resolve().parents[1] / "configs"


def fixture(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class Factory84UnifiedRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = fixture("factory_72_adopt_first.json")
        cls.r29 = fixture("factory_r29_only_requirements.json")
        cls.audit = fixture("factory_84_source_availability_audit_2026-11-23.json")

    def test_full_84_registry_is_indexed_without_installing_anything(self):
        rows = factory_84_registry.load()
        self.assertEqual(len(rows), 84)
        self.assertEqual(len({x["id"] for x in rows}), 84)
        self.assertEqual(len({x["upstream_repo"].casefold() for x in rows}), 76)
        self.assertEqual(
            dict(Counter(x["priority"] for x in rows)),
            {"P0": 26, "P1": 39, "P2": 19},
        )
        self.assertEqual([x["id"] for x in rows[:72]],
                         [f"source-{i:03d}" for i in range(1, 73)])
        self.assertEqual([x["id"] for x in rows[72:]],
                         [f"r29-{i:02d}" for i in range(1, 13)])
        for item in rows:
            self.assertEqual(item["admission"], "proposed_only")
            self.assertFalse(item["enabled"])
            self.assertFalse(item["approved"])
            self.assertFalse(item["installed"])
            self.assertIsNone(item["pinned_commit"])
            self.assertEqual(item["license_review"], "pending")
            self.assertEqual(item["security_review"], "pending")
            self.assertTrue(item["source_url"].startswith("https://github.com/"))

    def test_requirement_links_come_from_existing_r29_and_not_invention(self):
        rows = factory_84_registry.load()
        source_map = {x["id"]: x for x in rows}
        self.assertIn("ADD-13", source_map["r29-03"]["required_by"])
        self.assertIn("ADD-13", source_map["source-001"]["required_by"])
        self.assertEqual(source_map["r29-03"]["wave"], "W2")
        self.assertIn("W1", source_map["r29-03"]["requirement_waves"])
        self.assertEqual(source_map["source-001"]["wave"], None)
        self.assertEqual(len(self.r29["requirements"]), 47)

    def test_explicitly_requested_upstreams_are_present_and_disabled(self):
        rows = factory_84_registry.load()
        repos = {x["upstream_repo"] for x in rows}
        for name in (
            "NousResearch/hermes-agent", "NousResearch/hermes-agent-self-evolution",
            "cheaper-inference/OmniRoute", "tashfeenahmed/freellmapi",
            "devcontainers/templates", "fastapi/full-stack-fastapi-template",
            "SWE-bench/SWE-bench", "sigstore/rekor",
        ):
            self.assertIn(name, repos)
        self.assertEqual(len(factory_84_registry.select(rows, priority="P0")), 26)
        self.assertEqual(len(factory_84_registry.select(rows, requires="ADD-13")), 4)

    def test_query_by_source_id_name_requirement_and_wave(self):
        rows = factory_84_registry.load()
        self.assertEqual(factory_84_registry.select(rows, source_id="r29-03")[0]["upstream_repo"],
                         "fastapi/full-stack-fastapi-template")
        self.assertEqual(len(factory_84_registry.select(rows, text="freellmapi")), 1)
        self.assertGreater(len(factory_84_registry.select(rows, wave="W0")), 0)
        with self.assertRaises(ValueError):
            factory_84_registry.select(rows, wave="W9")
        with self.assertRaises(ValueError):
            factory_84_registry.select(rows, requires="ADD-99")
        with self.assertRaises(ValueError):
            factory_84_registry.select(rows, source_id="../credentials")

    def test_rejects_admission_tamper_and_snapshot_drift(self):
        cases = [
            ("base", "candidates", 0, "enabled", True),
            ("base", "candidates", 0, "pinned_commit", "abc"),
            ("r29", "extra_sources", 0, "installed", True),
            ("r29", "extra_sources", 1, "approved", True),
            ("audit", "entries", 0, "enabled", True),
            ("audit", "entries", 0, "url", "https://elsewhere.example/remote.py"),
        ]
        for section, key, number, field, value in cases:
            with self.subTest(section=section, field=field):
                data = {name: copy.deepcopy(getattr(self, name))
                        for name in ("base", "r29", "audit")}
                data[section][key][number][field] = value
                with self.assertRaises(ValueError):
                    factory_84_registry.build_view(
                        data["base"], data["r29"], data["audit"]
                    )

    def test_cannot_hide_new_or_missing_sources(self):
        data = {name: copy.deepcopy(getattr(self, name))
                for name in ("base", "r29", "audit")}
        data["audit"]["entries"].pop()
        with self.assertRaises(ValueError):
            factory_84_registry.build_view(data["base"], data["r29"], data["audit"])
        data = {name: copy.deepcopy(getattr(self, name))
                for name in ("base", "r29", "audit")}
        data["audit"]["source_enabled_by_this_audit"] = 1
        with self.assertRaises(ValueError):
            factory_84_registry.build_view(data["base"], data["r29"], data["audit"])


    def test_v1_1_repository_index_is_queryable_and_never_admits(self):
        rows = factory_84_registry.load_v1_1()
        self.assertEqual(len(rows), 128)
        self.assertEqual(len({r["repository"].casefold() for r in rows}), 128)
        self.assertEqual(sum(len(r["legacy_entry_ids"]) for r in rows), 84)
        self.assertEqual(sum(len(r["plan_references"]) for r in rows), 89)
        self.assertTrue(all(r["approved"] is False and r["enabled"] is False
                            and r["installed_by_this_catalog"] is False for r in rows))
        self.assertEqual(factory_84_registry.select_v1_1(rows, "autogen")[0]["decision"],
                         "hold_archived")
        self.assertEqual(len(factory_84_registry.select_v1_1(rows, "omniroute")), 1)

    def test_v1_1_index_rejects_modified_bytes_and_symlink(self):
        import tempfile
        from unittest.mock import patch
        raw = (ROOT / "factory_v1_1_repository_reconciliation.json").read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.json"
            path.write_bytes(raw + b" ")
            with patch.object(factory_84_registry, "V1_1", path):
                with self.assertRaises(ValueError):
                    factory_84_registry.load_v1_1()
            path.write_bytes(raw)
            alias = Path(tmp) / "alias.json"
            alias.symlink_to(path)
            with patch.object(factory_84_registry, "V1_1", alias):
                with self.assertRaises(ValueError):
                    factory_84_registry.load_v1_1()


    def test_gateway_review_index_links_six_candidates_without_activation(self):
        rows = factory_84_registry.load_gateway_review()
        self.assertEqual(len(rows), 6)
        self.assertEqual(dict(Counter(r["role"] for r in rows)),
                         {"agent_orchestration": 1, "model_gateway": 3, "mcp": 2})
        for row in rows:
            self.assertEqual(row["discovery_decision"], "proposed_only")
            self.assertFalse(row["approved"])
            self.assertFalse(row["enabled"])
            self.assertFalse(row["installed"])
            self.assertEqual(row["integration_test"], "not_run")
        self.assertEqual(len([r for r in rows if r["repository"].endswith("OmniRoute")]), 1)

    def test_gateway_review_index_rejects_tampered_bytes(self):
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review.json"
            data = fixture("factory_v1_1_gateway_mcp_review.json")
            data["entries"][0]["enabled"] = True
            path.write_text(json.dumps(data), encoding="utf-8")
            with patch.object(factory_84_registry, "GATEWAY_REVIEW", path):
                with self.assertRaises(ValueError):
                    factory_84_registry.load_gateway_review()


if __name__ == "__main__":
    unittest.main()
