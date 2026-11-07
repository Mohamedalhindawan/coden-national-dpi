# CODEN AI FinOps & Budget Control 1.0

**Status:** Experimental local accounting ledger. It does not connect to billing systems or provider usage APIs.

## Scope

The FinOps layer provides a persistent SQLite ledger for project/team budgets, pre-execution cost reservations, post-execution spend reconciliation, utilization snapshots, and threshold alerts.

## Current behavior

- Daily and monthly budget limits can be configured independently for project and team scope IDs.
- A reservation is checked atomically against configured project and team daily/monthly limits using SQLite `BEGIN IMMEDIATE`.
- A request ID is idempotent when all reservation dimensions match; reuse with changed details is rejected.
- Reconciliation replaces the outstanding reservation with actual spend and releases unused reserved capacity.
- Reconciliation above the reserved amount is rejected; the caller must request an explicit additional reservation rather than silently exceed the cap.
- Snapshots report reserved, actual, consumed, remaining, and utilization.
- Alerts are emitted at configurable percentage thresholds (default 80%, 90%, and 100%).

## Integration boundary

The ledger is not yet wired into ModelGateway or ProviderCatalog. A future orchestration integration must reserve estimated cost before dispatch and reconcile verified provider usage afterward. No model or provider is invoked by this module.

## Accounting assumptions and limitations

- Amounts are USD estimates supplied by the caller; no exchange-rate conversion is performed.
- Model price metadata and token estimates are not independently verified.
- No actual provider token usage is ingested.
- Budgets are local SQLite records; no multi-tenant authorization, distributed transaction, or multi-host concurrency service is provided.
- No scheduled notifications or automatic external kill switch exists. The ledger rejects new reservations, but cannot stop an already-running external provider request.
- Reservations are not automatically expired or released; reconciliation is required.
- Database administrators can alter local SQLite files; append-only tamper-evident audit is not implemented.

## Tests

```bash
python -m unittest skills.tests.test_finops -v
python -m unittest discover -s skills/tests -v
```

## Production requirements

Before production use, add authenticated budget administration, tenant/project RBAC, tamper-evident audit, backup/restore, reservation expiry/recovery, provider usage reconciliation, currency and tax policy, budget rollover, scheduled alerts, cost attribution, organization-wide caps, and integration tests proving the reservation gate executes before any live provider call.
