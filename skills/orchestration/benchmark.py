"""Deterministic, evidence-gated benchmark scoring; never executes providers."""
import math


class BenchmarkError(ValueError):
    pass


def _nonnegative_number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BenchmarkError(f"{field} must be numeric")
    if not math.isfinite(value) or value < 0:
        raise BenchmarkError(f"{field} must be finite and non-negative")
    return float(value)


def _nonnegative_int(value, field):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise BenchmarkError(f"{field} must be a non-negative integer")
    return value


def score_receipt(benchmark_case, receipt):
    if not isinstance(benchmark_case, dict) or not isinstance(receipt, dict):
        raise BenchmarkError("case and receipt must be objects")
    required_case = ("case_id", "version", "dataset_id", "criteria_version",
                     "acceptance_criteria", "minimum_sample_size")
    required_receipt = ("run_id", "case_id", "case_version", "dataset_id",
                        "criteria_version", "provider", "status",
                        "criterion_results", "evidence_ref", "evaluation_date")
    if any(k not in benchmark_case for k in required_case):
        raise BenchmarkError("benchmark case is missing required fields")
    if any(k not in receipt for k in required_receipt):
        raise BenchmarkError("receipt is missing required fields")
    for key, expected in (("case_id", benchmark_case["case_id"]),
                          ("case_version", benchmark_case["version"]),
                          ("dataset_id", benchmark_case["dataset_id"]),
                          ("criteria_version", benchmark_case["criteria_version"])):
        if receipt[key] != expected:
            raise BenchmarkError(f"{key} does not match benchmark definition")
    if not isinstance(receipt["run_id"], str) or not receipt["run_id"].strip():
        raise BenchmarkError("run_id is required")
    if not isinstance(receipt["provider"], str) or not receipt["provider"].strip():
        raise BenchmarkError("provider is required")
    if receipt["status"] not in {"succeeded", "failed", "blocked", "cancelled"}:
        raise BenchmarkError("unsupported status")
    criteria = benchmark_case["acceptance_criteria"]
    results = receipt["criterion_results"]
    if (not isinstance(criteria, list) or not criteria or
            len(criteria) != len(set(criteria)) or
            not isinstance(results, dict) or set(results) != set(criteria) or
            any(type(results[name]) is not bool for name in criteria)):
        raise BenchmarkError("criterion_results must contain one boolean per declared criterion")
    if receipt["status"] == "succeeded" and (
        not isinstance(receipt["evidence_ref"], str) or not receipt["evidence_ref"].strip()
    ):
        raise BenchmarkError("successful receipts require evidence_ref")
    if not isinstance(receipt["evaluation_date"], str) or not receipt["evaluation_date"].strip():
        raise BenchmarkError("evaluation_date is required")
    duration = _nonnegative_int(receipt.get("duration_ms"), "duration_ms")
    cost = _nonnegative_number(receipt.get("cost_usd"), "cost_usd")
    violations = _nonnegative_int(receipt.get("policy_violations"), "policy_violations")
    retries = _nonnegative_int(receipt.get("retry_count"), "retry_count")
    passed = sum(results.values())
    quality = passed / len(criteria)
    success = receipt["status"] == "succeeded" and passed == len(criteria) and violations == 0
    return {
        "run_id": receipt["run_id"], "case_id": benchmark_case["case_id"],
        "case_version": benchmark_case["version"], "dataset_id": benchmark_case["dataset_id"],
        "criteria_version": benchmark_case["criteria_version"], "minimum_sample_size": _nonnegative_int(benchmark_case["minimum_sample_size"], "minimum_sample_size"), "provider": receipt["provider"],
        "status": receipt["status"], "criteria_passed": passed,
        "criteria_total": len(criteria), "quality_score": quality, "passed": success,
        "duration_ms": duration, "cost_usd": cost, "policy_violations": violations,
        "retry_count": retries, "evidence_ref": receipt["evidence_ref"],
        "evaluation_date": receipt["evaluation_date"],
    }


class BenchmarkEvaluator:
    def __init__(self, cases):
        self.cases = {(item["case_id"], item["version"]): item for item in cases}
        if not self.cases:
            raise BenchmarkError("at least one benchmark case is required")
        self.rows = []
        self.run_ids = set()

    def ingest(self, receipt):
        key = (receipt.get("case_id"), receipt.get("case_version"))
        benchmark_case = self.cases.get(key)
        if benchmark_case is None:
            raise BenchmarkError("unknown benchmark case/version")
        row = score_receipt(benchmark_case, receipt)
        if row["run_id"] in self.run_ids:
            raise BenchmarkError("duplicate run_id")
        self.run_ids.add(row["run_id"])
        self.rows.append(row)
        return row

    def report(self):
        comparison = compare_providers(self.rows)
        dates = sorted({row["evaluation_date"] for row in self.rows})
        return {
            "benchmark": "CODEN Agent Benchmark & Provider Evaluation",
            "version": "1.0.0", "status": comparison["status"],
            "sample_size": len(self.rows), "evaluation_dates": dates,
            "comparison": comparison,
            "limitations": [
                "Only submitted receipts are measured; providers are not executed by this evaluator.",
                "Results are comparable only for identical case, version, dataset and criteria.",
                "Small samples are descriptive and do not justify provider rankings.",
                "Evidence references are recorded, not independently authenticated.",
            ],
        }


def compare_providers(rows):
    if not rows:
        return {"status": "insufficient_data", "ranking": None, "providers": []}
    identity = {(r["case_id"], r["case_version"], r["dataset_id"], r["criteria_version"])
                for r in rows}
    if len(identity) != 1:
        raise BenchmarkError("provider comparison requires identical case, version, dataset and criteria")
    grouped = {}
    for row in rows:
        grouped.setdefault(row["provider"], []).append(row)
    minimum = max(_nonnegative_int(r.get("minimum_sample_size", 1), "minimum_sample_size") for r in rows)
    providers = []
    for provider, samples in sorted(grouped.items()):
        n = len(samples)
        providers.append({
            "provider": provider, "sample_size": n,
            "pass_rate": sum(r["passed"] for r in samples) / n,
            "average_quality": sum(r["quality_score"] for r in samples) / n,
            "average_duration_ms": sum(r["duration_ms"] for r in samples) / n,
            "average_cost_usd": sum(r["cost_usd"] for r in samples) / n,
            "policy_violations": sum(r["policy_violations"] for r in samples),
            "retry_count": sum(r["retry_count"] for r in samples),
        })
    sufficient = all(item["sample_size"] >= minimum for item in providers)
    ranking = sorted(providers, key=lambda p: (
        -p["average_quality"], -p["pass_rate"], p["policy_violations"],
        p["average_cost_usd"], p["average_duration_ms"], p["provider"]
    )) if sufficient else None
    return {"status": "comparable" if sufficient else "insufficient_data",
            "ranking": ranking, "providers": providers}
