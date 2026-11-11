# AI Factory offline batch budget preflight

This document covers the **draft-only**, synthetic-data review queue in `ai_factory.review_queue`. It does not run agents, purchase resources, contact model APIs, deploy software, or authorize spending.

```bash
python -m ai_factory.review_queue synthetic-tasks.json --budget-usd 0.30
python -m unittest discover -s tests -v
```

Example `synthetic-tasks.json`:

```json
[
  {"id":"DEMO-1","title":"Offline test","description":"Synthetic data only","data_classification":"synthetic","requested_actions":["run_tests"],"estimated_cost_usd":"0.10"},
  {"id":"DEMO-2","title":"Review code","description":"Synthetic data only","data_classification":"synthetic","requested_actions":["read_repository"],"estimated_cost_usd":"0.20"}
]
```

With `--budget-usd`, every task must supply a nonnegative finite `estimated_cost_usd`; the entire batch is rejected when an estimate is missing, malformed, negative, nonfinite, or the summed estimate exceeds the ceiling. Estimates and limits are parsed with decimal arithmetic. An omitted budget retains the original validation-only behavior for backward compatibility. No budget argument represents an authorization to spend; every valid plan remains `awaiting_human_approval` with `execution_authorized: false`.

The ceiling is **not** a cloud-provider hard spending cap, metering service, or runtime cost enforcement. Real API billing requires separate provider-side limits, credentials isolation, human approval, and monitoring before enabling any executor.
