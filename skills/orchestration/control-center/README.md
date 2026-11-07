# CODEN AI Observability & Control Center 2.0

**Status:** Local read-only aggregation service. Not deployed and not yet exposed through the operator API or dashboard.

## Purpose

Combine the existing append-only agent metrics store and SQLite FinOps ledger into one scoped snapshot for operational review. The control center is a reporting layer; it does not schedule, pause, dispatch, execute, or terminate agents.

## Snapshot contents

- Run totals and counts by succeeded, failed, blocked, and cancelled status.
- Success rate, observed cost, input/output/total token counts, average quality and duration.
- Policy violation and retry totals.
- Per-agent rollups and per-provider rollups.
- Project and team budget snapshots for a caller-specified daily or monthly period.
- Project and team threshold alerts from the FinOps ledger.

## Data boundaries

The service reads the existing local metrics and budget stores. It does not collect prompts, payloads, credentials, or raw task content. Agent/provider metrics are aggregated across every run currently in the observability store; the current metrics schema does not include project/team/period attribution, so these run totals must not be interpreted as project-filtered results. Budget data is scoped by project/team and period key.

## Accuracy limitations

- Cost and token values are recorded metric values, not live provider telemetry unless an upstream trusted collector supplies them.
- Budget reservations and reconciled amounts come from the local FinOps ledger.
- No historical time-series query, retention, alert delivery, dashboard endpoint, authentication, multi-tenant isolation, or deployment is provided by this module.
- The service is read-only and does not enforce budget gates itself.

## Tests

```bash
python -m unittest skills.tests.test_control_center -v
python -m unittest discover -s skills/tests -v
```

## Next integration steps

Add project/team/period attribution to metric records; expose this snapshot through an authenticated read-only API; add dashboard panels and time-series views; then verify browser rendering and access controls before any deployment.
