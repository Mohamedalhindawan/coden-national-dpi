"""Regression tests: oversized Python integers must not crash KPI preflight."""
import unittest

from enterprise.performance.kpi_preflight import preflight_kpi_record, preflight_kpi_registry


class HugeIntegerKpiTest(unittest.TestCase):
    def test_huge_baseline_fails_closed(self):
        result = preflight_kpi_record({"baseline": 10 ** 1000})
        self.assertIn("invalid_numeric_baseline", result)

    def test_huge_negative_target_fails_closed(self):
        result = preflight_kpi_record({"target": -(10 ** 1000)})
        self.assertIn("invalid_numeric_target", result)

    def test_registry_returns_diagnostic_not_exception(self):
        result = preflight_kpi_registry({"kpis": [{"kpi_id": "kpi-001", "baseline": 10 ** 1000}]})
        self.assertIn("kpis[0]:invalid_numeric_baseline", result)

    def test_regular_finite_numbers_are_accepted(self):
        result = preflight_kpi_record({"baseline": 0, "target": 12.5})
        self.assertNotIn("invalid_numeric_baseline", result)
        self.assertNotIn("invalid_numeric_target", result)


if __name__ == "__main__":
    unittest.main()
