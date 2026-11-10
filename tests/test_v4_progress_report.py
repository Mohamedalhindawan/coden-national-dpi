"""Regression tests for the read-only, fail-closed report."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "enterprise" / "governance"))
from v4_progress_report import build_report
from v4_domain_progress import DOMAINS


class ReportTests(unittest.TestCase):
    def test_missing_source_fails_closed(self):
        report = build_report({"source_verified": False, "phases": []})
        self.assertEqual(report["status"], "unmeasurable")
        self.assertIsNone(report["overall"]["completed_pct"])
        self.assertEqual(set(report["domains"]), set(DOMAINS))
        self.assertTrue(all(v["remaining_pct"] is None for v in report["domains"].values()))

    def test_malformed_manifest_fails_closed(self):
        self.assertEqual(build_report({})["status"], "unmeasurable")

    def test_valid_synthetic_evidence(self):
        phases = []
        for i in range(8):
            domain = DOMAINS[i % 4]
            phases.append({"id": f"V4-P{i+1}", "verified": True, "title": f"Synthetic phase {i+1}", "weight": 1,
                           "requirements": [{"id": f"SYN-{i}", "domain": domain, "completed": i % 2 == 0,
                                             "human_accepted": True, "reviewed_evidence": "synthetic-evidence",
                                             "executed_tests": "synthetic-test", "acceptance_reference": "synthetic-approval"}]})
        report = build_report({"source_verified": True, "phases": phases, "domains": list(DOMAINS)})
        self.assertEqual(report["status"], "measurable")
        self.assertEqual(report["overall"], {"completed_pct": 50.0, "remaining_pct": 50.0})
        self.assertEqual(report["domains"][DOMAINS[0]]["completed_pct"], 100.0)
        self.assertEqual(report["domains"][DOMAINS[1]]["completed_pct"], 0.0)
        self.assertEqual(sum(report["denominators"].values()), 8)

    def test_cli_emits_nulls_without_claiming_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "baseline.json"
            path.write_text(json.dumps({"source_verified": False, "phases": []}), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(ROOT / "enterprise/governance/v4_progress_report.py"), str(path)], capture_output=True, text=True, check=True)
            data = json.loads(proc.stdout)
            self.assertIsNone(data["overall"]["remaining_pct"])


if __name__ == "__main__":
    unittest.main()
