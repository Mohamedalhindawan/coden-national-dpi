"""Fail-closed regression for the actual V4 KPI registry template.

This intentionally does not parse arbitrary YAML or approve a migration.
The template is a placeholder until schema/instance ownership is decided in #55.
"""
from pathlib import Path
import re
import unittest

from enterprise.performance.kpi_preflight import (
    REQUIRED_CANONICAL,
    preflight_kpi_record,
    preflight_kpi_registry,
)

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "enterprise" / "performance" / "kpi-registry.yaml"


class KpiTemplateGateTest(unittest.TestCase):
    def test_real_template_has_no_measured_records(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        # Fail if the known empty placeholder changes: a populated registry
        # needs a reviewed YAML parser and explicit human approval.
        self.assertEqual(len(re.findall(r"(?m)^kpis:\s*\[\s*\]\s*$", text)), 1)
        self.assertIn("empty_template_not_approved",
                      preflight_kpi_registry({"kpis": []}))

    def test_template_fields_require_human_schema_mapping(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        match = re.search(r"(?ms)^required_fields:\s*\n((?:  - [^\n]+\n?)+)", text)
        self.assertIsNotNone(match, "Template field inventory must remain explicit")
        legacy_fields = {
            line.strip()[2:].strip()
            for line in match.group(1).splitlines()
        }
        self.assertIn("id", legacy_fields)
        self.assertNotIn("kpi_id", legacy_fields)
        self.assertTrue(set(REQUIRED_CANONICAL) - legacy_fields)
        sample = {key: "placeholder" for key in legacy_fields}
        errors = preflight_kpi_record(sample)
        self.assertIn("human_mapping_required_id_to_kpi_id", errors)
        self.assertIn("missing_canonical_kpi_id", errors)

    def test_canonical_record_does_not_approve_template(self):
        valid_record = {
            "kpi_id": "kpi-001",
            "objective_id": "obj-001",
            "name": "Synthetic test KPI",
            "unit": "count",
            "baseline": 0,
            "target": 1,
            "direction": "increase",
            "measurement_frequency": "monthly",
            "status": "draft",
            "created_at": "2026-11-11T00:00:00Z",
        }
        self.assertEqual(preflight_kpi_record(valid_record), [])
        self.assertIn("empty_template_not_approved",
                      preflight_kpi_registry({"kpis": []}))


if __name__ == "__main__":
    unittest.main()
