import unittest

from skills.orchestration.benchmark import (
    BenchmarkError, BenchmarkEvaluator, compare_providers, score_receipt
)


def case(case_id="DPI-01", version="1.0.0"):
    return {
        "case_id": case_id, "version": version, "domain": "dpi",
        "dataset_id": "synthetic-dataset-01", "criteria_version": "1.0",
        "acceptance_criteria": ["schema_valid", "evidence_present"],
        "minimum_sample_size": 3,
    }


def receipt(run_id="run-1", provider="provider-a", **changes):
    value = {
        "run_id": run_id, "case_id": "DPI-01", "case_version": "1.0.0",
        "dataset_id": "synthetic-dataset-01", "criteria_version": "1.0",
        "provider": provider, "status": "succeeded",
        "criterion_results": {"schema_valid": True, "evidence_present": True},
        "evidence_ref": "artifact://synthetic/report-01.json",
        "duration_ms": 1200, "cost_usd": 0.01,
        "policy_violations": 0, "retry_count": 0,
        "evaluation_date": "2026-11-07",
    }
    value.update(changes)
    return value


class BenchmarkTests(unittest.TestCase):
    def test_scores_receipt_deterministically(self):
        result = score_receipt(case(), receipt())
        self.assertEqual(result["quality_score"], 1.0)
        self.assertTrue(result["passed"])
        self.assertEqual(result["criteria_passed"], 2)

    def test_rejects_missing_evidence_for_success(self):
        with self.assertRaises(BenchmarkError):
            score_receipt(case(), receipt(evidence_ref=""))

    def test_rejects_case_version_mismatch(self):
        with self.assertRaises(BenchmarkError):
            score_receipt(case(version="2.0.0"), receipt())

    def test_rejects_invalid_metric_ranges(self):
        for changes in ({"duration_ms": -1}, {"cost_usd": -0.1},
                        {"policy_violations": -1}, {"retry_count": -1}):
            with self.subTest(changes=changes), self.assertRaises(BenchmarkError):
                score_receipt(case(), receipt(**changes))

    def test_evaluator_rejects_duplicate_run_ids(self):
        evaluator = BenchmarkEvaluator([case()])
        evaluator.ingest(receipt())
        with self.assertRaises(BenchmarkError):
            evaluator.ingest(receipt())

    def test_comparison_rejects_different_case_versions(self):
        rows = [score_receipt(case(), receipt()),
                score_receipt(case(version="2.0.0"),
                              receipt(run_id="run-2", case_version="2.0.0"))]
        with self.assertRaises(BenchmarkError):
            compare_providers(rows)

    def test_comparison_reports_insufficient_data_without_ranking(self):
        rows = [score_receipt(case(), receipt())]
        result = compare_providers(rows)
        self.assertEqual(result["status"], "insufficient_data")
        self.assertIsNone(result["ranking"])
        self.assertEqual(result["providers"][0]["sample_size"], 1)

    def test_comparison_requires_same_benchmark_definition(self):
        rows = [score_receipt(case(), receipt()),
                score_receipt(case(), receipt(run_id="run-2", provider="provider-b"))]
        rows[1]["dataset_id"] = "different-dataset"
        with self.assertRaises(BenchmarkError):
            compare_providers(rows)


if __name__ == "__main__":
    unittest.main()
