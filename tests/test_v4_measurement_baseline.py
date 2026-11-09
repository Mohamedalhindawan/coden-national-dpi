"""Ensure an unverified V4 baseline never produces fabricated completion figures."""
import json
import unittest
from pathlib import Path

MANIFEST = Path(__file__).resolve().parents[1] / "enterprise/governance/v4-measurement-baseline.json"

def completion_rates(data):
    phases = data["phases"]
    if not data.get("source_verified") or len(phases) != 8:
        return None
    if any(not p.get("verified") or p.get("weight") is None or not p.get("requirements") for p in phases):
        return None
    if any(not r.get("reviewed_evidence") or not r.get("executed_tests") or r.get("human_accepted") is not True for p in phases for r in p["requirements"] if r.get("completed")):
        return None
    weights = [p["weight"] for p in phases]
    if any(type(w) not in (int, float) or w <= 0 for w in weights):
        return None
    total = sum(weights)
    done = sum(p["weight"] * sum(1 for r in p["requirements"] if r.get("completed")) / len(p["requirements"]) for p in phases)
    percent = round(100 * done / total, 2)
    return percent, round(100 - percent, 2)

class BaselineTests(unittest.TestCase):
    def test_eight_unverified_phases(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual([p["id"] for p in data["phases"]], [f"V4-P{i}" for i in range(1, 9)])
        self.assertFalse(data["source_verified"])
        self.assertIsNone(completion_rates(data))

    def test_missing_evidence_blocks_measurement(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        data["source_verified"] = True
        for p in data["phases"]:
            p.update(weight=1, verified=True, requirements=[{"completed":True}])
        self.assertIsNone(completion_rates(data))

    def test_verified_fixture_complements_to_100(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        data["source_verified"] = True
        for i, p in enumerate(data["phases"]):
            p.update(weight=1, verified=True, requirements=[{"completed":i < 4, "reviewed_evidence":"commit:fixture", "executed_tests":"test:fixture", "human_accepted":True}])
        self.assertEqual(completion_rates(data), (50.0, 50.0))

if __name__ == "__main__":
    unittest.main()
