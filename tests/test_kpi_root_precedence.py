"""Regression coverage for KPI root precedence and draft-only metadata."""
import unittest
from enterprise.performance.kpi_preflight import preflight_kpi_registry


class RootPrecedenceTests(unittest.TestCase):
    def test_missing_list_has_specific_diagnostic(self):
        self.assertEqual(preflight_kpi_registry({}), ["kpis_not_list"])
        self.assertEqual(preflight_kpi_registry({"status": "draft"}), ["kpis_not_list"])

    def test_legacy_draft_template_remains_unapproved(self):
        self.assertEqual(
            preflight_kpi_registry({"status": "draft", "kpis": []}),
            ["empty_template_not_approved"],
        )

    def test_status_cannot_claim_approval(self):
        self.assertEqual(
            preflight_kpi_registry({"status": "approved", "kpis": []}),
            ["unknown_registry_root_field"],
        )

    def test_unknown_metadata_rejected_even_on_empty_template(self):
        self.assertEqual(
            preflight_kpi_registry({"status": "draft", "kpis": [], "approved": True}),
            ["unknown_registry_root_field"],
        )


if __name__ == "__main__":
    unittest.main()
