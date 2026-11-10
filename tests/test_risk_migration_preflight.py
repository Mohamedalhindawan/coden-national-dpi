"""Synthetic tests for fail-closed #55 risk migration preflight."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / "enterprise/risk/risk_migration_preflight.py"
spec = importlib.util.spec_from_file_location("risk_migration_preflight", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
preflight_risk_record = module.preflight_risk_record


class TestRiskPreflight(unittest.TestCase):
    def test_open_status_never_auto_mapped(self):
        errors = preflight_risk_record({
            "id": "RISK-001", "title": "Example", "description": "Synthetic risk",
            "status": "open", "severity": "high", "owner": "unassigned",
        })
        self.assertIn("human_mapping_required_status", errors)
        self.assertIn("human_mapping_required_likelihood", errors)
        self.assertIn("human_mapping_required_impact", errors)
        self.assertIn("owner_unassigned", errors)

    def test_missing_description_is_detected(self):
        self.assertIn("missing_source_description",
                      preflight_risk_record({"id": "RISK-002", "title": "Example"}))

    def test_rejects_nonobject(self):
        self.assertEqual(preflight_risk_record(None), ["record_not_object"])

    def test_input_not_mutated(self):
        original = {"id": "RISK-001", "title": "Example", "description": "Synthetic risk"}
        before = original.copy()
        preflight_risk_record(original)
        self.assertEqual(original, before)


if __name__ == "__main__":
    unittest.main()
