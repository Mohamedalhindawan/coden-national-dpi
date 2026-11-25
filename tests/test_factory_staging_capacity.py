import unittest
from ai_factory.factory_staging_capacity import plan_staging


def item(name, compressed=4096, expanded=8192, members=1):
    return dict(name=name, compressed_bytes=compressed,
                expanded_bytes=expanded, members=members)


class StagingCapacityTest(unittest.TestCase):
    def test_accounting_and_release_order(self):
        result = plan_staging([item('small'), item('large', 8192, 16384, 2)],
                              capacity_bytes=65536, reserve_bytes=4096)
        self.assertEqual([s['name'] for s in result['steps']], ['large', 'small'])
        self.assertEqual(result['initial_bytes'], 12288)
        self.assertEqual(result['peak_bytes'], 40957)
        self.assertEqual(result['remaining_bytes'], 24579)
        self.assertTrue(result['fits_model'])
        self.assertFalse(result['build_authorized'])

    def test_capacity_and_reserve_fail_closed(self):
        self.assertFalse(plan_staging([item('a')], capacity_bytes=16384,
                                      reserve_bytes=4096)['fits_model'])

    def test_invalid_or_duplicate_input_rejected(self):
        for values in ([], [item('a'), item('a')], [item('a', -1)],
                       [item('a', True)], [item('a', members=0)]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                plan_staging(values)

    def test_deterministic_ties_and_no_mutation(self):
        records = [item('z'), item('a')]
        self.assertEqual([s['name'] for s in plan_staging(records)['steps']], ['a', 'z'])
        self.assertEqual(records, [item('z'), item('a')])

    def test_invalid_budget_rejected(self):
        for kwargs in ({'capacity_bytes': 0}, {'reserve_bytes': -1},
                       {'page_bytes': 3000}, {'reserve_bytes': 100, 'capacity_bytes': 99}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                plan_staging([item('a')], **kwargs)
