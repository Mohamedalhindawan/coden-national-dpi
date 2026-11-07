import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from skills.orchestration.validator import validate_task, validate_result

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "skills" / "orchestration" / "schemas"


class OrchestrationContractTests(unittest.TestCase):
    def test_task_schema_accepts_minimal_valid_task(self):
        schema = __import__("json").loads((SCHEMA_DIR / "task.schema.json").read_text())
        task = {
            "contract_version": "1.0.0",
            "run_id": "run-synth-01",
            "task_id": "task-synth-01",
            "role_id": "QA-01",
            "owner": "human-owner",
            "objective": "Check a synthetic fixture",
            "inputs": [{"artifact_id": "fixture-01", "uri": "workspace://fixtures/a.json", "classification": "synthetic"}],
            "constraints": {"allowed_tools": ["read_workspace", "run_tests"], "network": "disabled", "write_scope": ["workspace://reports/"], "max_runtime_seconds": 300, "max_retries": 1},
            "acceptance_criteria": ["Report validation outcome"],
            "deadline": "2026-12-01T00:00:00Z",
            "status": "ready"
        }
        Draft202012Validator.check_schema(schema)
        self.assertTrue(Draft202012Validator(schema).is_valid(task))

    def test_rejects_task_with_missing_owner(self):
        task = {"contract_version": "1.0.0", "run_id": "r", "task_id": "t", "role_id": "QA-01", "objective": "x"}
        result = validate_task(task)
        self.assertFalse(result["valid"])
        self.assertIn("owner", " ".join(result["errors"]))

    def test_rejects_tool_outside_role_allowlist(self):
        task = {
            "contract_version": "1.0.0", "run_id": "r", "task_id": "t",
            "role_id": "QA-01", "owner": "human", "objective": "test",
            "inputs": [{"artifact_id": "f", "uri": "workspace://fixtures/f.json", "classification": "synthetic"}],
            "constraints": {"allowed_tools": ["merge_pull_request"], "network": "disabled", "write_scope": [], "max_runtime_seconds": 60, "max_retries": 0},
            "acceptance_criteria": ["pass"], "deadline": "2026-12-01T00:00:00Z", "status": "ready"
        }
        result = validate_task(task)
        self.assertFalse(result["valid"])
        self.assertTrue(any("merge_pull_request" in error for error in result["errors"]))

    def test_rejects_real_personal_data_classification_in_synthetic_pilot(self):
        task = {
            "contract_version": "1.0.0", "run_id": "r", "task_id": "t",
            "role_id": "QA-01", "owner": "human", "objective": "test",
            "inputs": [{"artifact_id": "f", "uri": "workspace://fixtures/f.json", "classification": "personal"}],
            "constraints": {"allowed_tools": ["read_workspace"], "network": "disabled", "write_scope": [], "max_runtime_seconds": 60, "max_retries": 0},
            "acceptance_criteria": ["pass"], "deadline": "2026-12-01T00:00:00Z", "status": "ready"
        }
        result = validate_task(task)
        self.assertFalse(result["valid"])

    def test_result_pass_requires_evidence_reference(self):
        result = {
            "contract_version": "1.0.0", "run_id": "r", "task_id": "t",
            "role_id": "QA-01", "status": "succeeded", "summary": "done",
            "acceptance_results": [{"criterion": "safe", "status": "pass"}],
            "requires_human_approval": False
        }
        checked = validate_result(result)
        self.assertFalse(checked["valid"])
        self.assertTrue(any("evidence_ref" in error for error in checked["errors"]))


if __name__ == "__main__":
    unittest.main()
