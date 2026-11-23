"""Failing-first verification of a REAL (not fixture-backed) CPU model pilot."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from ai_factory import free_cpu_receipt


class FreeCpuReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.work = self.root / "coden-project-verified"
        self.work.mkdir()
        self.artifact = self.work / "candidate.pyz"
        self.artifact.write_bytes(b"synthetic generated package placeholder")
        self.sha = hashlib.sha256(self.artifact.read_bytes()).hexdigest()
        self.events = [
            {"role": "orchestrator", "state": "planned", "task_id": "FREE-CPU-LIST-LENGTH",
             "paid_calls": 0, "budget_usd": 0},
            {"role": "coding", "state": "complete",
             "input": "local Qwen2.5-Coder / llama.cpp b12600"},
            {"role": "testing", "state": "passed", "verified_cases": 2},
            {"role": "review", "state": "passed", "sha256": self.sha,
             "release_authorized": False, "review_cases": 2},
            {"role": "orchestrator", "state": "awaiting_human_review"},
        ]
        self.result = self.root / "result.json"
        self.result.write_text(json.dumps({
            "directory": str(self.work), "status": "awaiting_human_review"
        }))
        self.receipt = self.work / "review.json"
        self.receipt.write_text(json.dumps({
            "status": "awaiting_human_review", "sha256": self.sha,
            "review_cases": 2, "release_authorized": False
        }))
        self._write_events()

    def _write_events(self):
        (self.work / "events.jsonl").write_text(
            "".join(json.dumps(e) + "\n" for e in self.events)
        )

    def test_verifies_bounded_model_origin_and_heldout_review(self):
        result = free_cpu_receipt.inspect(self.result, self.root)
        self.assertEqual(result["status"], "awaiting_human_review")
        self.assertEqual(result["model"], "Qwen2.5-Coder-0.5B-Instruct-Q4_K_M")
        self.assertEqual(result["artifact_sha256"], self.sha)
        self.assertEqual(result["independent_review_cases"], 2)
        self.assertFalse(result["release_authorized"])

    def test_rejects_fixture_origin_without_model_invocation_evidence(self):
        self.events[1]["input"] = "built-in recipe"
        self._write_events()
        with self.assertRaises(ValueError):
            free_cpu_receipt.inspect(self.result, self.root)

    def test_rejects_tampered_review_or_release_authorization(self):
        value = json.loads(self.receipt.read_text())
        value["release_authorized"] = True
        self.receipt.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            free_cpu_receipt.inspect(self.result, self.root)

    def test_rejects_wrong_digest_and_cross_directory_result(self):
        self.artifact.write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            free_cpu_receipt.inspect(self.result, self.root)
        self.artifact.write_bytes(b"synthetic generated package placeholder")
        self.result.write_text(json.dumps({
            "directory": str(self.root.parent), "status": "awaiting_human_review"
        }))
        with self.assertRaises(ValueError):
            free_cpu_receipt.inspect(self.result, self.root)

    def test_rejects_nonzero_budget_and_missing_independent_tests(self):
        self.events[0]["budget_usd"] = 0.01
        self._write_events()
        with self.assertRaises(ValueError):
            free_cpu_receipt.inspect(self.result, self.root)
        self.events[0]["budget_usd"] = 0
        self.events[3]["review_cases"] = 0
        self._write_events()
        with self.assertRaises(ValueError):
            free_cpu_receipt.inspect(self.result, self.root)


    def test_exports_only_verified_generated_package_for_human_review(self):
        target = self.root / "human-review-export"
        summary = free_cpu_receipt.export_reviewed(self.result, self.root, target)
        self.assertEqual(summary["artifact_sha256"], self.sha)
        self.assertEqual({x.name for x in target.iterdir()},
                         {"candidate.pyz", "review.json", "model_receipt.json"})
        self.assertEqual((target / "candidate.pyz").read_bytes(),
                         b"synthetic generated package placeholder")
        self.assertFalse(json.loads((target / "model_receipt.json").read_text())["release_authorized"])

    def test_export_fails_closed_on_unreviewed_content(self):
        self.events[1]["input"] = "built-in recipe"
        self._write_events()
        target = self.root / "human-review-export"
        with self.assertRaises(ValueError):
            free_cpu_receipt.export_reviewed(self.result, self.root, target)
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
