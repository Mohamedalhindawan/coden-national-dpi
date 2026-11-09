"""Integration checks for the actual unapproved CODEN V4 baseline file.

These tests intentionally do not assert a fabricated completion percentage.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.validate_v4_progress import calculate_progress

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "enterprise" / "performance" / "v4-progress-baseline.json"


class RealBaselineIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = json.loads(BASELINE.read_text(encoding="utf-8"))

    def test_baseline_is_v4_and_has_eight_unique_phases(self):
        self.assertEqual(self.baseline["playbook_version"], "4.0")
        self.assertEqual({p["id"] for p in self.baseline["phases"]}, {f"P{i}" for i in range(1, 9)})
        self.assertEqual(len(self.baseline["phases"]), 8)

    def test_unapproved_baseline_never_claims_percentages(self):
        result = calculate_progress(self.baseline)
        self.assertEqual(result["status"], "not_measurable")
        self.assertIsNone(result["completion_percent"])
        self.assertIsNone(result["remaining_percent"])

    def test_cli_reads_real_baseline_and_returns_no_fabricated_progress(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_v4_progress.py"), str(BASELINE)],
            cwd=ROOT, capture_output=True, text=True, check=True,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "not_measurable")
        self.assertIsNone(result["completion_percent"])
        self.assertIsNone(result["remaining_percent"])

    def test_no_accidental_approval_flags_in_baseline(self):
        for key in ("full_master_text_committed", "requirements_decomposed_and_audited", "weights_approved"):
            self.assertIs(self.baseline[key], False)
        self.assertIsNone(self.baseline["baseline_approved_by"])
        self.assertEqual(self.baseline["requirements"], [])


if __name__ == "__main__":
    unittest.main()
