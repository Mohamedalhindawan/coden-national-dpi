"""Stage 3B KPI measurement record contract tests."""
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "enterprise"
FIXTURES = ROOT / "tests" / "fixtures" / "enterprise"


class KpiMeasurementContractTests(unittest.TestCase):
    def test_measurement_schema_is_valid(self):
        schema = json.loads((SCHEMAS / "kpi-measurement.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_synthetic_measurement_fixture_validates(self):
        schema = json.loads((SCHEMAS / "kpi-measurement.schema.json").read_text(encoding="utf-8"))
        fixture = json.loads((FIXTURES / "kpi-measurement.json").read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(fixture))
        self.assertEqual(errors, [], [error.message for error in errors])

    def test_measurement_links_to_existing_kpi(self):
        kpi = json.loads((FIXTURES / "kpi.json").read_text(encoding="utf-8"))
        measurement = json.loads((FIXTURES / "kpi-measurement.json").read_text(encoding="utf-8"))
        self.assertEqual(measurement["kpi_id"], kpi["kpi_id"])

    def test_measurement_rejects_unknown_fields_and_negative_sample_size(self):
        schema = json.loads((SCHEMAS / "kpi-measurement.schema.json").read_text(encoding="utf-8"))
        fixture = json.loads((FIXTURES / "kpi-measurement.json").read_text(encoding="utf-8"))
        for mutation in ({"unreviewed_override": True}, {"sample_size": -1}):
            invalid = dict(fixture)
            invalid.update(mutation)
            with self.subTest(mutation=mutation):
                self.assertTrue(list(Draft202012Validator(schema).iter_errors(invalid)))

    def test_measurement_requires_provenance_and_reporting_period(self):
        schema = json.loads((SCHEMAS / "kpi-measurement.schema.json").read_text(encoding="utf-8"))
        fixture = json.loads((FIXTURES / "kpi-measurement.json").read_text(encoding="utf-8"))
        for field in ("source_ref", "period_start", "period_end"):
            invalid = dict(fixture)
            invalid.pop(field)
            with self.subTest(field=field):
                self.assertTrue(list(Draft202012Validator(schema).iter_errors(invalid)))


if __name__ == "__main__":
    unittest.main()
