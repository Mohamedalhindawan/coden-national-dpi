import tempfile
import unittest
from pathlib import Path

from skills.orchestration.finops import BudgetLedger, SpendRequest
from skills.orchestration.finops_governance import FinOpsGovernance, FinOpsGovernanceError


class FinOpsGovernanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.ledger = BudgetLedger(root / "ledger.sqlite")
        self.reservation = self.ledger.reserve(SpendRequest(
            "request-1", "project-a", "team-a", 2.0,
            "2026-11-07T10:00:00+00:00", run_id="run-1"))
        self.governance = FinOpsGovernance(self.ledger, root / "governance.sqlite")

    def tearDown(self):
        self.tmp.cleanup()

    def test_reconciliation_requires_submitter_and_separate_approver(self):
        request = self.governance.submit_reconciliation(
            self.reservation["reservation_id"], 1.25,
            actor_id="finance-maker", role="finance_operator",
            request_id="recon-1")
        self.assertEqual(request["status"], "pending")
        with self.assertRaises(FinOpsGovernanceError):
            self.governance.approve_reconciliation(
                "recon-1", actor_id="finance-maker", role="finance_approver")
        approved = self.governance.approve_reconciliation(
            "recon-1", actor_id="finance-checker", role="finance_approver")
        self.assertEqual(approved["status"], "approved")
        self.assertEqual(self.ledger.reconciliation_snapshot(
            "project-a", "team-a", "daily", "2026-11-07")["reconciled_actual_usd"], 1.25)

    def test_roles_are_separated_for_submission_and_approval(self):
        with self.assertRaises(FinOpsGovernanceError):
            self.governance.submit_reconciliation(
                self.reservation["reservation_id"], 1.0,
                actor_id="viewer", role="viewer", request_id="recon-2")
        with self.assertRaises(FinOpsGovernanceError):
            self.governance.approve_reconciliation(
                "missing", actor_id="maker", role="finance_operator")

    def test_duplicate_request_is_idempotent_but_conflicting_reuse_is_rejected(self):
        first = self.governance.submit_reconciliation(
            self.reservation["reservation_id"], 1.0,
            actor_id="maker", role="finance_operator", request_id="recon-3")
        second = self.governance.submit_reconciliation(
            self.reservation["reservation_id"], 1.0,
            actor_id="maker", role="finance_operator", request_id="recon-3")
        self.assertEqual(first, second)
        with self.assertRaises(FinOpsGovernanceError):
            self.governance.submit_reconciliation(
                self.reservation["reservation_id"], 1.5,
                actor_id="maker", role="finance_operator", request_id="recon-3")

    def test_approved_reconciliation_cannot_be_changed_or_reapproved(self):
        self.governance.submit_reconciliation(
            self.reservation["reservation_id"], 1.0,
            actor_id="maker", role="finance_operator", request_id="recon-4")
        self.governance.approve_reconciliation(
            "recon-4", actor_id="checker", role="finance_approver")
        with self.assertRaises(FinOpsGovernanceError):
            self.governance.approve_reconciliation(
                "recon-4", actor_id="second-checker", role="finance_approver")
        with self.assertRaises(FinOpsGovernanceError):
            self.governance.reject_reconciliation(
                "recon-4", actor_id="checker", role="finance_approver")

    def test_audit_events_are_append_only_and_rejection_preserves_ledger(self):
        self.governance.submit_reconciliation(
            self.reservation["reservation_id"], 1.0,
            actor_id="maker", role="finance_operator", request_id="recon-5")
        self.governance.reject_reconciliation(
            "recon-5", actor_id="checker", role="finance_approver")
        self.assertEqual(self.ledger.reconciliation_snapshot(
            "project-a", "team-a", "daily", "2026-11-07")["reconciled_runs"], 0)
        with self.assertRaises(Exception):
            self.governance.db.execute("DELETE FROM audit_events")
        events = self.governance.audit_events("recon-5")
        self.assertEqual([event["event_type"] for event in events],
                         ["reconciliation_submitted", "reconciliation_rejected"])


if __name__ == "__main__":
    unittest.main()
