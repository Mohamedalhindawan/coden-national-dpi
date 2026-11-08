import unittest

from skills.orchestration.routing import (
    RoutingError, recommend_route, validate_route_policy
)


class RoutingTests(unittest.TestCase):
    def profile(self, **changes):
        value = {
            "task_type": "software_implementation",
            "risk_level": "low",
            "data_classification": "synthetic",
            "network_required": False,
            "requires_code_execution": True,
            "requires_human_approval": False,
            "provider": "codex",
        }
        value.update(changes)
        return value

    def test_recommends_role_and_adapter_without_executing(self):
        result = recommend_route(self.profile())
        self.assertEqual(result["agent_role"], "DEV-01")
        self.assertEqual(result["execution_mode"], "dry_run")
        self.assertFalse(result["provider_invoked"])
        self.assertTrue(result["human_approval_required"])

    def test_high_impact_task_requires_human_approval(self):
        result = recommend_route(self.profile(
            task_type="benefits_decision", risk_level="high",
            data_classification="sensitive", requires_human_approval=False
        ))
        self.assertTrue(result["human_approval_required"])
        self.assertEqual(result["execution_mode"], "recommendation_only")

    def test_rejects_real_personal_data(self):
        with self.assertRaises(RoutingError):
            recommend_route(self.profile(data_classification="personal"))

    def test_rejects_unknown_task_type(self):
        with self.assertRaises(RoutingError):
            recommend_route(self.profile(task_type="unknown"))

    def test_rejects_network_required_route(self):
        with self.assertRaises(RoutingError):
            recommend_route(self.profile(network_required=True))

    def test_provider_name_is_not_a_quality_ranking(self):
        result = recommend_route(self.profile(provider="manus"))
        self.assertEqual(result["provider"], "manus")
        self.assertEqual(result["provider_selection_basis"], "user_supplied")
        self.assertNotIn("provider_score", result)

    def test_policy_validator_rejects_unsafe_execution(self):
        route = recommend_route(self.profile())
        route["execution_mode"] = "live"
        with self.assertRaises(RoutingError):
            validate_route_policy(route)


if __name__ == "__main__":
    unittest.main()
