import unittest
from ai_factory import factory_staging_capacity as capacity


class ReadonlyStagingTest(unittest.TestCase):
    def test_separate_input_and_writable_budgets(self):
        rows = [dict(name='a', compressed_bytes=80, expanded_bytes=100, members=1),
                dict(name='b', compressed_bytes=20, expanded_bytes=100, members=1)]
        result = capacity.plan_readonly_staging(rows, input_capacity_bytes=100,
                                              capacity_bytes=240, page_bytes=1,
                                              additional_bytes=20, reserve_bytes=10)
        self.assertEqual(result['readonly_input_bytes'], 100)
        self.assertEqual(result['required_writable_bytes'], 230)
        self.assertEqual(result['writable_headroom_bytes'], 10)
        self.assertTrue(result['fits_model'])
        self.assertFalse(result['readonly_boundary_verified'])
        self.assertFalse(result['build_authorized'])
        self.assertFalse(result['release_authorized'])

    def test_either_budget_can_fail(self):
        rows = [dict(name='a', compressed_bytes=80, expanded_bytes=100, members=1)]
        for inputs, writable in ((79, 100), (80, 99)):
            with self.subTest(inputs=inputs, writable=writable):
                self.assertFalse(capacity.plan_readonly_staging(
                    rows, input_capacity_bytes=inputs, capacity_bytes=writable,
                    page_bytes=1, additional_bytes=0)['fits_model'])

    def test_invalid_independent_input_budget_rejected(self):
        rows = [dict(name='a', compressed_bytes=1, expanded_bytes=1, members=1)]
        for value in (0, -1, True, 1.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                capacity.plan_readonly_staging(rows, input_capacity_bytes=value,
                                               additional_bytes=0)
