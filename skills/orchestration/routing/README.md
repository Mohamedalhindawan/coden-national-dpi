# CODEN Agent Routing & Model Selection 1.0

**Status:** Experimental / Draft. Recommendation-only; no provider integrations.

## Purpose

Map a task profile to a logical CODEN agent role, capability, and a suggested tool boundary. The router is policy-first and deterministic. It does not call a model, execute a tool, dispatch a task, or select a provider based on unverified claims.

## Supported task families

| Task type | Logical role | Capability |
|---|---|---|
| planning | PLN-01 | reasoning |
| architecture | ARC-01 | architecture |
| dpi_design | DPI-01 | dpi_architecture |
| software_implementation | DEV-01 | coding |
| data_engineering | DATA-01 | data_engineering |
| security_review | SEC-01 | security |
| quality_assurance | QA-01 | testing |
| documentation | DOC-01 | technical_writing |
| cost_analysis | FIN-01 | finops |
| release_review | REL-01 | release |
| benefits / health / identity / financial decisions | DPI-01 / SEC-01 / FIN-01 | policy_analysis / security / finops |

## Safety policy

- Network-enabled routes are rejected.
- Only synthetic, public, or explicitly reviewed sensitive metadata classifications are accepted; personal and citizen records are rejected.
- High/critical risk, sensitive data, and high-impact decision tasks are recommendation-only.
- Human approval is mandatory for every route.
- Provider names are accepted only as user-supplied metadata. They are not endorsed, evaluated, or ranked.
- Provider invocation is always false and execution mode is limited to dry-run or recommendation-only.

## Components and tests

- `routing.py`: deterministic recommendation and policy validation.
- `schemas/routing-profile.schema.json`: input profile contract.
- `../../tests/test_routing.py`: policy, safety, and deterministic routing tests.

Run from repository root:

```bash
python -m unittest discover -s skills/tests -v
```

## Limits

This is not a model router, provider gateway, load balancer, or agent runtime integration. It does not inspect live provider availability, prices, model versions, latency, or benchmark scores. The benchmark suite must first collect comparable, independently reviewed evidence before provider-specific selection criteria can be considered.
