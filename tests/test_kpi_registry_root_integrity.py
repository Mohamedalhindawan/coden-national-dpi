"""Synthetic, read-only KPI registry root integrity regression."""
import copy
import unittest

from enterprise.performance.kpi_preflight import preflight_kpi_registry


def synthetic():
    return {
        "kpi_id": "kpi-001",
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


class RootIntegrityTests(unittest.TestCase):
    def test_valid_root_accepted_without_mutation(self):
        payload = {"kpis": [synthetic()]}
        before = copy.deepcopy(payload)
        self.assertEqual(preflight_kpi_registry(payload), [])
        self.assertEqual(payload, before)

    def test_unknown_root_key_rejected(self):
        payload = {"kpis": [synthetic()], "approved": True}
        self.assertEqual(preflight_kpi_registry(payload), ["unknown_registry_root_field"])

    def test_non_string_root_key_rejected(self):
        payload = {"kpis": [synthetic()], 42: "synthetic"}
        self.assertEqual(preflight_kpi_registry(payload), ["non_string_registry_root_key"])

    def test_missing_kpis_still_rejected(self):
        self.assertIn("kpis_not_list", preflight_kpi_registry({}))


if __name__ == "__main__":
    unittest.main()
