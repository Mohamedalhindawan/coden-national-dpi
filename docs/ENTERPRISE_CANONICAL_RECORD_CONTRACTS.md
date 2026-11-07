# Stage 3A — Canonical Enterprise Record Contracts

**Status:** Draft implementation; synthetic fixtures only.  
**Scope:** Data contracts, not a deployed management service.

## Canonical records

| Record | Purpose | Important controls |
|---|---|---|
| Project | Groups work under an accountable owner | Status, risk tier, data classification, timestamps |
| AgentProfile | Describes a potential human- or AI-operated worker | Type, provider/model reference, version, lifecycle status, risk tier, human owner |
| WorkItem | Defines a bounded unit of work | Owner, optional agent assignment, priority, lifecycle, acceptance criteria, data class, explicit allowed tools |
| Approval | Records a decision about a specific artifact/action | Immutable artifact digest, environment, requester, decision, optional approver and timestamps |
| AuditEvent | Records an attributable action and outcome | Actor, subject, timestamp, correlation ID, outcome, optional evidence and redacted metadata |

## Contract conventions

- JSON Schema Draft 2020-12 is the contract dialect.
- Unknown top-level properties are rejected (additionalProperties: false).
- Identifiers use a restricted ASCII token syntax; they are not credentials.
- Date/time fields use JSON Schema date/time formats and are checked with a format checker in tests.
- Enumerations are intentionally narrow. Adding a lifecycle state requires a reviewed schema change and fixture/test update.
- Fixtures contain synthetic identifiers and no personal or beneficiary data.
- Audit metadata is limited to scalar values and is explicitly named metadata_redacted; this does not make sensitive-data ingestion safe.
- allowed_tools is declarative metadata only. It does not grant or enforce runtime permissions.
- An Approval record is evidence of a decision request/outcome, not an authorization engine. Runtime must independently authenticate the approver, enforce separation of duties, validate the digest against the exact artifact, and reject stale/replayed approvals.

## Lifecycle and human control

A WorkItem may move through draft, submitted, approved, ready, in-progress, validating, human-review, accepted, blocked, rejected, cancelled, or failed. These schemas validate individual values; they do not enforce legal state transitions. A future service must implement a transition table, concurrency control, idempotency, and append-only audit recording.

High-impact actions (production deployment, financial decisions, identity changes, policy changes, or use of real beneficiary data) must remain behind explicit human approval and independently enforced authorization. No such action is implemented by this PR.

## Validation

CI installs the pinned jsonschema validator and runs schema meta-validation, fixture validation with format checking, negative tests for unknown properties/missing artifact digest/secret-field insertion, existing TAMAM prototype tests, and OpenAPI validation.

## Non-goals and limitations

This PR does not add a database, API, authentication/authorization provider, agent runtime, workflow scheduler, UI, audit immutability guarantees, cryptographic signing, retention policy, or production deployment. It does not establish that CODEN is approved for national or government use.

## Next Stage 3A increments

1. Add cross-record reference checks (e.g., WorkItem project and AgentProfile references).
2. Define a versioned lifecycle transition contract and idempotency requirements.
3. Add policy decision/approval separation-of-duties tests.
4. Only then consider persistence/API implementation behind a separate reviewed PR.
