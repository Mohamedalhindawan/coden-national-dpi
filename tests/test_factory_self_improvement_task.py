"""Contract for a genuine, no-secrets CODEN self-improvement pilot."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "ai_factory" / "examples" / "factory-review-queue-metric.json"
WORKFLOW = ROOT / ".github" / "workflows" / "factory-self-improvement-cpu.yml"


class ReviewQueueSelfImprovementTaskTests(unittest.TestCase):
    def test_task_is_synthetic_read_only_and_has_independent_holdout(self):
        task = json.loads(TASK.read_text(encoding="utf-8"))
        self.assertEqual(task["id"], "CODEN-SELF-REVIEW-METRIC-01")
        self.assertEqual(task["recipe"], "python-transform")
        self.assertEqual(task["data_classification"], "synthetic")
        self.assertEqual(task["requested_actions"], ["run_tests"])
        self.assertEqual(task["estimated_cost_usd"], 0)
        self.assertEqual(len(task["cases"]), 3)
        self.assertEqual(len(task["review_cases"]), 3)
        self.assertFalse(
            {json.dumps(c["input"], sort_keys=True) for c in task["cases"]}
            & {json.dumps(c["input"], sort_keys=True) for c in task["review_cases"]}
        )
        for case in task["cases"] + task["review_cases"]:
            result = sum(
                1 for status in case["input"]
                if status in {"pending_review", "needs_review"}
            )
            self.assertEqual(result, case["expected"])

    def test_workflow_executes_real_local_model_and_review_gate_only(self):
        flow = WORKFLOW.read_text(encoding="utf-8").lower()
        self.assertIn("feat/factory-self-improvement-freecpu-20261123", flow)
        self.assertIn("factory-review-queue-metric.json", flow)
        self.assertIn("permissions:\n  contents: read", flow)
        self.assertIn("github.event.pull_request.head.repo.full_name == github.repository", flow)
        self.assertIn("python -m ai_factory.project", flow)
        self.assertIn("--local-model", flow)
        self.assertIn("python -m ai_factory.free_cpu_receipt", flow)
        self.assertIn("--export-dir", flow)
        self.assertIn("sha256sum --check", flow)
        self.assertIn("retention-days: 7", flow)
        self.assertIn("timeout-minutes: 12", flow)
        self.assertNotIn("pull_request_target", flow)
        self.assertNotIn("secrets.", flow)
        self.assertNotIn("supabase_service_role", flow)
        self.assertNotIn("git push", flow)
        self.assertNotIn("| bash", flow)
        self.assertNotIn("ollama pull", flow)


if __name__ == "__main__":
    unittest.main()
