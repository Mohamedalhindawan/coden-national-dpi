"""Stage 3B portfolio and initiative contract tests."""
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "enterprise"
FIXTURES = ROOT / "tests" / "fixtures" / "enterprise"


class PortfolioInitiativeTests(unittest.TestCase):
    def test_portfolio_and_initiative_schemas_exist_and_are_valid(self):
        for name in ("portfolio", "initiative"):
            with self.subTest(name=name):
                schema = json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
                Draft202012Validator.check_schema(schema)
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_synthetic_portfolio_and_initiative_fixtures_validate(self):
        for name in ("portfolio", "initiative"):
            with self.subTest(name=name):
                schema = json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
                fixture = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
                errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(fixture))
                self.assertEqual(errors, [], [error.message for error in errors])

    def test_initiative_links_to_existing_portfolio(self):
        portfolio = json.loads((FIXTURES / "portfolio.json").read_text(encoding="utf-8"))
        initiative = json.loads((FIXTURES / "initiative.json").read_text(encoding="utf-8"))
        self.assertEqual(initiative["portfolio_id"], portfolio["portfolio_id"])

    def test_portfolio_rejects_negative_budget_and_unknown_fields(self):
        schema = json.loads((SCHEMA_DIR / "portfolio.schema.json").read_text(encoding="utf-8"))
        fixture = json.loads((FIXTURES / "portfolio.json").read_text(encoding="utf-8"))
        for mutation in ({"budget_amount": -1}, {"unreviewed_admin_flag": True}):
            with self.subTest(mutation=mutation):
                invalid = dict(fixture)
                invalid.update(mutation)
                errors = list(Draft202012Validator(schema).iter_errors(invalid))
                self.assertTrue(errors)

    def test_initiative_rejects_invalid_status_and_currency(self):
        schema = json.loads((SCHEMA_DIR / "initiative.schema.json").read_text(encoding="utf-8"))
        fixture = json.loads((FIXTURES / "initiative.json").read_text(encoding="utf-8"))
        for mutation in ({"status": "magic"}, {"currency": "YERX"}):
            with self.subTest(mutation=mutation):
                invalid = dict(fixture)
                invalid.update(mutation)
                errors = list(Draft202012Validator(schema).iter_errors(invalid))
                self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
