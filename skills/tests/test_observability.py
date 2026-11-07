import tempfile
import unittest
from pathlib import Path

from skills.orchestration.observability import ObservabilityStore, ObservabilityError

class ObservabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ObservabilityStore(Path(self.tmp.name) / "metrics.sqlite")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def sample(self, agent="QA-01", **overrides):
        record = {
            "run_id": "run-1", "task_id": "task-1", "agent_id": agent,
            "provider": "local-dry-run", "status": "succeeded",
            "duration_ms": 1200, "input_tokens": 100, "output_tokens": 50,
            "cost_usd": 0.002, "quality_score": 0.9,
            "policy_violations": 0, "retry_count": 0,
            "evidence_ref": "artifact://reports/result.json"
        }
        record.update(overrides)
        return record

    def test_records_metrics_without_raw_prompt_fields(self):
        stored = self.store.record(self.sample(secret="do-not-store", prompt="private"))
        self.assertNotIn("secret", stored)
        self.assertNotIn("prompt", stored)
        self.assertEqual(stored["agent_id"], "QA-01")

    def test_aggregates_agent_performance_and_cost(self):
        self.store.record(self.sample())
        self.store.record(self.sample(status="failed", duration_ms=800, cost_usd=0.003,
                                      quality_score=0.4, policy_violations=1))
        result = self.store.agent_summary("QA-01")
        self.assertEqual(result["runs"], 2)
        self.assertEqual(result["success_rate"], 0.5)
        self.assertAlmostEqual(result["total_cost_usd"], 0.005)
        self.assertAlmostEqual(result["average_quality"], 0.65)
        self.assertEqual(result["policy_violations"], 1)

    def test_rejects_invalid_ranges_and_status(self):
        for record in [self.sample(duration_ms=-1), self.sample(cost_usd=-1),
                       self.sample(quality_score=1.5), self.sample(status="unknown")]:
            with self.subTest(record=record), self.assertRaises(ObservabilityError):
                self.store.record(record)

    def test_rejects_missing_evidence_for_success(self):
        with self.assertRaises(ObservabilityError):
            self.store.record(self.sample(evidence_ref=""))

    def test_events_are_append_only(self):
        self.store.record(self.sample())
        with self.assertRaises(Exception):
            self.store.db.execute("DELETE FROM agent_metrics")

    def test_records_project_team_and_timestamp_attribution(self):
        stored = self.store.record(self.sample(
            project_id="tamam", team_id="platform",
            occurred_at="2026-11-07T10:15:00+03:00"))
        self.assertEqual(stored["project_id"], "tamam")
        self.assertEqual(stored["team_id"], "platform")
        self.assertEqual(stored["occurred_at"], "2026-11-07T07:15:00+00:00")

    def test_rejects_partial_scope_attribution_and_naive_timestamp(self):
        for changes in [
            {"project_id": "tamam"},
            {"team_id": "platform"},
            {"project_id": "tamam", "team_id": "platform", "occurred_at": "2026-11-07T10:00:00"},
        ]:
            with self.subTest(changes=changes), self.assertRaises(ObservabilityError):
                self.store.record(self.sample(**changes))

if __name__ == "__main__":
    unittest.main()
