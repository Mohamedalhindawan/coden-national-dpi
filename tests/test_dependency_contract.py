"""Stage 3B enterprise dependency contract tests."""
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker

from coden_enterprise.dependencies import validate_dependency, find_dependency_cycle

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "enterprise" / "dependency.schema.json"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "enterprise" / "dependency.json"


class EnterpriseDependencyContractTests(unittest.TestCase):
    def test_schema_is_valid_and_fixture_conforms(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(fixture))
        self.assertEqual(errors, [], [error.message for error in errors])

    def test_schema_rejects_unknown_fields_and_invalid_values(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        for mutation in ({"unexpected": True}, {"dependency_type": "magical"}, {"status": "done-ish"}):
            candidate = dict(fixture, **mutation)
            with self.subTest(mutation=mutation):
                self.assertTrue(list(Draft202012Validator(schema).iter_errors(candidate)))

    def test_dependency_rejects_self_reference_and_missing_endpoints(self):
        valid = {"dependency_id": "dep-001", "source_id": "initiative-a",
                 "target_id": "initiative-b", "dependency_type": "blocks",
                 "status": "active"}
        self.assertEqual(validate_dependency(valid, {"initiative-a", "initiative-b"}), [])
        self.assertIn("self_dependency", validate_dependency(
            dict(valid, target_id="initiative-a"), {"initiative-a"}))
        self.assertIn("unknown_endpoint", validate_dependency(valid, {"initiative-a"}))

    def test_cycle_detection_returns_deterministic_cycle_or_none(self):
        edges = [("a", "b"), ("b", "c"), ("c", "a")]
        self.assertEqual(find_dependency_cycle(edges), ("a", "b", "c", "a"))
        self.assertIsNone(find_dependency_cycle([("a", "b"), ("b", "c"), ("d", "e")]))

    def test_cycle_detection_ignores_duplicate_edges(self):
        self.assertEqual(find_dependency_cycle([("a", "b"), ("a", "b"), ("b", "a")]),
                         ("a", "b", "a"))


if __name__ == "__main__":
    unittest.main()
