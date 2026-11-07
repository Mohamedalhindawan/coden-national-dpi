import unittest

from skills.orchestration.model_gateway import (
    ModelGateway, ModelProfile, ModelRequest, GatewayPolicy, GatewayError,
)


class ModelGatewayTests(unittest.TestCase):
    def setUp(self):
        self.gateway = ModelGateway()
        self.gateway.register_model(ModelProfile(
            model_id="model-a", provider_id="provider-a",
            capabilities=("coding", "reasoning"), context_window=32000,
            input_cost_per_1k=0.001, output_cost_per_1k=0.002,
            enabled=True,
        ))
        self.gateway.register_model(ModelProfile(
            model_id="model-b", provider_id="provider-b",
            capabilities=("coding",), context_window=8000,
            input_cost_per_1k=0.0005, output_cost_per_1k=0.001,
            enabled=True,
        ))

    def request(self, **changes):
        values = dict(request_id="r-1", task_id="t-1", capability="coding",
                      estimated_input_tokens=1000, max_output_tokens=1000,
                      max_cost_usd=0.01, data_classification="synthetic")
        values.update(changes)
        return ModelRequest(**values)

    def test_selects_eligible_model_within_budget_and_context(self):
        result = self.gateway.route(self.request(), GatewayPolicy())
        self.assertEqual(result["model_id"], "model-b")
        self.assertEqual(result["mode"], "simulated")
        self.assertFalse(result["provider_invoked"])
        self.assertFalse(result["network_used"])

    def test_rejects_budget_below_all_eligible_models(self):
        with self.assertRaises(GatewayError):
            self.gateway.route(self.request(max_cost_usd=0.0001), GatewayPolicy())

    def test_rejects_context_window_overflow(self):
        with self.assertRaises(GatewayError):
            self.gateway.route(self.request(estimated_input_tokens=33000), GatewayPolicy())

    def test_rejects_sensitive_and_personal_data(self):
        for classification in ("sensitive", "personal"):
            with self.assertRaises(GatewayError):
                self.gateway.route(self.request(data_classification=classification), GatewayPolicy())

    def test_rejects_live_mode_or_network(self):
        with self.assertRaises(GatewayError):
            self.gateway.route(self.request(), GatewayPolicy(mode="live"))
        with self.assertRaises(GatewayError):
            self.gateway.route(self.request(), GatewayPolicy(network="enabled"))

    def test_rejects_duplicate_request_ids(self):
        self.gateway.route(self.request(), GatewayPolicy())
        with self.assertRaises(GatewayError):
            self.gateway.route(self.request(), GatewayPolicy())

    def test_capability_and_disabled_model_are_enforced(self):
        with self.assertRaises(GatewayError):
            self.gateway.route(self.request(capability="medical_decision"), GatewayPolicy())
        self.gateway.set_enabled("model-b", False)
        result = self.gateway.route(self.request(request_id="r-2"), GatewayPolicy())
        self.assertEqual(result["model_id"], "model-a")

    def test_invalid_cost_metadata_is_rejected(self):
        with self.assertRaises(GatewayError):
            ModelProfile("bad", "p", ("coding",), 1000, -1, 0.1, True)


if __name__ == "__main__":
    unittest.main()
