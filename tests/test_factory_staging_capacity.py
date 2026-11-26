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


    def test_reclaim_first_order_avoids_false_capacity_rejection(self):
        records = [item("large", 100, 90), item("reclaim", 80, 1)]
        result = plan_staging(records, capacity_bytes=200, page_bytes=1)
        self.assertEqual([s["name"] for s in result["steps"]], ["reclaim", "large"])
        self.assertEqual(result["peak_bytes"], 191)
        self.assertTrue(result["fits_model"])
        self.assertFalse(result["actual_peak_build_capacity_proven"])
        self.assertFalse(result["build_authorized"])

    def test_order_minimizes_model_peak_against_exhaustive_small_cases(self):
        from itertools import permutations, product
        # Exhaustive oracle for three archives with positive/negative/zero deltas.
        for sizes in product(((1, 4), (4, 1), (2, 2), (4, 3), (3, 5)), repeat=3):
            records = [item(str(i), c, e) for i, (c, e) in enumerate(sizes)]
            def peak(order):
                current = highest = sum(c for c, e in sizes)
                for c, e in order:
                    highest = max(highest, current + e)
                    current += e - c
                return highest
            self.assertEqual(plan_staging(records, page_bytes=1)["peak_bytes"],
                             min(peak(order) for order in permutations(sizes)), sizes)
