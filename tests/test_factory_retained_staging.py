import unittest
from ai_factory import factory_staging_capacity as capacity


def record(name, compressed, expanded):
    return dict(name=name, compressed_bytes=compressed, expanded_bytes=expanded, members=1)


class RetainedStagingTest(unittest.TestCase):
    def test_retaining_inputs_can_exceed_budget_even_when_reclaim_fits(self):
        rows = [record('a', 80, 100), record('b', 20, 100)]
        self.assertTrue(capacity.plan_staging(rows, capacity_bytes=250, page_bytes=1)['fits_model'])
        result = capacity.plan_retained_staging(rows, capacity_bytes=250, page_bytes=1, additional_bytes=0)
        self.assertEqual(result['required_bytes'], 300)
        self.assertEqual(result['headroom_bytes'], -50)
        self.assertFalse(result['fits_model'])
        self.assertFalse(result['build_authorized'])

    def test_counts_source_output_allowance_and_reserve(self):
        result = capacity.plan_retained_staging([record('a', 5, 10)], capacity_bytes=40,
                                               page_bytes=4, additional_bytes=12, reserve_bytes=7)
        self.assertEqual(result['required_bytes'], 40)
        self.assertEqual(result['headroom_bytes'], 0)
        self.assertTrue(result['fits_model'])
        self.assertFalse(result['actual_peak_build_capacity_proven'])
        self.assertFalse(result['release_authorized'])

    def test_rejects_invalid_additional_allowance(self):
        for value in (-1, True, 1.5, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                capacity.plan_retained_staging([record('a', 5, 10)], additional_bytes=value)
