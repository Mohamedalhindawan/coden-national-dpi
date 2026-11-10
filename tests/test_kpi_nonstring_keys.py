"""Regression tests for malformed mapping keys in KPI preflight."""
import unittest

from enterprise.performance.kpi_preflight import preflight_kpi_record, preflight_kpi_registry


class NonStringKpiKeysTest(unittest.TestCase):
    def test_mixed_keys_fail_closed_without_exception(self):
        diagnostics = preflight_kpi_record({42: "bad", "unexpected": 1})
        self.assertIn("non_string_canonical_field_key", diagnostics)
        self.assertIn("unknown_canonical_field:unexpected", diagnostics)

    def test_nonstring_key_in_registry_fails_closed(self):
        diagnostics = preflight_kpi_registry({"kpis": [{42: "bad", "kpi_id": "kpi-123"}]})
        self.assertIn("kpis[0]:non_string_canonical_field_key", diagnostics)

    def test_unknown_string_keys_stay_deterministic(self):
        diagnostics = preflight_kpi_record({"zeta": 1, "alpha": 2})
        self.assertEqual([x for x in diagnostics if x.startswith("unknown_canonical_field:")],
                         ["unknown_canonical_field:alpha", "unknown_canonical_field:zeta"])


if __name__ == "__main__":
    unittest.main()
