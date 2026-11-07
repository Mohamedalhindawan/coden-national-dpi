# CODEN Agent Benchmark & Provider Evaluation 1.0

**Status:** Experimental / Draft. No provider has been evaluated by this repository yet.

## Purpose

A deterministic scoring and reporting layer for comparing agent receipts on the same versioned synthetic benchmark. It does not call, launch, or orchestrate Factory AI, Manus, Codex, OpenHands, or any external provider.

## Components

- `schemas/benchmark-case.schema.json`: benchmark case contract.
- `benchmark_manifest.json`: four synthetic case definitions across engineering, DPI, DevSecOps, and QA.
- `benchmark.py`: receipt validation, deterministic scoring, duplicate-run protection, fair comparison, and report metadata.
- `../../tests/test_benchmark.py`: unit tests for evidence, versions, metric ranges, duplicate IDs, fair comparison, and minimum samples.

## Safe workflow

1. Select a case ID and immutable case version.
2. Give the same synthetic dataset, prompt/task specification, tools policy, and criteria version to each provider in a separately controlled evaluation.
3. Have an authorized evaluator submit a receipt with criterion booleans, status, evidence reference, duration, cost, policy violations, retries, and evaluation date.
4. Ingest receipts using `BenchmarkEvaluator`.
5. Review the generated report and evidence independently before drawing conclusions.

Raw prompts, credentials, citizen data, and unrestricted provider output must not be placed in benchmark receipts. Evidence references are pointers only; this prototype does not authenticate or fetch them.

## Scoring

- Quality = passed declared criteria / total declared criteria.
- A run passes only when status is `succeeded`, every criterion passes, and policy violations equal zero.
- Latency and cost are reported as averages; retries and policy violations are totals.
- Provider comparisons require identical case ID, case version, dataset ID, and criteria version.
- Rankings are withheld until every provider meets the case's minimum sample size (3 by default). Below that threshold the report says `insufficient_data`.

This is a transparent deterministic scorecard, not a universal provider-quality score. Criteria design and evidence review remain human responsibilities. The prototype does not calculate confidence intervals, significance tests, or adjust for hardware, model version, context window, tool access, prompt variance, or evaluator bias.

## Run tests

From repository root:

```bash
python -m unittest discover -s skills/tests -v
```

The GitHub Actions workflow already runs the skills test directory. Check the PR's actual Actions run before treating tests as passed.

## Non-goals and restrictions

- No live provider calls, subprocess execution, network access, or automatic agent selection.
- No fabricated sample results or provider leaderboard.
- No production, government, or real-citizen data.
- No automatic merge or deployment.
- This is a local evaluation prototype, not a certified benchmark or procurement decision tool.
