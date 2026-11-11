"""Synthetic registry boundary tests; no citizen or production records.

These tests protect fail-closed preflight behavior while schema ownership remains
unresolved in issue #55. They do not approve registry migration.
"""
import copy
import math
import unittest

from enterprise.performance.kpi_preflight import preflight_kpi_registry


def synthetic(identifier="kpi-001"):
    return {
        "kpi_id": identifier,
        "objective_id": "obj-001",
        "name": "Synthetic KPI",
        "unit": "count",
        "baseline": 0,
        "target": 1,
        "direction": "increase",
        "measurement_frequency": "monthly",
        "status": "draft",
        "created_at": "2026-11-11T00:00:00Z",
    }


class RegistryBoundaryTests(unittest.TestCase):
    def test_duplicate_identifiers_are_rejected_at_second_index(self):
        registry = {"kpis": [synthetic(), synthetic()]}
        before = copy.deepcopy(registry)
        self.assertEqual(
            preflight_kpi_registry(registry),
            ["kpis[1]:duplicate_kpi_id"],
        )
        self.assertEqual(registry, before)

    def test_distinct_identifiers_are_accepted_without_approval_side_effect(self):
        registry = {"kpis": [synthetic("kpi-001"), synthetic("kpi-002")]}
        self.assertEqual(preflight_kpi_registry(registry), [])

    def test_nonfinite_values_are_rejected_without_crashing(self):
        for invalid in (math.nan, math.inf, -math.inf):
            with self.subTest(value=repr(invalid)):
                record = synthetic()
                record["target"] = invalid
                self.assertIn(
                    "kpis[0]:invalid_numeric_target",
                    preflight_kpi_registry({"kpis": [record]}),
                )

    def test_non_string_mapping_key_is_rejected_deterministically(self):
        record = synthetic()
        record[7] = "synthetic"
        self.assertIn(
            "kpis[0]:non_string_canonical_field_key",
            preflight_kpi_registry({"kpis": [record]}),
        )

    def test_legacy_identifier_requires_human_mapping(self):
        record = synthetic()
        record["id"] = record.pop("kpi_id")
        diagnostics = preflight_kpi_registry({"kpis": [record]})
        self.assertIn("kpis[0]:human_mapping_required_id_to_kpi_id", diagnostics)
        self.assertIn("kpis[0]:missing_canonical_kpi_id", diagnostics)


if __name__ == "__main__":
    unittest.main()
