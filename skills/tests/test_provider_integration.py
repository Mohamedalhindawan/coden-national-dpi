import unittest

from skills.orchestration.providers import (
    ProviderCatalog, ProviderProfile, ProviderPolicy, ProviderError,
    ProviderRequest, SimulatedProviderAdapter,
)


class ProviderIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.catalog = ProviderCatalog()
        self.catalog.register(ProviderProfile(
            provider_id="codex", display_name="Codex",
            capabilities=("coding", "testing"), secret_ref="secret://codex/api-key",
            enabled=True, mode="simulated",
        ))
        self.catalog.register_adapter("codex", SimulatedProviderAdapter())

    def test_catalog_never_returns_secret_values(self):
        profile = self.catalog.get("codex")
        self.assertEqual(profile["secret_ref"], "secret://codex/api-key")
        self.assertNotIn("api_key", profile)
        self.assertNotIn("secret_value", profile)

    def test_request_is_simulated_and_never_invokes_live_provider(self):
        request = ProviderRequest(
            request_id="req-1", provider_id="codex", capability="coding",
            task_id="task-1", data_classification="synthetic",
            payload={"prompt": "implement a fixture"},
        )
        receipt = self.catalog.dispatch(request, ProviderPolicy())
        self.assertEqual(receipt["status"], "simulated")
        self.assertFalse(receipt["provider_invoked"])
        self.assertFalse(receipt["network_used"])
        self.assertEqual(receipt["provider_id"], "codex")

    def test_sensitive_or_personal_data_is_rejected(self):
        for classification in ("sensitive", "personal"):
            request = ProviderRequest("req-x", "codex", "coding", "task-x",
                                      classification, {"prompt": "private"})
            with self.assertRaises(ProviderError):
                self.catalog.dispatch(request, ProviderPolicy())

    def test_unknown_provider_or_capability_is_rejected(self):
        request = ProviderRequest("req-2", "unknown", "coding", "task-2",
                                  "synthetic", {})
        with self.assertRaises(ProviderError):
            self.catalog.dispatch(request, ProviderPolicy())
        request = ProviderRequest("req-3", "codex", "medical_decision", "task-3",
                                  "synthetic", {})
        with self.assertRaises(ProviderError):
            self.catalog.dispatch(request, ProviderPolicy())

    def test_live_mode_and_network_are_fail_closed(self):
        request = ProviderRequest("req-4", "codex", "coding", "task-4",
                                  "synthetic", {})
        with self.assertRaises(ProviderError):
            self.catalog.dispatch(request, ProviderPolicy(mode="live"))
        with self.assertRaises(ProviderError):
            self.catalog.dispatch(request, ProviderPolicy(network="enabled"))

    def test_duplicate_request_id_is_rejected(self):
        request = ProviderRequest("req-5", "codex", "coding", "task-5",
                                  "synthetic", {})
        self.catalog.dispatch(request, ProviderPolicy())
        with self.assertRaises(ProviderError):
            self.catalog.dispatch(request, ProviderPolicy())

    def test_secret_reference_must_be_a_reference_not_a_credential(self):
        with self.assertRaises(ProviderError):
            ProviderProfile("unsafe", "Unsafe", ("coding",), "sk-live-plaintext",
                            True, "simulated")


if __name__ == "__main__":
    unittest.main()
