"""Integrated CODEN workflow facade over the local control plane.

Coordinates policy routing, task contracts, state transitions, validation and
human review. It never invokes providers or executes tools.
"""
import json

from skills.orchestration.runtime import OrchestrationRuntime, WorkflowError
from skills.orchestration.routing import recommend_route, RoutingError
from skills.orchestration.validator import validate_result


class WorkflowOrchestrationError(ValueError):
    pass


class WorkflowOrchestrator:
    def __init__(self, database=":memory:"):
        self.runtime = OrchestrationRuntime(database)
        self.routes = {}

    def intake(self, task, profile):
        try:
            route = recommend_route(profile)
            if route["agent_role"] != task.get("role_id"):
                raise WorkflowOrchestrationError("Task role does not match the policy route")
            if profile.get("data_classification") != "synthetic":
                raise WorkflowOrchestrationError("Integrated workflow currently accepts synthetic data only")
            if task.get("constraints", {}).get("network") != "disabled":
                raise WorkflowOrchestrationError("Task contract must disable network access")
            run = self.runtime.create_run(task)
            self.routes[task["run_id"]] = route
            run = self.runtime.transition(task["run_id"], "submit", actor="workflow-orchestrator")
            run = self.runtime.transition(task["run_id"], "allow", actor="policy-gate",
                                          details={"route_version": route["routing_version"],
                                                   "agent_role": route["agent_role"]})
            return {"run_id": task["run_id"], "state": run["state"], "route": route}
        except (WorkflowError, RoutingError) as exc:
            raise WorkflowOrchestrationError(str(exc)) from exc

    def accept_plan(self, run_id, actor):
        try:
            return self.runtime.transition(run_id, "plan_accepted", actor=actor)
        except WorkflowError as exc:
            raise WorkflowOrchestrationError(str(exc)) from exc

    def start_dry_run(self, run_id, actor):
        route = self.routes.get(run_id)
        if route is None:
            raise WorkflowOrchestrationError("No in-memory policy route is available for this run")
        if route["execution_mode"] != "dry_run" or route["high_impact"]:
            raise WorkflowOrchestrationError("Route is recommendation-only; execution is prohibited")
        try:
            return self.runtime.transition(run_id, "start", actor=actor,
                                           details={"mode": "dry_run", "provider_invoked": False,
                                                    "network": "disabled"})
        except WorkflowError as exc:
            raise WorkflowOrchestrationError(str(exc)) from exc

    def submit_validation(self, run_id, result, actor):
        run = self.get_run(run_id)
        task = run["task"]
        if result.get("run_id") != run_id or result.get("task_id") != task["task_id"]:
            raise WorkflowOrchestrationError("Result identity does not match workflow task")
        if result.get("role_id") != task["role_id"]:
            raise WorkflowOrchestrationError("Result role does not match task role")
        checked = validate_result(result)
        if not checked["valid"]:
            raise WorkflowOrchestrationError("Invalid result contract: " + "; ".join(checked["errors"]))
        criteria = {item["criterion"]: item["status"] for item in result["acceptance_results"]}
        expected = set(task["acceptance_criteria"])
        if set(criteria) != expected:
            raise WorkflowOrchestrationError("Result criteria must exactly match task acceptance criteria")
        if result["status"] == "succeeded" and not all(value == "pass" for value in criteria.values()):
            raise WorkflowOrchestrationError("Succeeded result requires every acceptance criterion to pass")
        if result["status"] != "succeeded" or any(value != "pass" for value in criteria.values()):
            event = "checks_fail"
        else:
            event = "checks_pass"
        try:
            self.runtime.transition(run_id, "tasks_done", actor=actor,
                                           details={"result_status": result["status"]})
        except WorkflowError as exc:
            raise WorkflowOrchestrationError(str(exc)) from exc
        try:
            return self.runtime.transition(run_id, event, actor=actor,
                                           details={"criteria_total": len(criteria),
                                                    "criteria_passed": sum(v == "pass" for v in criteria.values())})
        except WorkflowError as exc:
            raise WorkflowOrchestrationError(str(exc)) from exc

    def approve(self, run_id, actor, artifact_hash):
        try:
            return self.runtime.transition(run_id, "human_approve", actor=actor,
                                           details={"actor_type": "independent_human"},
                                           artifact_hash=artifact_hash)
        except WorkflowError as exc:
            raise WorkflowOrchestrationError(str(exc)) from exc

    def reject(self, run_id, actor, reason):
        if not isinstance(reason, str) or not reason.strip():
            raise WorkflowOrchestrationError("Review rejection requires a reason")
        try:
            return self.runtime.transition(run_id, "human_reject", actor=actor,
                                           details={"actor_type": "independent_human",
                                                    "reason": reason})
        except WorkflowError as exc:
            raise WorkflowOrchestrationError(str(exc)) from exc

    def request_changes(self, run_id, actor, reason):
        if not isinstance(reason, str) or not reason.strip():
            raise WorkflowOrchestrationError("Change request requires a reason")
        try:
            return self.runtime.transition(run_id, "human_request_changes", actor=actor,
                                           details={"actor_type": "independent_human",
                                                    "reason": reason})
        except WorkflowError as exc:
            raise WorkflowOrchestrationError(str(exc)) from exc

    def get_run(self, run_id):
        try:
            row = self.runtime.get_run(run_id)
            row["task"] = json.loads(row.pop("task_json"))
            return row
        except WorkflowError as exc:
            raise WorkflowOrchestrationError(str(exc)) from exc

    def list_runs(self):
        rows = self.runtime.db.execute(
            "SELECT run_id,state,owner,created_at,updated_at FROM runs ORDER BY created_at,run_id"
        ).fetchall()
        return [dict(row) for row in rows]

    def audit_log(self, run_id):
        try:
            return self.runtime.audit_log(run_id)
        except WorkflowError as exc:
            raise WorkflowOrchestrationError(str(exc)) from exc

    def close(self):
        self.runtime.close()
