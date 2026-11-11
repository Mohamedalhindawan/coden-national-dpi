"""Fail-closed cost authorization for CODEN's future cloud agent runner."""
import unittest
from ai_factory.budget_guard import authorize_run


class BudgetGuardTests(unittest.TestCase):
    def test_requires_explicit_human_approval(self):
        self.assertFalse(authorize_run({"approved": False, "estimated_usd": 0, "max_usd": 1})["allowed"])

    def test_approved_bounded_run(self):
        self.assertTrue(authorize_run({"approved": True, "estimated_usd": 0.25, "max_usd": 1})["allowed"])

    def test_rejects_over_budget(self):
        self.assertFalse(authorize_run({"approved": True, "estimated_usd": 2, "max_usd": 1})["allowed"])

    def test_rejects_invalid_and_missing_values(self):
        for request in ({}, {"approved": True, "estimated_usd": -1, "max_usd": 1},
                        {"approved": 1, "estimated_usd": 0, "max_usd": 1},
                        {"approved": True, "estimated_usd": "0", "max_usd": 1},
                        {"approved": True, "estimated_usd": float("nan"), "max_usd": 1},
                        {"approved": True, "estimated_usd": 0, "max_usd": 0}):
            with self.subTest(request=request):
                self.assertFalse(authorize_run(request)["allowed"])
