"""Stage 3B resource allocation contract tests."""
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker

from coden_enterprise.resources import ResourceAllocationError, validate_resource_allocation

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "enterprise"
FIXTURES = ROOT / "tests" / "fixtures" / "enterprise"


class ResourceAllocationContractTests(unittest.TestCase):
    def test_resource_allocation_schema_is_valid(self):
        schema = json.loads((SCHEMAS / "resource-allocation.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)

    def test_synthetic_resource_allocation_fixture_is_valid(self):
        schema = json.loads((SCHEMAS / "resource-allocation.schema.json").read_text(encoding="utf-8"))
        fixture = json.loads((FIXTURES / "resource-allocation.json").read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(fixture))
        self.assertEqual(errors, [], [error.message for error in errors])

    def test_allocation_rejects_invalid_capacity_and_period(self):
        schema = json.loads((SCHEMAS / "resource-allocation.schema.json").read_text(encoding="utf-8"))
        fixture = json.loads((FIXTURES / "resource-allocation.json").read_text(encoding="utf-8"))
        mutations = (
            {"allocation_percent": 101},
            {"allocation_percent": 0},
            {"start_date": "2026-12-31", "end_date": "2026-01-01"},
            {"unexpected": "field"},
        )
        for mutation in mutations:
            invalid = dict(fixture)
            invalid.update(mutation)
            with self.subTest(mutation=mutation):
                if "start_date" in mutation:
                    with self.assertRaises(ResourceAllocationError):
                        validate_resource_allocation(invalid)
                else:
                    self.assertTrue(list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(invalid)))

    def test_allocation_accepts_valid_date_order_and_rejects_reverse_order(self):
        fixture = json.loads((FIXTURES / "resource-allocation.json").read_text(encoding="utf-8"))
        validate_resource_allocation(fixture)
        invalid = dict(fixture, start_date="2026-12-31", end_date="2026-01-01")
        with self.assertRaises(ResourceAllocationError):
            validate_resource_allocation(invalid)

    def test_allocation_requires_assignment_and_accountability(self):
        schema = json.loads((SCHEMAS / "resource-allocation.schema.json").read_text(encoding="utf-8"))
        fixture = json.loads((FIXTURES / "resource-allocation.json").read_text(encoding="utf-8"))
        for field in ("initiative_id", "resource_id", "role", "start_date", "end_date", "allocation_percent", "status"):
            invalid = dict(fixture)
            invalid.pop(field)
            with self.subTest(field=field):
                self.assertTrue(list(Draft202012Validator(schema).iter_errors(invalid)))


if __name__ == "__main__":
    unittest.main()
