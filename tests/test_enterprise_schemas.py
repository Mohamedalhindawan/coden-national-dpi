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

    def test_work_item_references_an_existing_project_and_agent(self):
        project = json.loads((FIXTURES / "project.json").read_text(encoding="utf-8"))
        agent = json.loads((FIXTURES / "agent-profile.json").read_text(encoding="utf-8"))
        work_item = json.loads((FIXTURES / "work-item.json").read_text(encoding="utf-8"))
        self.assertEqual(work_item["project_id"], project["project_id"])
        self.assertEqual(work_item["assignee_agent_id"], agent["agent_id"])

    def test_pending_approval_has_no_decision_timestamp(self):
        approval = json.loads((FIXTURES / "approval.json").read_text(encoding="utf-8"))
        self.assertEqual(approval["decision"], "pending")
        self.assertNotIn("decided_at", approval)

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

    def test_approval_schema_requires_approver_and_decision_time_for_final_decisions(self):
        schema = json.loads((SCHEMA_DIR / "approval.schema.json").read_text(encoding="utf-8"))
        instance = json.loads((FIXTURES / "approval.json").read_text(encoding="utf-8"))
        instance["decision"] = "approved"
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance))
        self.assertTrue(any(error.validator == "required" for error in errors))

    def test_approval_schema_rejects_pending_decision_metadata(self):
        schema = json.loads((SCHEMA_DIR / "approval.schema.json").read_text(encoding="utf-8"))
        instance = json.loads((FIXTURES / "approval.json").read_text(encoding="utf-8"))
        instance["approver_id"] = "human-approver-01"
        errors = list(Draft202012Validator(schema).iter_errors(instance))
        self.assertTrue(errors)

    def test_audit_event_schema_requires_hash_chain_integrity_fields(self):
        schema = json.loads((SCHEMA_DIR / "audit-event.schema.json").read_text(encoding="utf-8"))
        instance = json.loads((FIXTURES / "audit-event.json").read_text(encoding="utf-8"))
        for field in ("sequence", "previous_hash", "event_hash"):
            with self.subTest(field=field):
                invalid = dict(instance)
                invalid.pop(field, None)
                errors = list(Draft202012Validator(schema).iter_errors(invalid))
                self.assertTrue(errors)

    def test_audit_event_rejects_secret_material(self):
        schema = json.loads((SCHEMA_DIR / "audit-event.schema.json").read_text(encoding="utf-8"))
        instance = json.loads((FIXTURES / "audit-event.json").read_text(encoding="utf-8"))
        instance["secret"] = "never-store-this"
        errors = list(Draft202012Validator(schema).iter_errors(instance))
        self.assertTrue(any(list(error.path) == [] for error in errors))


if __name__ == "__main__":
    unittest.main()
