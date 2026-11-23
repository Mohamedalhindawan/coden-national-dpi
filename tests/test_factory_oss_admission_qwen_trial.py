"""TDD contract for actual factory OSS admission gate improvement with real CPU Qwen.

This contract is *not* evidence of model execution. Only GitHub's successful
pinned workflow with an artifact+receipt can establish a real inference run.
"""
import json
from pathlib import Path
import unittest

from ai_factory import project, local_coder

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "ai_factory" / "examples" / "factory-oss-admission-blockers.json"
WORKFLOW = ROOT / ".github" / "workflows" / "factory-oss-admission-qwen.yml"


class FactoryOSSAdmissionQwenTrialTests(unittest.TestCase):
    def test_real_factory_development_task_is_distinct_and_synthetic(self):
        task = json.loads(TASK.read_text(encoding="utf-8"))
        self.assertTrue(project.valid(task))
        self.assertEqual(task["id"], "CODEN-OSS-ADMISSION-BLOCKERS-02")
        self.assertEqual(task["recipe"], "python-transform")
        self.assertEqual(task["data_classification"], "synthetic")
        self.assertEqual(task["estimated_cost_usd"], 0)
        self.assertEqual(task["requested_actions"], ["run_tests"])
        self.assertEqual(len(task["cases"]), 3)
        self.assertEqual(len(task["review_cases"]), 3)
        self.assertEqual(task["cases"][0], {"input": [], "expected": 0})
        self.assertEqual(task["cases"][1]["expected"], 2)
        self.assertEqual(task["review_cases"][0]["expected"], 3)
        self.assertIn("license_pending", task["description"])
        self.assertIn("security_pending", task["description"])
        self.assertNotIn("https://", task["description"])

    def test_workflow_requires_real_pinned_qwen_not_fake_fallback(self):
        flow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("feat/factory-oss-admission-metric-real-qwen-20261123", flow)
        self.assertIn("ai_factory/examples/factory-oss-admission-blockers.json", flow)
        self.assertIn("python -m ai_factory.project", flow)
        self.assertIn("python -m ai_factory.free_cpu_receipt", flow)
        self.assertIn("python -m ai_factory.factory_failure_diagnostic", flow)
        self.assertIn("coden-qwen-oss-admission-blockers", flow)
        self.assertIn(local_coder.CPU_SHA, flow)
        self.assertIn(local_coder.MODEL_SHA, flow)
        self.assertIn("CODEN_REQUIRE_SANDBOX", flow)
        self.assertIn("persist-credentials: false", flow)
        self.assertIn("contents: read", flow)
        self.assertIn("release_authorized", flow)
        self.assertNotIn("continue-on-error: true", flow)
        self.assertNotIn("pull_request_target:", flow)
        self.assertNotIn("actions/checkout@v", flow)

    def test_admission_flags_have_real_hidden_edge_cases(self):
        task = json.loads(TASK.read_text(encoding="utf-8"))
        examples = task["cases"] + task["review_cases"]
        def expected_count(value):
            return sum(
                1 for label in value if label in ("license_pending", "security_pending")
            )
        for case in examples:
            self.assertEqual(case["expected"], expected_count(case["input"]))
        self.assertEqual(
            len({project.encoded(x["input"]) for x in examples}), len(examples)
        )


if __name__ == "__main__":
    unittest.main()
