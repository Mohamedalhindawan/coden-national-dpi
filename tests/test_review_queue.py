"""Tests for atomic synthetic-only review queue."""
import json
import tempfile
import unittest
from pathlib import Path
from ai_factory.review_queue import prepare_review_queue, main


class ReviewQueueTests(unittest.TestCase):
    def test_two_tasks_generate_reviewable_plans_without_authorization(self):
        tasks = [
            {'id': 'T-1', 'title': 'Demo', 'description': 'Synthetic', 'data_classification': 'synthetic', 'requested_actions': ['run_tests']},
            {'id': 'T-2', 'title': 'Other', 'description': 'Synthetic', 'data_classification': 'synthetic', 'requested_actions': ['read_repository']},
        ]
        result = prepare_review_queue(tasks)
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['plans']), 2)
        self.assertTrue(all(not plan['execution_authorized'] for plan in result['plans']))

    def test_atomic_rejection_for_bad_task(self):
        tasks = [
            {'id': 'T-1', 'title': 'Demo', 'description': 'Synthetic', 'data_classification': 'synthetic', 'requested_actions': ['run_tests']},
            {'id': 'T-2', 'title': 'Bad', 'description': 'Citizen', 'data_classification': 'personal', 'requested_actions': ['merge_main']},
        ]
        result = prepare_review_queue(tasks)
        self.assertFalse(result['valid'])
        self.assertEqual(result['plans'], [])
        self.assertEqual(result['errors'][0]['index'], 1)

    def test_reject_duplicate_ids_and_nonlist(self):
        task = {'id': 'T', 'title': 'x', 'description': 'y', 'data_classification': 'synthetic', 'requested_actions': ['run_tests']}
        self.assertFalse(prepare_review_queue([task, task])['valid'])
        self.assertFalse(prepare_review_queue({})['valid'])

    def test_cli_reads_and_outputs_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'tasks.json'
            path.write_text(json.dumps([{'id': 'T', 'title': 'x', 'description': 'y', 'data_classification': 'synthetic', 'requested_actions': ['run_tests']}]))
            self.assertEqual(main([str(path)]), 0)
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), ['tasks.json'])

    def test_cli_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'tasks.json'
            path.write_text('{broken')
            self.assertEqual(main([str(path)]), 1)

    def test_budget_ceiling_allows_only_estimated_batches_within_limit(self):
        tasks = [
            {'id': 'B1', 'title': 'Demo', 'description': 'Synthetic', 'data_classification': 'synthetic', 'requested_actions': ['run_tests'], 'estimated_cost_usd': '0.10'},
            {'id': 'B2', 'title': 'Demo2', 'description': 'Synthetic', 'data_classification': 'synthetic', 'requested_actions': ['run_tests'], 'estimated_cost_usd': '0.20'},
        ]
        result = prepare_review_queue(tasks, budget_usd='0.30')
        self.assertTrue(result['valid'])
        self.assertTrue(all(not p['execution_authorized'] for p in result['plans']))
        self.assertFalse(prepare_review_queue(tasks, budget_usd='0.29')['valid'])

    def test_budget_fail_closed_for_missing_negative_nan_and_bad_limit(self):
        task = {'id': 'B1', 'title': 'Demo', 'description': 'Synthetic', 'data_classification': 'synthetic', 'requested_actions': ['run_tests']}
        self.assertFalse(prepare_review_queue([task], budget_usd='1')['valid'])
        for value in ['-1', 'NaN', 'Infinity', True]:
            self.assertFalse(prepare_review_queue([{**task, 'estimated_cost_usd': value}], budget_usd='1')['valid'])
        for limit in ['-1', 'NaN', 'not-a-number']:
            self.assertFalse(prepare_review_queue([{**task, 'estimated_cost_usd': '0'}], budget_usd=limit)['valid'])

    def test_budget_cli_rejects_overspend(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'tasks.json'
            path.write_text(json.dumps([{'id': 'B1', 'title': 'Demo', 'description': 'Synthetic', 'data_classification': 'synthetic', 'requested_actions': ['run_tests'], 'estimated_cost_usd': '1.01'}]))
            self.assertEqual(main([str(path), '--budget-usd', '1.00']), 1)

    def test_rejects_whitespace_alias_ids_atomically(self):
        base = {'title': 'Demo', 'description': 'Synthetic', 'data_classification': 'synthetic', 'requested_actions': ['run_tests']}
        tasks = [{**base, 'id': 'TASK-1'}, {**base, 'id': ' TASK-1 '}]
        result = prepare_review_queue(tasks)
        self.assertFalse(result['valid'])
        self.assertEqual(result['plans'], [])
        self.assertIn({'index': 1, 'reason': 'duplicate task id'}, result['errors'])

    def test_rejects_ambiguous_whitespace_id_without_alias(self):
        task = {'id': ' TASK-1 ', 'title': 'Demo', 'description': 'Synthetic', 'data_classification': 'synthetic', 'requested_actions': ['run_tests']}
        result = prepare_review_queue([task])
        self.assertFalse(result['valid'])
        self.assertEqual(result['plans'], [])
        self.assertIn({'index': 0, 'reason': 'task id must be canonical (no surrounding whitespace)'}, result['errors'])
