"""Regression tests for V4 progress approval and evidence gates."""
import unittest
from scripts.validate_v4_progress import calculate_progress


def baseline():
    return {
        "full_master_text_committed": True,
        "requirements_decomposed_and_audited": True,
        "weights_approved": True,
        "baseline_approved_by": "Independent reviewer",
        "phases": [{"id": f"P{i}", "approved_weight": 0.125} for i in range(1, 9)],
        "requirements": [
            {"id": f"REQ-{i}", "phase": f"P{i}", "weight": 1, "score": 0.25}
            for i in range(1, 9)
        ],
    }


class ProgressApprovalEvidenceTests(unittest.TestCase):
    def test_no_approval_does_not_publish_percentage(self):
        b = baseline()
        b["baseline_approved_by"] = ""
        self.assertEqual(calculate_progress(b)["status"], "not_measurable")

    def test_all_eight_phases_required(self):
        b = baseline()
        b["phases"].pop()
        with self.assertRaises(ValueError):
            calculate_progress(b)

    def test_evidence_gate_for_implementation(self):
        b = baseline()
        b["requirements"][0]["score"] = 0.5
        with self.assertRaises(ValueError):
            calculate_progress(b)

    def test_critical_blocker_caps_score(self):
        b = baseline()
        b["requirements"][0].update(score=0.75, evidence_url="https://github.com/example/evidence", critical_blocker=True)
        with self.assertRaises(ValueError):
            calculate_progress(b)

    def test_weighted_percentages_sum_to_hundred(self):
        b = baseline()
        r = calculate_progress(b)
        self.assertEqual(r["completion_percent"], 25.0)
        self.assertEqual(r["remaining_percent"], 75.0)
        self.assertEqual(r["completion_percent"] + r["remaining_percent"], 100.0)


if __name__ == "__main__":
    unittest.main()
