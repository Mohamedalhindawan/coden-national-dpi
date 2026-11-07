import tempfile
import unittest
from pathlib import Path

from skills.orchestration.control_center import ControlCenter, ControlCenterError
from skills.orchestration.observability import ObservabilityStore
from skills.orchestration.finops import BudgetLedger, BudgetLimit, SpendRequest


class ControlCenterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.metrics = ObservabilityStore(root / "metrics.sqlite")
        self.ledger = BudgetLedger(root / "finops.sqlite")
        self.ledger.set_budget(BudgetLimit("project-a", "daily", 10.0))
        self.ledger.set_budget(BudgetLimit("team-a", "daily", 5.0))
        self.ledger.reserve(SpendRequest("spend-1", "project-a", "team-a", 2.0,
                                        "2026-11-07T10:00:00+00:00"))
        self.metrics.record(self.metric("run-1", "agent-a", "provider-a", "succeeded", 0.25))
        self.metrics.record(self.metric("run-2", "agent-b", "provider-b", "failed", 0.50))

    def tearDown(self):
        self.metrics.close()
        self.tmp.cleanup()

    @staticmethod
    def metric(run_id, agent, provider, status, cost):
        return {
            "run_id": run_id, "task_id": "task-" + run_id, "agent_id": agent,
            "provider": provider, "status": status, "duration_ms": 1000,
            "input_tokens": 100, "output_tokens": 50, "cost_usd": cost,
            "quality_score": 0.8, "policy_violations": 0, "retry_count": 0,
            "evidence_ref": "artifact://evidence/" + run_id,
            "project_id": "project-a", "team_id": "team-a",
            "occurred_at": "2026-11-07T10:00:00+00:00",
        }

    def test_snapshot_aggregates_runs_cost_tokens_quality_and_agents(self):
        center = ControlCenter(self.metrics, self.ledger)
        result = center.snapshot("project-a", "team-a", "daily", "2026-11-07")
        self.assertEqual(result["runs"]["total"], 2)
        self.assertEqual(result["runs"]["failed"], 1)
        self.assertEqual(result["runs"]["succeeded"], 1)
        self.assertEqual(result["usage"]["total_tokens"], 300)
        self.assertEqual(result["usage"]["observed_cost_usd"], 0.75)
        self.assertEqual(len(result["agents"]), 2)
        self.assertEqual(result["budget"]["project"]["remaining_usd"], 8.0)
        self.assertEqual(result["budget"]["team"]["remaining_usd"], 3.0)

    def test_provider_rollup_is_aggregated_without_payload_content(self):
        result = ControlCenter(self.metrics, self.ledger).snapshot(
            "project-a", "team-a", "daily", "2026-11-07")
        self.assertEqual({item["provider"] for item in result["providers"]},
                         {"provider-a", "provider-b"})
        self.assertNotIn("prompt", str(result))
        self.assertNotIn("secret", str(result).lower())

    def test_rejects_invalid_scope_and_period(self):
        center = ControlCenter(self.metrics, self.ledger)
        with self.assertRaises(ControlCenterError):
            center.snapshot("", "team-a", "daily", "2026-11-07")
        with self.assertRaises(ControlCenterError):
            center.snapshot("project-a", "team-a", "weekly", "2026-W45")

    def test_empty_metrics_return_zeroed_snapshot(self):
        empty = ObservabilityStore(":memory:")
        try:
            result = ControlCenter(empty, self.ledger).snapshot(
                "project-a", "team-a", "daily", "2026-11-07")
            self.assertEqual(result["runs"]["total"], 0)
            self.assertEqual(result["usage"]["total_tokens"], 0)
            self.assertEqual(result["agents"], [])
        finally:
            empty.close()


    def test_snapshot_filters_metrics_to_project_team_and_period(self):
        self.metrics.record(self.metric("run-3", "agent-c", "provider-c", "succeeded", 9.0) | {
            "project_id": "another-project", "team_id": "team-a",
            "occurred_at": "2026-11-07T10:00:00+00:00"})
        self.metrics.record(self.metric("run-4", "agent-d", "provider-d", "succeeded", 8.0) | {
            "project_id": "project-a", "team_id": "team-a",
            "occurred_at": "2026-11-06T10:00:00+00:00"})
        result = ControlCenter(self.metrics, self.ledger).snapshot(
            "project-a", "team-a", "daily", "2026-11-07")
        self.assertEqual(result["runs"]["total"], 0)
        self.assertEqual(result["usage"]["observed_cost_usd"], 0.0)

    def test_snapshot_rejects_unattributed_legacy_metrics_for_scoped_reporting(self):
        self.metrics.record(self.metric("legacy-run", "agent-x", "provider-x", "succeeded", 1.0))
        result = ControlCenter(self.metrics, self.ledger).snapshot(
            "project-a", "team-a", "daily", "2026-11-07")
        self.assertEqual(result["runs"]["total"], 0)
        self.assertEqual(result["unattributed_metrics"], 1)

if __name__ == "__main__":
    unittest.main()
