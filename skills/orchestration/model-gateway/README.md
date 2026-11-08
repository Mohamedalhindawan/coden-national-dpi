# CODEN AI Model Gateway & Intelligent Routing 1.0

**Status:** Experimental, simulated-only model selection. No model provider is invoked.

## Responsibility boundary

- Provider integration describes vendor/provider adapters and their security contracts.
- Model profiles describe individual model capabilities, context limits, and declared token prices.
- The model gateway selects an eligible model for a task request based on capability, context window, estimated request cost, and a caller-supplied budget ceiling.
- Existing task routing continues to recommend the agent role and capability. This gateway does not replace task routing or execute the task.

## Current behavior

`ModelGateway` accepts registered `ModelProfile` records and a `ModelRequest`. It filters disabled models, unsupported capabilities, insufficient context windows, and models whose estimated input/output cost exceeds the request's budget. It then chooses the lowest estimated-cost eligible model, with a deterministic model ID tie-breaker.

The receipt identifies the selected provider/model, selection basis, estimated cost, token estimates, and mandatory approval. It explicitly reports `mode=simulated`, `provider_invoked=false`, and `network_used=false`.

## Safety and cost limitations

- Only `synthetic` and `public` classifications are accepted.
- Live mode and network access are rejected.
- Human approval is mandatory.
- Token counts and prices are caller-supplied estimates/model metadata, not measured provider usage.
- The request budget is a per-request ceiling, not a monthly or organization-wide spend limit.
- No provider credentials are read and no provider SDK is imported.
- No fallback call is made; a routing failure returns an error.
- This is not a quality benchmark and does not claim that the lowest-cost model is the most capable or best-performing.

## Tests

```bash
python -m unittest skills.tests.test_model_gateway -v
python -m unittest discover -s skills/tests -v
```

## Production gaps

Before live use, add independently verified provider price catalogs, tokenizer-aware estimates, organization/project budgets, atomic spend reservations, actual usage reconciliation, quotas, rate limits, provider health and circuit breakers, policy-aware fallback, tenant isolation, secret-manager integration, signed audit records, and vendor data-processing/security reviews. Live provider execution requires a separate explicit approval and security review.
