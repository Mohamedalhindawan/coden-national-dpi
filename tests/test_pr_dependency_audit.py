import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from pr_dependency_audit import audit


def pr(n, head, base):
    return {'number': n, 'head': {'ref': head}, 'base': {'ref': base}}


class AuditTests(unittest.TestCase):
    def test_stacked(self):
        x = audit([pr(2, 'second', 'first'), pr(1, 'first', 'main')])
        self.assertEqual(x['stacked'], [{'pr': 2, 'depends_on_pr': 1}])
        self.assertEqual(x['independent'], [1])

    def test_empty(self):
        self.assertEqual(audit([])['open_pr_count'], 0)

    def test_duplicate(self):
        with self.assertRaisesRegex(ValueError, 'duplicate head'):
            audit([pr(1, 'x', 'main'), pr(2, 'x', 'main')])

    def test_cycle(self):
        with self.assertRaisesRegex(ValueError, 'cycle'):
            audit([pr(1, 'x', 'y'), pr(2, 'y', 'x')])

    def test_non_list(self):
        with self.assertRaises(ValueError):
            audit({})

    def test_duplicate_pr_number_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate PR number'):
            audit([pr(1, 'a', 'main'), pr(1, 'b', 'main')])

    def test_malformed_record_rejected(self):
        with self.assertRaises(ValueError):
            audit([{'number': 1, 'head': None, 'base': {'ref': 'main'}}])

    def test_self_based_pr_rejected(self):
        with self.assertRaisesRegex(ValueError, 'cycle'):
            audit([pr(1, 'same', 'same')])

    def test_order_independent(self):
        self.assertEqual(audit([pr(3, 'c', 'b'), pr(2, 'b', 'a'), pr(1, 'a', 'main')])['stacked'], [{'pr': 2, 'depends_on_pr': 1}, {'pr': 3, 'depends_on_pr': 2}])


if __name__ == '__main__':
    unittest.main()
