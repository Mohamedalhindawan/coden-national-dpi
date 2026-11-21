"""Prepare a reviewable work order, never execute it."""
from ai_factory.intake import validate_intake
from ai_factory.budget_guard import authorize_run


def prepare_work_order(task, budget):
    validation = validate_intake(task)
    cost = authorize_run(budget)
    ready = validation["valid"] and cost["allowed"]
    return {
        "task_id": task.get("id") if isinstance(task, dict) else None,
        "ready_for_review": ready,
        "execution_authorized": False,
        "status": "awaiting_execution_approval" if ready else "blocked",
        "allowed_actions": list(task["requested_actions"]) if ready else [],
        "reasons": validation["errors"] + ([] if cost["allowed"] else [cost["reason"]]),
    }
