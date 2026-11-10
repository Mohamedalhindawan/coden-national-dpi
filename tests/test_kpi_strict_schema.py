"""Synthetic strict-field and timestamp regression checks against PR #43."""
import copy
import unittest
from enterprise.performance.kpi_preflight import preflight_kpi_record, preflight_kpi_registry
BASE = {"kpi_id": "kpi-001", "objective_id": "obj-001", "name": "Synthetic", "unit": "count", "baseline": 1, "target": 2, "direction": "increase", "measurement_frequency": "monthly", "status": "draft", "created_at": "2026-11-10T00:00:00Z"}
class StrictSchemaTests(unittest.TestCase):
    def test_valid_record(self):
        self.assertEqual([], preflight_kpi_record(BASE))
    def test_timestamp_invalid(self):
        for value in ("2026-11-10", "2026-02-30T12:00:00Z", "2026-11-10T12:00:00", 123, "2026-11-10T00:00:00+99:00"):
            with self.subTest(value=value):
                self.assertIn("invalid_canonical_created_at", preflight_kpi_record(dict(BASE, created_at=value)))
    def test_optional_fields(self):
        self.assertEqual([], preflight_kpi_record(dict(BASE, owner_id="own-1", definition="")))
        for field, value in (("owner_id", "-bad"), ("definition", "x"*2001)):
            self.assertIn("invalid_canonical_"+field, preflight_kpi_record(dict(BASE, **{field:value})))
    def test_unknown_field(self):
        self.assertIn("unknown_canonical_field:invented", preflight_kpi_record(dict(BASE, invented=1)))
    def test_read_only(self):
        record = dict(BASE, invented=1)
        before = copy.deepcopy(record)
        preflight_kpi_registry({"kpis":[record]})
        self.assertEqual(record, before)
    def test_measurement_separation(self):
        problems = preflight_kpi_record(dict(BASE, observed_value=42))
        self.assertIn("measurement_provenance_requires_separate_review", problems)
if __name__ == "__main__":
    unittest.main()
