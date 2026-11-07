"""Stage 3A contract tests for canonical CODEN management records."""
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "enterprise"
FIXTURES = ROOT / "tests" / "fixtures" / "enterprise"

RECORDS = ("project", "agent-profile", "work-item", "approval", "audit-event")


class EnterpriseSchemaTests(unittest.TestCase):
    def test_all_canonical_schemas_exist_and_are_valid_draft_2020_12(self):
        for record in RECORDS:
            with self.subTest(record=record):
                schema = json.loads((SCHEMA_DIR / f"{record}.schema.json").read_text(encoding="utf-8"))
                Draft202012Validator.check_schema(schema)
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_synthetic_fixtures_validate_against_their_schemas(self):
        for record in RECORDS:
            with self.subTest(record=record):
                schema = json.loads((SCHEMA_DIR / f"{record}.schema.json").read_text(encoding="utf-8"))
                instance = json.loads((FIXTURES / f"{record}.json").read_text(encoding="utf-8"))
                errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance))
                self.assertEqual(errors, [], [error.message for error in errors])

    def test_work_item_rejects_unknown_fields(self):
        schema = json.loads((SCHEMA_DIR / "work-item.schema.json").read_text(encoding="utf-8"))
        instance = json.loads((FIXTURES / "work-item.json").read_text(encoding="utf-8"))
        instance["unreviewed_permission"] = "admin"
        errors = list(Draft202012Validator(schema).iter_errors(instance))
        self.assertTrue(any(list(error.path) == [] for error in errors))

    def test_approval_requires_artifact_digest_and_human_decision_fields(self):
        schema = json.loads((SCHEMA_DIR / "approval.schema.json").read_text(encoding="utf-8"))
        instance = json.loads((FIXTURES / "approval.json").read_text(encoding="utf-8"))
        instance.pop("artifact_digest")
        errors = list(Draft202012Validator(schema).iter_errors(instance))
        self.assertTrue(any(error.validator == "required" for error in errors))

    def test_audit_event_rejects_secret_material(self):
        schema = json.loads((SCHEMA_DIR / "audit-event.schema.json").read_text(encoding="utf-8"))
        instance = json.loads((FIXTURES / "audit-event.json").read_text(encoding="utf-8"))
        instance["secret"] = "never-store-this"
        errors = list(Draft202012Validator(schema).iter_errors(instance))
        self.assertTrue(any(list(error.path) == [] for error in errors))


if __name__ == "__main__":
    unittest.main()
