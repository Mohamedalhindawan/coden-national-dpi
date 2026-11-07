import unittest

from skills.orchestration.adapters import AdapterRegistry, AdapterError
from skills.orchestration.adapters.dry_run import DryRunAdapter

class AdapterRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = AdapterRegistry()
        self.registry.register("run_tests", DryRunAdapter())

    @staticmethod
    def task():
        return {
            "contract_version": "1.0.0", "run_id": "run-01", "task_id": "task-01",
            "role_id": "QA-01", "owner": "owner", "objective": "test",
            "inputs": [{"artifact_id": "fixture", "uri": "workspace://fixture.json", "classification": "synthetic"}],
            "constraints": {"allowed_tools": ["read_workspace", "run_tests"], "network": "disabled",
                            "write_scope": [], "max_runtime_seconds": 30, "max_retries": 0},
            "acceptance_criteria": ["record"], "deadline": "2026-12-01T00:00:00Z", "status": "ready"
        }

    def test_registered_dry_run_adapter_returns_non_execution_receipt(self):
        receipt = self.registry.dispatch(
            task=self.task(),
            tool_name="run_tests",
            payload={"fixture": "synthetic"},
            mode="dry_run",
        )
        self.assertEqual(receipt["status"], "simulated")
        self.assertFalse(receipt["executed"])
        self.assertEqual(receipt["tool_name"], "run_tests")

    def test_unknown_tool_is_rejected(self):
        with self.assertRaises(AdapterError):
            self.registry.dispatch(self.task(), "shell", {})

    def test_live_mode_is_rejected_even_for_registered_adapter(self):
        with self.assertRaises(AdapterError):
            self.registry.dispatch(self.task(), "run_tests", {}, mode="live")

    @classmethod
    def task_with_network(cls, network):
        task = cls.task()
        task["constraints"]["network"] = network
        return task

    def test_network_enabled_task_is_rejected(self):
        with self.assertRaises(AdapterError):
            self.registry.dispatch(self.task_with_network("enabled"), "run_tests", {})

    def test_adapter_receipt_cannot_claim_execution(self):
        class LyingAdapter:
            def execute(self, context):
                return {"status": "succeeded", "executed": True}
        registry = AdapterRegistry()
        registry.register("run_tests", LyingAdapter())
        with self.assertRaises(AdapterError):
            registry.dispatch(self.task(), "run_tests", {})

if __name__ == "__main__":
    unittest.main()
