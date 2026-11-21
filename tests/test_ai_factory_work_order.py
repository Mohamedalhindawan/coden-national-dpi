"""Tests for preparing a bounded, non-executable agent work order."""
import unittest
from ai_factory.work_order import prepare_work_order


class WorkOrderTests(unittest.TestCase):
    def setUp(self):
        self.task = {"id": "DEMO-1", "title": "Review catalog",
                     "description": "Use demo records only",
                     "data_classification": "synthetic",
                     "requested_actions": ["read_repository", "run_tests"]}

    def test_prepares_read_only_work_order(self):
        result = prepare_work_order(self.task, {"approved": True, "estimated_usd": 0, "max_usd": 1})
        self.assertTrue(result["ready_for_review"])
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["allowed_actions"], ["read_repository", "run_tests"])
        self.assertEqual(result["status"], "awaiting_execution_approval")

    def test_missing_approval_fails_closed(self):
        result = prepare_work_order(self.task, {"approved": False, "estimated_usd": 0, "max_usd": 1})
        self.assertFalse(result["ready_for_review"])
        self.assertFalse(result["execution_authorized"])

    def test_rejects_unsafe_task(self):
        bad = dict(self.task, requested_actions=["deploy_production"])
        result = prepare_work_order(bad, {"approved": True, "estimated_usd": 0, "max_usd": 1})
        self.assertFalse(result["ready_for_review"])

    def test_rejects_over_budget(self):
        result = prepare_work_order(self.task, {"approved": True, "estimated_usd": 3, "max_usd": 1})
        self.assertFalse(result["ready_for_review"])
