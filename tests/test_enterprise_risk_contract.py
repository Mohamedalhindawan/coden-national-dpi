"""Stage 3B enterprise risk register contract tests."""
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "enterprise"
FIXTURES = ROOT / "tests" / "fixtures" / "enterprise"


class EnterpriseRiskContractTests(unittest.TestCase):
    def test_risk_schema_is_valid(self):
        schema = json.loads((SCHEMAS / "risk.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)

    def test_synthetic_risk_fixture_is_valid(self):
        schema = json.loads((SCHEMAS / "risk.schema.json").read_text(encoding="utf-8"))
        fixture = json.loads((FIXTURES / "risk.json").read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(fixture))
        self.assertEqual(errors, [], [error.message for error in errors])

    def test_risk_rejects_out_of_range_score_and_unknown_fields(self):
        schema = json.loads((SCHEMAS / "risk.schema.json").read_text(encoding="utf-8"))
        fixture = json.loads((FIXTURES / "risk.json").read_text(encoding="utf-8"))
        for mutation in ({"likelihood": 6}, {"impact": 0}, {"unapproved_override": True}):
            invalid = dict(fixture)
            invalid.update(mutation)
            with self.subTest(mutation=mutation):
                self.assertTrue(list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(invalid)))

    def test_mitigated_or_closed_risk_requires_owner_and_review(self):
        schema = json.loads((SCHEMAS / "risk.schema.json").read_text(encoding="utf-8"))
        fixture = json.loads((FIXTURES / "risk.json").read_text(encoding="utf-8"))
        for status in ("mitigating", "closed"):
            invalid = dict(fixture, status=status, risk_owner_id="owner-demo-001", mitigation_plan="Synthetic mitigation plan")
            invalid.pop("risk_owner_id")
            with self.subTest(status=status):
                self.assertTrue(list(Draft202012Validator(schema).iter_errors(invalid)))


if __name__ == "__main__":
    unittest.main()
