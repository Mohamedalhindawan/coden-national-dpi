# Enterprise dependency register contract

## Purpose
A dependency record expresses a directed relationship between two CODEN enterprise work entities (for example, initiatives or work items). The identifiers are intentionally generic; the authoritative registry must establish each endpoint's entity type and tenant/project scope.

## Relationship semantics
- `blocks`: the source cannot proceed until the target is resolved.
- `requires`: the source requires a deliverable or capability from the target.
- `informs`: the target provides context but does not block progress.
- `related_to`: informational association without ordering semantics.

Statuses: proposed, active, satisfied, waived, cancelled. Resolved statuses require `resolved_at`. A waiver is a recorded exception, not proof that an underlying control or obligation is met.

## Validation
- Endpoint IDs must resolve in the trusted application service; the JSON Schema cannot prove their existence.
- A dependency cannot point from an entity to itself.
- Directed cycles should be rejected for ordering relationships (normally `blocks` and `requires`). Informational edges may legitimately form cycles.
- The helper returns a deterministic cycle path. Callers must filter edges by relationship semantics before cycle analysis.

## Governance and limits
This is a contract and pure in-memory validation helper only. It does not implement persistence, tenant isolation, authorization, change history, notifications, scheduling, dependency impact propagation, or a live graph service. Endpoint existence supplied by a caller is not authenticated by this module. Use synthetic identifiers only; do not put secrets or personal data in rationale fields.
