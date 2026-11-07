"""Tests for the Stage 3A work-item lifecycle transition policy."""
import unittest

from coden_enterprise.workflow import (\n    validate_work_item_transition,\n    validate_work_item_references,\n    TransitionError,\n)


class WorkItemLifecycleTests(unittest.TestCase):
    def test_allows_only_declared_forward_transitions(self):
        validate_work_item_transition("draft", "submitted")
        validate_work_item_transition("in_progress", "validating")
        validate_work_item_transition("human_review", "accepted", approval_status="approved")

    def test_rejects_skipping_required_review(self):
        with self.assertRaises(TransitionError):
            validate_work_item_transition("in_progress", "accepted", approval_status="approved")

    def test_requires_approval_before_acceptance(self):
        for status in ("pending", "rejected", None):
            with self.subTest(status=status):
                with self.assertRaises(TransitionError):
                    validate_work_item_transition("human_review", "accepted", approval_status=status)

    def test_terminal_states_cannot_be_reopened(self):
        for state in ("accepted", "rejected", "cancelled", "failed"):
            with self.subTest(state=state):
                with self.assertRaises(TransitionError):
                    validate_work_item_transition(state, "ready")

    def test_rejects_unknown_project_and_assignee_references(self):
        work_item = {"project_id": "missing-project", "assignee_agent_id": "missing-agent"}
        with self.assertRaises(TransitionError):
            validate_work_item_references(work_item, {"known-project"}, {"known-agent"})

    def test_allows_unassigned_work_item_when_project_exists(self):
        work_item = {"project_id": "known-project"}
        validate_work_item_references(work_item, {"known-project"}, set())

    def test_unknown_states_and_self_transitions_are_rejected(self):
        with self.assertRaises(TransitionError):
            validate_work_item_transition("unknown", "ready")
        with self.assertRaises(TransitionError):
            validate_work_item_transition("draft", "draft")


if __name__ == "__main__":
    unittest.main()
