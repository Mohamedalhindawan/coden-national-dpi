"""Independent Draft 2020-12 validation against a pinned PR #43 schema snapshot.

Snapshot source: feat/stage-3b-strategic-objective-kpi-contracts,
schemas/enterprise/kpi.schema.json, blob 827d5a4d0299ca727be594c56130f1605353bd6a.
This is a test fixture, NOT a canonical schema decision or registry migration.
"""
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from enterprise.performance.kpi_preflight import preflight_kpi_record


SCHEMA_PATH = Path(__file__).parent / "fixtures" / "kpi_pr43_schema_snapshot.json"


def sample():
    return {
        "kpi_id": "kpi-001", "objective_id": "obj-001",
        "name": "Synthetic KPI", "unit": "count",
        "baseline": 0, "target": 1, "direction": "increase",
        "measurement_frequency": "monthly", "status": "draft",
        "created_at": "2026-11-11T00:00:00Z",
    }


class KpiDraft202012ParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema, format_checker=FormatChecker())

    def assert_both_accept(self, record):
        self.assertEqual(list(self.validator.iter_errors(record)), [])
        self.assertEqual(preflight_kpi_record(record), [])

    def assert_both_reject(self, record):
        self.assertTrue(list(self.validator.iter_errors(record)))
        self.assertTrue(preflight_kpi_record(record))

    def test_valid_synthetic_record(self):
        self.assert_both_accept(sample())

    def test_optional_fields(self):
        record = sample()
        record.update(owner_id="team-001", definition="Synthetic definition")
        self.assert_both_accept(record)

    def test_unknown_property(self):
        record = sample()
        record["unexpected"] = 42
        self.assert_both_reject(record)

    def test_invalid_enum(self):
        record = sample()
        record["direction"] = "sideways"
        self.assert_both_reject(record)

    def test_invalid_identifier(self):
        record = sample()
        record["kpi_id"] = "bad id"
        self.assert_both_reject(record)

    def test_missing_required_field(self):
        record = sample()
        del record["objective_id"]
        self.assert_both_reject(record)

    def test_invalid_timestamp_format(self):
        record = sample()
        record["created_at"] = "not-a-date"
        self.assert_both_reject(record)

    def test_boolean_is_not_number(self):
        record = sample()
        record["target"] = True
        self.assert_both_reject(record)


if __name__ == "__main__":
    unittest.main()
