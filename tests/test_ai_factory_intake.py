"""Behavioral tests for the synthetic-only AI factory intake vertical slice."""
import unittest
from ai_factory.intake import validate_intake, make_execution_plan


class IntakeTests(unittest.TestCase):
    def test_valid_synthetic_task(self):
        task = {'id': 'TASK-1', 'title': 'Build demo search', 'description': 'Synthetic-only catalog search', 'data_classification': 'synthetic', 'requested_actions': ['read_repository', 'write_branch']}
        self.assertTrue(validate_intake(task)['valid'])
        plan = make_execution_plan(task)
        self.assertEqual(plan['status'], 'awaiting_human_approval')
        self.assertFalse(plan['execution_authorized'])
        self.assertEqual(plan['steps'][-1], 'human_approval')

    def test_rejects_personal_data(self):
        self.assertFalse(validate_intake({'id': 'T-2', 'title': 'Read records', 'description': 'citizens', 'data_classification': 'personal', 'requested_actions': ['read_repository']})['valid'])

    def test_rejects_unsafe_actions(self):
        for action in ['merge_main', 'deploy_production', 'spend_money', 'expand_permissions', 'access_citizen_data']:
            with self.subTest(action=action):
                self.assertFalse(validate_intake({'id': 'T-3', 'title': 'Test task', 'description': 'synthetic', 'data_classification': 'synthetic', 'requested_actions': [action]})['valid'])

    def test_missing_and_invalid_fields(self):
        self.assertFalse(validate_intake({})['valid'])
        self.assertFalse(validate_intake({'id': 'T', 'title': ' ', 'description': 'a', 'data_classification': 'synthetic', 'requested_actions': []})['valid'])

    def test_no_automatic_execution(self):
        with self.assertRaises(ValueError):
            make_execution_plan({'id': 'X', 'title': 'unsafe', 'description': 'x', 'data_classification': 'real', 'requested_actions': ['deploy_production']})

    def test_rejects_non_dictionary(self):
        self.assertFalse(validate_intake(None)['valid'])
