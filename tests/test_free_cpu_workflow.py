"""Contract for a one-shot no-secrets GitHub Actions REAL CPU model trial."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FLOW = ROOT / ".github" / "workflows" / "factory-free-cpu-pilot.yml"
TASK = ROOT / "ai_factory" / "examples" / "free-cpu-list-length.json"


class FreeCpuWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.flow = FLOW.read_text(encoding="utf-8").lower()
        cls.task = TASK.read_text(encoding="utf-8").lower()

    def test_uses_only_pinned_upstream_real_cpu_assets(self):
        self.assertIn("llama-b12600-bin-ubuntu-x64.tar.gz", self.flow)
        self.assertIn("da524c71f9dd09913df29264bb7229b99a2de82d8a26e6902e6921d413560d6d", self.flow)
        self.assertIn("qwen2.5-coder-0.5b-instruct-q4_k_m.gguf", self.flow)
        self.assertIn("1d9614638d18024d0fbb36575a15f1302a3adf044df10345688ec4f6e1c4ff32", self.flow)
        self.assertIn("ebb2015119c907b064c512bf053e945850b5875f", self.flow)
        self.assertIn("sha256sum --check", self.flow)

    def test_gates_budget_repo_and_model_execution(self):
        self.assertIn("permissions:\n  contents: read", self.flow)
        self.assertIn("timeout-minutes:", self.flow)
        self.assertIn("feat/factory-free-cpu-real-inference-20261123", self.flow)
        self.assertNotIn("pull_request_target", self.flow)
        self.assertNotIn("secrets.", self.flow)
        self.assertNotIn("curl -fs", self.flow.replace("curl -fs\n", ""))  # no installation pipe
        self.assertNotIn("| bash", self.flow)
        self.assertNotIn("ollama pull", self.flow)
        self.assertNotIn("supabase_service_role", self.flow)

    def test_invokes_actual_factory_and_checkpoints_independent_review(self):
        self.assertIn("python -m ai_factory.project", self.flow)
        self.assertIn("--local-model", self.flow)
        self.assertIn("python -m ai_factory.free_cpu_receipt", self.flow)
        self.assertIn("--result", self.flow)
        self.assertIn("factory-free-cpu-pilot.yml", self.flow)
        self.assertIn('"recipe": "python-transform"', self.task)
        self.assertIn('"data_classification": "synthetic"', self.task)
        self.assertIn('"estimated_cost_usd": 0', self.task)


if __name__ == "__main__":
    unittest.main()
