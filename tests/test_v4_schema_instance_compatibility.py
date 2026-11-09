"""Fail-closed regression checks for issue #55 schema/instance reconciliation.

This does not claim that YAML registries conform to enterprise JSON Schemas.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "enterprise/governance/v4-schema-instance-compatibility.json"


def migration_allowed(entry):
    """No migration unless every required field is mapped and reviewed."""
    return (
        entry.get("migration") == "approved"
        and not entry.get("required_missing")
        and not entry.get("unmapped_values", {})
        and all(value is not None for value in entry.get("field_map", {}).values())
    )


class SchemaInstanceCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MAPPING.read_text(encoding="utf-8"))

    def test_scope_and_draft_status(self):
        self.assertEqual(self.manifest["issue"], 55)
        self.assertEqual(self.manifest["status"], "draft")
        self.assertEqual(set(self.manifest["source_prs"]), {43, 44, 46, 51, 53})

    def test_contracts_are_not_claimed_compatible(self):
        for name in ("risk", "kpi"):
            with self.subTest(contract=name):
                self.assertFalse(migration_allowed(self.manifest["contracts"][name]))
                self.assertEqual(
                    self.manifest["contracts"][name]["migration"],
                    "blocked_pending_human_mapping",
                )

    def test_risk_required_fields_are_explicitly_missing(self):
        risk = self.manifest["contracts"]["risk"]
        self.assertTrue({"initiative_id", "likelihood", "impact", "identified_at"}
                        <= set(risk["required_missing"]))
        self.assertIsNone(risk["field_map"]["status"])
        self.assertIsNone(risk["field_map"]["owner"])
        self.assertIsNone(risk["field_map"]["severity"])

    def test_kpi_missing_contract_fields_are_explicit(self):
        kpi = self.manifest["contracts"]["kpi"]
        self.assertTrue({"objective_id", "unit", "direction", "status", "created_at"}
                        <= set(kpi["required_missing"]))
        self.assertIn("observed_value", kpi["template_only"])
        self.assertEqual(kpi["measurement_pr"], 44)

    def test_approval_flag_alone_cannot_bypass_missing_fields(self):
        for name in ("risk", "kpi"):
            with self.subTest(contract=name):
                record = dict(self.manifest["contracts"][name], migration="approved")
                self.assertFalse(migration_allowed(record))

    def test_complete_reviewed_mapping_can_pass_predicate(self):
        record = {"migration": "approved", "required_missing": [],
                  "unmapped_values": {}, "field_map": {"id": "risk_id"}}
        self.assertTrue(migration_allowed(record))
        record["field_map"]["status"] = None
        self.assertFalse(migration_allowed(record))


if __name__ == "__main__":
    unittest.main()
