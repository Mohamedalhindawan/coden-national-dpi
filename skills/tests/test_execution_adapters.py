import unittest

from skills.orchestration.adapters import AdapterRegistry, AdapterError
from skills.orchestration.adapters.dry_run import DryRunAdapter

class AdapterRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = AdapterRegistry()
        self.registry.register("run_tests", DryRunAdapter())

    def test_registered_dry_run_adapter_returns_non_execution_receipt(self):
        receipt = self.registry.dispatch(
            tool_name="run_tests",
            task_id="task-01",
            run_id="run-01",
            payload={"fixture": "synthetic"},
            network="disabled",
            mode="dry_run",
        )
        self.assertEqual(receipt["status"], "simulated")
        self.assertFalse(receipt["executed"])
        self.assertEqual(receipt["tool_name"], "run_tests")

    def test_unknown_tool_is_rejected(self):
        with self.assertRaises(AdapterError):
            self.registry.dispatch("shell", "task-01", "run-01", {}, "disabled", "dry_run")

    def test_live_mode_is_rejected_even_for_registered_adapter(self):
        with self.assertRaises(AdapterError):
            self.registry.dispatch("run_tests", "task-01", "run-01", {}, "disabled", "live")

    def test_network_enabled_task_is_rejected(self):
        with self.assertRaises(AdapterError):
            self.registry.dispatch("run_tests", "task-01", "run-01", {}, "enabled", "dry_run")

    def test_adapter_receipt_cannot_claim_execution(self):
        class LyingAdapter:
            def execute(self, context):
                return {"status": "succeeded", "executed": True}
        registry = AdapterRegistry()
        registry.register("run_tests", LyingAdapter())
        with self.assertRaises(AdapterError):
            registry.dispatch("run_tests", "task-01", "run-01", {}, "disabled", "dry_run")

if __name__ == "__main__":
    unittest.main()
