"""Deterministic validation for CODEN orchestration task/result envelopes."""
import json
from pathlib import Path

from jsonschema import Draft202012Validator

BASE = Path(__file__).resolve().parent
TASK_SCHEMA = json.loads((BASE / "schemas" / "task.schema.json").read_text(encoding="utf-8"))
RESULT_SCHEMA = json.loads((BASE / "schemas" / "result.schema.json").read_text(encoding="utf-8"))

ROLE_TOOLS = {
    "ORC-01": {"read_workspace", "schedule_task", "record_state"},
    "PLN-01": {"read_workspace"},
    "ARC-01": {"read_workspace"},
    "DPI-01": {"read_workspace"},
    "DEV-01": {"read_workspace", "write_task_branch", "run_tests"},
    "DATA-01": {"read_synthetic_fixtures", "write_task_branch", "run_tests"},
    "SEC-01": {"read_workspace", "run_security_scans", "write_findings"},
    "QA-01": {"read_workspace", "run_tests", "write_test_report"},
    "DOC-01": {"read_workspace", "write_docs_branch", "run_docs_checks"},
    "FIN-01": {"read_cost_metadata", "write_cost_report"},
    "REL-01": {"read_release_artifacts", "read_ci_results"},
}

def _schema_errors(instance, schema):
    validator = Draft202012Validator(schema)
    return [f"{'.'.join(map(str, error.absolute_path)) or '$'}: {error.message}"
            for error in sorted(validator.iter_errors(instance), key=lambda item: list(map(str, item.absolute_path)))]

def validate_task(task):
    errors = _schema_errors(task, TASK_SCHEMA)
    if not errors:
        role = task["role_id"]
        allowed = ROLE_TOOLS.get(role, set())
        requested = set(task["constraints"]["allowed_tools"])
        for tool in sorted(requested - allowed):
            errors.append(f"constraints.allowed_tools: {tool} is not allowed for role {role}")
        for item in task["inputs"]:
            if item["classification"] != "synthetic":
                errors.append(f"inputs: {item['artifact_id']} is not synthetic; pilot accepts synthetic data only")
    return {"valid": not errors, "errors": errors}

def validate_result(result):
    errors = _schema_errors(result, RESULT_SCHEMA)
    if not errors:
        for index, item in enumerate(result["acceptance_results"]):
            if item["status"] == "pass" and not item.get("evidence_ref"):
                errors.append(f"acceptance_results.{index}.evidence_ref is required for pass")
    return {"valid": not errors, "errors": errors}
