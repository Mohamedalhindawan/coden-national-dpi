"""Contract tests for the on-disk V4 progress baseline fixture."""
import json
import unittest
from pathlib import Path
from scripts.validate_v4_progress import calculate_progress

BASELINE = Path(__file__).resolve().parents[1] / "enterprise/performance/v4-progress-baseline.json"

class BaselineFixtureTests(unittest.TestCase):
    def test_baseline_is_valid_json(self):
        with BASELINE.open(encoding="utf-8") as f:
            baseline = json.load(f)
        self.assertEqual(baseline["playbook_version"], "4.0")
        self.assertEqual({p["id"] for p in baseline["phases"]}, {f"P{i}" for i in range(1, 9)})

    def test_unapproved_baseline_does_not_fabricate_percentage(self):
        with BASELINE.open(encoding="utf-8") as f:
            result = calculate_progress(json.load(f))
        self.assertEqual(result["status"], "not_measurable")
        self.assertIsNone(result["completion_percent"])
        self.assertIsNone(result["remaining_percent"])

if __name__ == "__main__":
    unittest.main()
