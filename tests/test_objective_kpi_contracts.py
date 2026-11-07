"""Stage 3B strategic objective and KPI contract tests."""
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "enterprise"
FIXTURES = ROOT / "tests" / "fixtures" / "enterprise"


class ObjectiveKpiContractsTests(unittest.TestCase):
    def _schema(self, name):
        schema = json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        return schema

    def test_objective_and_kpi_schemas_are_valid(self):
        for name in ("strategic-objective", "kpi"):
            with self.subTest(name=name):
                self.assertEqual(self._schema(name)["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_synthetic_objective_and_kpi_fixtures_validate(self):
        for name in ("strategic-objective", "kpi"):
            with self.subTest(name=name):
                fixture = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
                errors = list(Draft202012Validator(self._schema(name), format_checker=FormatChecker()).iter_errors(fixture))
                self.assertEqual(errors, [], [error.message for error in errors])

    def test_objective_links_to_existing_portfolio(self):
        portfolio = json.loads((FIXTURES / "portfolio.json").read_text(encoding="utf-8"))
        objective = json.loads((FIXTURES / "strategic-objective.json").read_text(encoding="utf-8"))
        self.assertEqual(objective["portfolio_id"], portfolio["portfolio_id"])

    def test_kpi_links_to_existing_objective_and_valid_range(self):
        objective = json.loads((FIXTURES / "strategic-objective.json").read_text(encoding="utf-8"))
        kpi = json.loads((FIXTURES / "kpi.json").read_text(encoding="utf-8"))
        self.assertEqual(kpi["objective_id"], objective["objective_id"])
        self.assertLessEqual(kpi["baseline"], kpi["target"])

    def test_objective_rejects_unknown_fields_and_invalid_status(self):
        schema = self._schema("strategic-objective")
        fixture = json.loads((FIXTURES / "strategic-objective.json").read_text(encoding="utf-8"))
        for mutation in ({"unexpected": True}, {"status": "unbounded"}):
            invalid = dict(fixture)
            invalid.update(mutation)
            with self.subTest(mutation=mutation):
                self.assertTrue(list(Draft202012Validator(schema).iter_errors(invalid)))

    def test_kpi_rejects_bad_unit_and_target(self):
        schema = self._schema("kpi")
        fixture = json.loads((FIXTURES / "kpi.json").read_text(encoding="utf-8"))
        for mutation in ({"unit": ""}, {"direction": "sideways"}):
            invalid = dict(fixture)
            invalid.update(mutation)
            with self.subTest(mutation=mutation):
                self.assertTrue(list(Draft202012Validator(schema).iter_errors(invalid)))


if __name__ == "__main__":
    unittest.main()
