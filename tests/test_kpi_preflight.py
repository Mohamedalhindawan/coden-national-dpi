import copy
import unittest
from enterprise.performance.kpi_preflight import preflight_kpi_record, preflight_kpi_registry


class KpiPreflightTests(unittest.TestCase):
    def test_empty_template_is_not_approved(self):
        self.assertEqual(preflight_kpi_registry({"status": "draft", "kpis": []}), ["empty_template_not_approved"])

    def test_invalid_registry_type(self):
        self.assertEqual(preflight_kpi_registry([]), ["registry_not_object"])
        self.assertEqual(preflight_kpi_registry({"kpis": {}}), ["kpis_not_list"])

    def test_draft_record_fails_closed(self):
        record = {"id": "kpi-1", "name": "Test", "baseline": None, "status": "draft"}
        snapshot = copy.deepcopy(record)
        result = preflight_kpi_record(record)
        self.assertIn("human_mapping_required_id_to_kpi_id", result)
        self.assertIn("missing_canonical_objective_id", result)
        self.assertIn("missing_canonical_baseline", result)
        self.assertEqual(record, snapshot)

    def test_unknown_enums_and_bool_numeric_rejected(self):
        result = preflight_kpi_record({"direction": "up", "measurement_frequency": "sometimes", "status": "approved", "baseline": True, "target": "10"})
        for code in ("invalid_canonical_direction", "invalid_canonical_measurement_frequency", "invalid_canonical_status", "invalid_numeric_baseline", "invalid_numeric_target"):
            self.assertIn(code, result)

    def test_unhashable_enum_is_rejected_without_exception(self):
        self.assertIn("invalid_canonical_status", preflight_kpi_record({"status": []}))

    def test_provenance_not_silently_promoted(self):
        self.assertIn("measurement_provenance_requires_separate_review", preflight_kpi_record({"observed_value": 7}))

    def test_canonical_synthetic_record_has_no_preflight_diagnostics(self):
        record = {"kpi_id": "kpi-001", "objective_id": "obj-001", "name": "Synthetic", "unit": "count", "baseline": 1, "target": 2, "direction": "increase", "measurement_frequency": "monthly", "status": "draft", "created_at": "2026-11-10T00:00:00Z"}
        self.assertEqual(preflight_kpi_registry({"kpis": [record]}), [])

    def test_nonobject_record_is_rejected(self):
        self.assertEqual(preflight_kpi_registry({"kpis": [None]}), ["kpis[0]:record_not_object"])


if __name__ == "__main__":
    unittest.main()
