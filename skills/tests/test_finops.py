import tempfile
import unittest
from pathlib import Path

from skills.orchestration.finops import (
    BudgetLedger, BudgetError, BudgetLimit, SpendRequest,
)


class FinOpsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "finops.sqlite")
        self.ledger = BudgetLedger(self.db)
        self.ledger.set_budget(BudgetLimit("project-a", "daily", 10.0))
        self.ledger.set_budget(BudgetLimit("team-a", "daily", 4.0))

    def tearDown(self):
        self.tmp.cleanup()

    def request(self, request_id="r1", project="project-a", team="team-a",
                amount=1.0, created_at="2026-11-07T10:00:00+00:00"):
        return SpendRequest(request_id, project, team, amount, created_at)

    def test_reserves_against_project_and_team_budgets(self):
        receipt = self.ledger.reserve(self.request(amount=2.0))
        self.assertEqual(receipt["status"], "reserved")
        self.assertEqual(receipt["reserved_usd"], 2.0)
        self.assertEqual(self.ledger.snapshot("project-a", "daily", "2026-11-07")["reserved_usd"], 2.0)

    def test_blocks_when_team_budget_would_be_exceeded(self):
        self.ledger.reserve(self.request(amount=3.0))
        with self.assertRaises(BudgetError):
            self.ledger.reserve(self.request("r2", amount=1.1))

    def test_blocks_when_project_budget_would_be_exceeded(self):
        self.ledger.set_budget(BudgetLimit("project-a", "daily", 1.5))
        with self.assertRaises(BudgetError):
            self.ledger.reserve(self.request(amount=2.0))

    def test_idempotent_reservation_and_conflicting_reuse(self):
        first = self.ledger.reserve(self.request())
        second = self.ledger.reserve(self.request())
        self.assertEqual(first["reservation_id"], second["reservation_id"])
        with self.assertRaises(BudgetError):
            self.ledger.reserve(self.request(amount=2.0))

    def test_reconcile_actual_spend_releases_unused_reservation(self):
        reservation = self.ledger.reserve(self.request(amount=3.0))
        result = self.ledger.reconcile(reservation["reservation_id"], 1.25)
        self.assertEqual(result["actual_usd"], 1.25)
        snap = self.ledger.snapshot("team-a", "daily", "2026-11-07")
        self.assertEqual(snap["actual_usd"], 1.25)
        self.assertEqual(snap["reserved_usd"], 0.0)

    def test_rejects_actual_spend_above_reservation(self):
        reservation = self.ledger.reserve(self.request(amount=1.0))
        with self.assertRaises(BudgetError):
            self.ledger.reconcile(reservation["reservation_id"], 1.01)

    def test_monthly_budget_and_threshold_alerts(self):
        self.ledger.set_budget(BudgetLimit("project-a", "monthly", 10.0))
        self.ledger.reserve(self.request(amount=8.5))
        alerts = self.ledger.alerts("project-a", "monthly", "2026-11")
        self.assertTrue(any(alert["threshold_percent"] == 80 for alert in alerts))

    def test_rejects_invalid_dates_amounts_and_budget_limits(self):
        with self.assertRaises(BudgetError):
            self.ledger.reserve(self.request(amount=-1))
        with self.assertRaises(BudgetError):
            self.ledger.reserve(self.request(created_at="not-a-date"))
        with self.assertRaises(BudgetError):
            self.ledger.set_budget(BudgetLimit("x", "weekly", 1.0))

    def test_persists_reservations_after_restart(self):
        self.ledger.reserve(self.request(amount=2.5))
        reopened = BudgetLedger(self.db)
        self.assertEqual(reopened.snapshot("project-a", "daily", "2026-11-07")["reserved_usd"], 2.5)


if __name__ == "__main__":
    unittest.main()
