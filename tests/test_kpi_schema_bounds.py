"""Synthetic checks against identifier and text bounds in PR #43 KPI schema."""
import copy
import unittest
from enterprise.performance.kpi_preflight import preflight_kpi_record, preflight_kpi_registry

BASE = {"kpi_id": "kpi-001", "objective_id": "obj-001", "name": "Synthetic", "unit": "count", "baseline": 1, "target": 2, "direction": "increase", "measurement_frequency": "monthly", "status": "draft", "created_at": "2026-11-10T00:00:00Z"}


class KpiSchemaBoundsTests(unittest.TestCase):
    def test_valid_synthetic_record(self):
        self.assertEqual([], preflight_kpi_record(BASE))

    def test_identifier_pattern_and_lengths(self):
        for field in ("kpi_id", "objective_id"):
            for bad in ("a", "bad id", "-invalid", "x" * 101, [], 23):
                with self.subTest(field=field, bad=repr(bad)):
                    self.assertIn("invalid_canonical_" + field, preflight_kpi_record(dict(BASE, **{field: bad})))

    def test_name_and_unit_bounds(self):
        for field, bad in (("name", "ab"), ("name", "x" * 161), ("unit", "x" * 41), ("unit", [])):
            with self.subTest(field=field):
                self.assertIn("invalid_canonical_" + field, preflight_kpi_record(dict(BASE, **{field: bad})))

    def test_registry_fails_closed_and_remains_read_only(self):
        source = {"kpis": [dict(BASE, kpi_id="bad id")]}
        before = copy.deepcopy(source)
        self.assertIn("kpis[0]:invalid_canonical_kpi_id", preflight_kpi_registry(source))
        self.assertEqual(source, before)


if __name__ == "__main__":
    unittest.main()
