import unittest

from skills.orchestration.workflow import (
    WorkflowOrchestrator, WorkflowOrchestrationError
)


def task(run_id="workflow-01", owner="owner"):
    return {
        "contract_version": "1.0.0", "run_id": run_id, "task_id": "task-01",
        "role_id": "DEV-01", "owner": owner,
        "objective": "Implement a synthetic fixture safely",
        "inputs": [{"artifact_id": "fixture", "uri": "workspace://fixtures/input.json",
                    "classification": "synthetic"}],
        "constraints": {"allowed_tools": ["read_workspace", "write_task_branch"],
                        "network": "disabled", "write_scope": ["workspace://reports/"],
                        "max_runtime_seconds": 300, "max_retries": 1},
        "acceptance_criteria": ["Implementation contract is recorded"],
        "deadline": "2026-12-01T00:00:00Z", "status": "ready"
    }


class WorkflowOrchestrationTests(unittest.TestCase):
    def setUp(self):
        self.flow = WorkflowOrchestrator()

    def tearDown(self):
        self.flow.close()

    def test_intake_creates_policy_checked_run_and_route(self):
        result = self.flow.intake(task(), {
            "task_type": "software_implementation", "risk_level": "low",
            "data_classification": "synthetic", "network_required": False,
            "requires_code_execution": True
        })
        self.assertEqual(result["state"], "PLANNING")
        self.assertEqual(result["route"]["agent_role"], "DEV-01")
        self.assertFalse(result["route"]["provider_invoked"])

    def test_rejects_role_route_mismatch_before_creating_run(self):
        with self.assertRaises(WorkflowOrchestrationError):
            self.flow.intake(task(), {
                "task_type": "security_review", "risk_level": "low",
                "data_classification": "synthetic", "network_required": False,
                "requires_code_execution": False
            })
        self.assertEqual(self.flow.list_runs(), [])

    def test_workflow_requires_validation_and_independent_approval(self):
        self.flow.intake(task(), {
            "task_type": "software_implementation", "risk_level": "low",
            "data_classification": "synthetic", "network_required": False,
            "requires_code_execution": True
        })
        self.flow.accept_plan("workflow-01", actor="planner")
        self.flow.start_dry_run("workflow-01", actor="operator")
        self.flow.submit_validation("workflow-01", {
            "contract_version": "1.0.0", "run_id": "workflow-01", "task_id": "task-01",
            "role_id": "DEV-01", "status": "succeeded",
            "acceptance_results": [{"criterion": "Implementation contract is recorded",
                                    "status": "pass", "evidence_ref": "workspace://reports/result.json"}],
            "summary": "Synthetic dry-run validation completed", "requires_human_approval": True
        }, actor="validator")
        self.assertEqual(self.flow.get_run("workflow-01")["state"], "REVIEW_REQUIRED")
        with self.assertRaises(WorkflowOrchestrationError):
            self.flow.approve("workflow-01", actor="owner", artifact_hash="a" * 64)
        completed = self.flow.approve("workflow-01", actor="independent-reviewer",
                                      artifact_hash="a" * 64)
        self.assertEqual(completed["state"], "COMPLETED")

    def test_failed_validation_returns_to_planning(self):
        self.flow.intake(task(), {
            "task_type": "software_implementation", "risk_level": "low",
            "data_classification": "synthetic", "network_required": False,
            "requires_code_execution": True
        })
        self.flow.accept_plan("workflow-01", actor="planner")
        self.flow.start_dry_run("workflow-01", actor="operator")
        self.flow.submit_validation("workflow-01", {
            "contract_version": "1.0.0", "run_id": "workflow-01", "task_id": "task-01",
            "role_id": "DEV-01", "status": "failed",
            "acceptance_results": [{"criterion": "Implementation contract is recorded",
                                    "status": "fail"}],
            "summary": "Acceptance check failed", "requires_human_approval": True
        }, actor="validator")
        self.assertEqual(self.flow.get_run("workflow-01")["state"], "PLANNING")

    def test_high_impact_route_cannot_be_started(self):
        t=task()
        t["role_id"]="DPI-01"
        t["constraints"]["allowed_tools"]=["read_workspace"]
        self.flow.intake(t, {
            "task_type": "benefits_decision", "risk_level": "high",
            "data_classification": "synthetic", "network_required": False,
            "requires_code_execution": False
        })
        self.flow.accept_plan("workflow-01", actor="planner")
        with self.assertRaises(WorkflowOrchestrationError):
            self.flow.start_dry_run("workflow-01", actor="operator")

    def test_validation_rejects_missing_evidence_for_pass(self):
        self.flow.intake(task(), {
            "task_type": "software_implementation", "risk_level": "low",
            "data_classification": "synthetic", "network_required": False,
            "requires_code_execution": True
        })
        self.flow.accept_plan("workflow-01", actor="planner")
        self.flow.start_dry_run("workflow-01", actor="operator")
        with self.assertRaises(WorkflowOrchestrationError):
            self.flow.submit_validation("workflow-01", {
                "contract_version": "1.0.0", "run_id": "workflow-01", "task_id": "task-01",
                "role_id": "DEV-01", "status": "succeeded",
                "acceptance_results": [{"criterion": "Implementation contract is recorded",
                                        "status": "pass"}],
                "summary": "Missing evidence", "requires_human_approval": True
            }, actor="validator")


if __name__ == "__main__":
    unittest.main()
