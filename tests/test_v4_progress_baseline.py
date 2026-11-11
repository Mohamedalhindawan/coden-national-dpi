"""Synthetic tests only; these are not an approved V4 requirements inventory."""
import unittest
from copy import deepcopy
from scripts.v4_progress import calculate

def sample():
    names = ["governance_docs", "ai_factory", "tamam_dpi", "security_ops"]
    return [{"id": f"S{i}", "phase": i, "domain": names[(i-1) % 4],
             "weight": 1, "accepted": False, "evidence": [], "tests": [],
             "human_approval": False} for i in range(1, 9)]

class ProgressGateTests(unittest.TestCase):
    def test_missing_baseline_fails_closed(self):
        self.assertIsNone(calculate([]))
        self.assertIsNone(calculate(sample()[:-1]))
    def test_unverified_acceptance_fails_closed(self):
        rows = sample()
        rows[0]["accepted"] = True
        self.assertIsNone(calculate(rows))
    def test_duplicate_id_fails_closed(self):
        rows = sample()
        rows[1]["id"] = rows[0]["id"]
        self.assertIsNone(calculate(rows))
    def test_nonfinite_or_negative_weight_fails_closed(self):
        for value in ("NaN", "Infinity", -1, 0):
            rows = sample()
            rows[0]["weight"] = value
            self.assertIsNone(calculate(rows))
    def test_verified_weighted_progress_and_complement(self):
        rows = sample()
        rows[0].update(accepted=True, human_approval=True,
                       evidence=["reviewed-commit"], tests=["passing-ci"])
        rows[0]["weight"] = 2
        result = calculate(rows)
        self.assertEqual(result["completed"], "22.22")
        self.assertEqual(result["remaining"], "77.78")
        self.assertEqual(result["domains"]["governance_docs"], "66.67")
        self.assertEqual(result["denominator"], "9")
    def test_boolean_phase_rejected(self):
        rows = sample()
        rows[0]["phase"] = True
        self.assertIsNone(calculate(rows))

if __name__ == "__main__":
    unittest.main()
