"""Deterministic, side-effect-free WorkItem lifecycle policy.

This module validates requested state changes. It does not authenticate actors,
persist state, verify approval signatures, or enforce runtime permissions.
"""
from __future__ import annotations


class TransitionError(ValueError):
    """Raised when a WorkItem lifecycle transition violates policy."""


_ALLOWED_TRANSITIONS = {
    "draft": {"submitted", "cancelled"},
    "submitted": {"approved", "rejected", "blocked", "cancelled"},
    "approved": {"ready", "blocked", "cancelled"},
    "ready": {"in_progress", "blocked", "cancelled"},
    "in_progress": {"validating", "blocked", "failed", "cancelled"},
    "validating": {"human_review", "blocked", "failed"},
    "human_review": {"accepted", "rejected", "blocked"},
    "blocked": {"ready", "cancelled"},
    "accepted": set(),
    "rejected": set(),
    "cancelled": set(),
    "failed": set(),
}

_APPROVAL_GATED_TRANSITIONS = {
    ("submitted", "approved"),
    ("human_review", "accepted"),
}


def validate_work_item_transition(
    current_status: str,
    next_status: str,
    *,
    approval_status: str | None = None,
) -> None:
    """Validate one state transition; return None when the transition is allowed."""
    if current_status not in _ALLOWED_TRANSITIONS:
        raise TransitionError(f"Unknown current status: {current_status!r}")
    if next_status not in _ALLOWED_TRANSITIONS:
        raise TransitionError(f"Unknown next status: {next_status!r}")
    if current_status == next_status:
        raise TransitionError("Self-transitions are not allowed")
    if next_status not in _ALLOWED_TRANSITIONS[current_status]:
        raise TransitionError(
            f"Transition {current_status!r} -> {next_status!r} is not allowed"
        )
    if (current_status, next_status) in _APPROVAL_GATED_TRANSITIONS:
        if approval_status != "approved":
            raise TransitionError(
                f"Transition {current_status!r} -> {next_status!r} "
                "requires an approved decision"
            )


def validate_work_item_references(
    work_item: dict,
    project_ids: set[str],
    agent_ids: set[str],
) -> None:
    """Reject unresolved project/agent references using supplied trusted indexes."""
    project_id = work_item.get("project_id")
    if not isinstance(project_id, str) or project_id not in project_ids:
        raise TransitionError(f"Unknown project reference: {project_id!r}")

    agent_id = work_item.get("assignee_agent_id")
    if agent_id is not None and (
        not isinstance(agent_id, str) or agent_id not in agent_ids
    ):
        raise TransitionError(f"Unknown agent reference: {agent_id!r}")
