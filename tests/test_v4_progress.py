import unittest
from scripts.validate_v4_progress import calculate_progress

def baseline():
    return {"full_master_text_committed": True, "requirements_decomposed_and_audited": True, "weights_approved": True, "baseline_approved_by": "human", "phases": [{"id": f"P{i}", "approved_weight": .125} for i in range(1, 9)], "requirements": [{"id": f"R{i}", "phase": f"P{i}", "weight": 1, "score": .5, "evidence_url": "https://github.com/example/evidence"} for i in range(1, 9)]}

class ProgressTests(unittest.TestCase):
    def test_unapproved_is_not_measurable(self):
        b = baseline(); b["weights_approved"] = False
        self.assertIsNone(calculate_progress(b)["completion_percent"])
    def test_balanced_score(self):
        self.assertEqual(calculate_progress(baseline())["remaining_percent"], 50.0)
    def test_missing_evidence_rejected(self):
        b = baseline(); del b["requirements"][0]["evidence_url"]
        with self.assertRaises(ValueError): calculate_progress(b)
    def test_duplicate_requirement_rejected(self):
        b = baseline(); b["requirements"][1]["id"] = "R1"
        with self.assertRaises(ValueError): calculate_progress(b)
    def test_invalid_phase_weights_rejected(self):
        b = baseline(); b["phases"][0]["approved_weight"] = .2
        with self.assertRaises(ValueError): calculate_progress(b)
    def test_critical_blocker_rejected(self):
        b = baseline(); b["requirements"][0]["critical_blocker"] = True
        with self.assertRaises(ValueError): calculate_progress(b)
    def test_no_requirements_rejected(self):
        b = baseline(); b["requirements"] = []
        with self.assertRaises(ValueError): calculate_progress(b)
    def test_all_zero(self):
        b = baseline()
        for r in b["requirements"]: r["score"] = 0
        self.assertEqual(calculate_progress(b)["remaining_percent"], 100.0)

    def test_boolean_score_rejected(self):
        b = baseline(); b["requirements"][0]["score"] = True
        with self.assertRaises(ValueError): calculate_progress(b)
    def test_nonfinite_phase_weight_rejected(self):
        b = baseline(); b["phases"][0]["approved_weight"] = float("nan")
        with self.assertRaises(ValueError): calculate_progress(b)
    def test_nonfinite_requirement_weight_rejected(self):
        b = baseline(); b["requirements"][0]["weight"] = float("inf")
        with self.assertRaises(ValueError): calculate_progress(b)
    def test_blank_evidence_rejected(self):
        b = baseline(); b["requirements"][0]["evidence_url"] = "  "
        with self.assertRaises(ValueError): calculate_progress(b)
    def test_non_https_evidence_rejected(self):
        b = baseline(); b["requirements"][0]["evidence_url"] = "javascript:alert(1)"
        with self.assertRaises(ValueError): calculate_progress(b)
    def test_duplicate_phase_rejected(self):
        b = baseline(); b["phases"][1]["id"] = "P1"
        with self.assertRaises(ValueError): calculate_progress(b)
