# Stage 86 — FinOps Governance API & Operator Dashboard
Status: PROPOSED / NOT DEPLOYED
Owner: CODEN engineering (proposal)
Scope: synthetic-only prototype. No real payments, beneficiaries, credentials, or financial approvals.

## Objective
Expose reconciliation requests to authorized operators with enforced separation of duties, immutable audit evidence and transparent KPIs. Do not infer that stage 85 is merged into main without verifying its code and CI evidence.

## Proposed API (versioned /api/v1/finops)
- POST /reconciliations — create a request; required: idempotency key, synthetic reference, amount/currency, justification. Respond 201 or same existing resource for replay.
- GET /reconciliations — cursor pagination and filters (status, owner, created range); enforce tenant and role scope server-side.
- GET /reconciliations/{id} — authorized detail and audit history.
- POST /reconciliations/{id}/decisions — approve/reject with mandatory rationale, expected version and distinct reviewer identity.
- GET /finops/metrics — aggregate synthetic counts and durations, no personally identifying data.
- GET /reconciliations/{id}/audit — append-only events with actor, action, UTC time, request ID, previous/new state, reason and correlation ID.

## State machine
PENDING_REVIEW -> APPROVED or REJECTED. Final states cannot be changed; corrections require a new linked request. Creator must never approve their own request. Only FINOPS_REVIEWER may decide; ADMIN does not bypass separation of duties. Duplicate decisions must not create duplicate audit events. Concurrent decisions must use optimistic locking.

## UI screens
1. Overview: pending/approved/rejected, aging, processing time; label all data synthetic.
2. Requests: search, filters, pagination, status and assigned reviewer.
3. Request detail: evidence, decision form, reason, and read-only event history.
4. Audit explorer: filter by actor/action/date; export synthetic CSV with access checks.
5. Access denied and empty/error/loading states; Arabic RTL and English, keyboard navigation.

## Security and governance
- Backend authentication and authorization required; deny by default.
- Never trust client-side roles or status transitions.
- Validate amounts, currency, input size and idempotency keys.
- Use transactional state transition + audit append; prohibit update/delete of audit events at the application layer and enforce database permissions.
- Rate limits, request tracing, structured logs without secrets/PII.
- No deployment until threat modeling, integration tests, review and explicit approval.

## Acceptance tests (write failing tests before implementation)
- Creator cannot approve own request (403).
- Unauthenticated request (401); unauthorized tenant access (404/403 without leakage).
- Distinct reviewer approves once, creating exactly one event.
- Replayed idempotency key does not create a second request.
- Concurrent reviewers cannot both finalize a pending request.
- Approved/rejected requests cannot transition again.
- Metrics reflect only authorized, synthetic data.
- Audit events cannot be edited/deleted through API.
- UI renders Arabic RTL, accessible labels, loading/empty/error states.
- OpenAPI and implementation agree; all repository tests and CI pass.

## Dependencies / next steps
1. Locate and verify stage 85 implementation/commit and tests (not confirmed on main).
2. Add failing backend unit tests for the state machine.
3. Implement in-memory synthetic service and tests, then persistence with migrations.
4. Publish OpenAPI contract and accessible dashboard.
5. Security review, CI evidence and human approval before merge.
