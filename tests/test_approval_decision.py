"""Tests for approval decision and separation-of-duties policy."""
import unittest

from coden_enterprise.workflow import TransitionError, validate_approval_decision


class ApprovalDecisionTests(unittest.TestCase):
    def pending(self):
        return {
            "approval_id": "approval-001",
            "requested_by": "agent-requester-01",
            "decision": "pending",
        }

    def test_pending_decision_has_no_approver_or_decision_timestamp(self):
        validate_approval_decision(self.pending())

    def test_approved_decision_requires_distinct_approver_and_timestamp(self):
        item = self.pending()
        item.update({
            "decision": "approved",
            "approver_id": "human-approver-01",
            "decided_at": "2026-11-07T20:00:00Z",
        })
        validate_approval_decision(item)

    def test_rejects_self_approval(self):
        item = self.pending()
        item.update({
            "decision": "approved",
            "approver_id": item["requested_by"],
            "decided_at": "2026-11-07T20:00:00Z",
        })
        with self.assertRaises(TransitionError):
            validate_approval_decision(item)

    def test_final_decision_requires_approver_and_timestamp(self):
        for decision in ("approved", "rejected", "expired", "revoked"):
            with self.subTest(decision=decision):
                item = self.pending()
                item["decision"] = decision
                with self.assertRaises(TransitionError):
                    validate_approval_decision(item)

    def test_pending_cannot_carry_approver_or_decided_at(self):
        for field, value in (("approver_id", "human-01"), ("decided_at", "2026-11-07T20:00:00Z")):
            with self.subTest(field=field):
                item = self.pending()
                item[field] = value
                with self.assertRaises(TransitionError):
                    validate_approval_decision(item)

    def test_unknown_decision_and_missing_requester_are_rejected(self):
        item = self.pending()
        item["decision"] = "maybe"
        with self.assertRaises(TransitionError):
            validate_approval_decision(item)
        item = self.pending()
        item["requested_by"] = ""
        with self.assertRaises(TransitionError):
            validate_approval_decision(item)


if __name__ == "__main__":
    unittest.main()
