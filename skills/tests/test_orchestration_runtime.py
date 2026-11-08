import tempfile
import unittest
from pathlib import Path

from skills.orchestration.runtime import OrchestrationRuntime, WorkflowError

def valid_task(run_id="run-runtime-01"):
    return {
        "contract_version": "1.0.0", "run_id": run_id, "task_id": "task-01",
        "role_id": "QA-01", "owner": "task-owner",
        "objective": "Validate synthetic runtime fixture",
        "inputs": [{"artifact_id": "fixture-01", "uri": "workspace://fixtures/a.json", "classification": "synthetic"}],
        "constraints": {"allowed_tools": ["read_workspace", "run_tests"], "network": "disabled",
                        "write_scope": ["workspace://reports/"], "max_runtime_seconds": 300, "max_retries": 1},
        "acceptance_criteria": ["Validation result is recorded"],
        "deadline": "2026-12-01T00:00:00Z", "status": "ready"
    }

class OrchestrationRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "runtime.sqlite"
        self.runtime = OrchestrationRuntime(self.db_path)

    def tearDown(self):
        self.runtime.close()
        self.tmp.cleanup()

    def advance_to_review(self, run_id="run-runtime-01"):
        self.runtime.create_run(valid_task(run_id))
        for event in ["submit", "allow", "plan_accepted", "start", "tasks_done", "checks_pass"]:
            self.runtime.transition(run_id, event, actor="operator")
        return run_id

    def test_run_follows_allowed_transitions_and_persists(self):
        run_id = self.advance_to_review()
        self.assertEqual(self.runtime.get_run(run_id)["state"], "REVIEW_REQUIRED")
        self.runtime.close()
        self.runtime = OrchestrationRuntime(self.db_path)
        self.assertEqual(self.runtime.get_run(run_id)["state"], "REVIEW_REQUIRED")
        self.assertEqual(len(self.runtime.audit_log(run_id)), 7)

    def test_invalid_transition_is_rejected(self):
        self.runtime.create_run(valid_task())
        with self.assertRaises(WorkflowError):
            self.runtime.transition("run-runtime-01", "start", actor="operator")

    def test_approval_requires_independent_human_and_artifact_hash(self):
        run_id = self.advance_to_review()
        with self.assertRaises(WorkflowError):
            self.runtime.transition(run_id, "human_approve", actor="task-owner", artifact_hash="a" * 64)
        with self.assertRaises(WorkflowError):
            self.runtime.transition(run_id, "human_approve", actor="reviewer",
                                     details={"actor_type": "independent_human"}, artifact_hash="bad")
        result = self.runtime.transition(run_id, "human_approve", actor="reviewer",
                                         details={"actor_type": "independent_human"},
                                         artifact_hash="a" * 64)
        self.assertEqual(result["state"], "COMPLETED")
        self.assertEqual(result["approved_artifact_hash"], "a" * 64)

    def test_terminal_run_cannot_be_reopened(self):
        run_id = self.advance_to_review()
        self.runtime.transition(run_id, "human_reject", actor="reviewer",
                                details={"actor_type": "independent_human"})
        with self.assertRaises(WorkflowError):
            self.runtime.transition(run_id, "submit", actor="operator")

    def test_duplicate_run_id_is_rejected(self):
        self.runtime.create_run(valid_task())
        with self.assertRaises(WorkflowError):
            self.runtime.create_run(valid_task())

    def test_cancel_stops_run_and_audit_is_append_only(self):
        self.runtime.create_run(valid_task())
        self.runtime.transition("run-runtime-01", "cancel", actor="operator")
        self.assertEqual(self.runtime.get_run("run-runtime-01")["state"], "CANCELLED")
        with self.assertRaises(Exception):
            self.runtime.db.execute("DELETE FROM audit_events")

if __name__ == "__main__":
    unittest.main()
