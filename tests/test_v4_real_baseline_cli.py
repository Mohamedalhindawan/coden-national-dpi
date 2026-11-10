"""Integration gate: repository's real unapproved baseline must never yield percentages."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE = ROOT / "enterprise" / "governance"


class RealBaselineCLITests(unittest.TestCase):
    def test_real_baseline_remains_unmeasurable(self):
        baseline = GOVERNANCE / "v4-measurement-baseline.json"
        self.assertTrue(baseline.is_file(), "Repository baseline missing")
        source = json.loads(baseline.read_text(encoding="utf-8"))
        self.assertIs(source["source_verified"], False)
        proc = subprocess.run(
            [sys.executable, str(GOVERNANCE / "v4_progress_report.py"), str(baseline)],
            check=True, capture_output=True, text=True,
        )
        report = json.loads(proc.stdout)
        self.assertEqual(report["status"], "unmeasurable")
        self.assertEqual(set(report["domains"]), set(source["domains"]))
        for item in [report["overall"], *report["domains"].values()]:
            self.assertIsNone(item["completed_pct"])
            self.assertIsNone(item["remaining_pct"])
        self.assertNotIn("denominators", report)

    def test_real_baseline_is_not_modified_by_cli(self):
        baseline = GOVERNANCE / "v4-measurement-baseline.json"
        before = baseline.read_bytes()
        subprocess.run([sys.executable, str(GOVERNANCE / "v4_progress_report.py"), str(baseline)], check=True, capture_output=True, text=True)
        self.assertEqual(baseline.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
