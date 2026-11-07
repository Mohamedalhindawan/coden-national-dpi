# Approval decision and separation of duties

The local policy validator enforces structural decision invariants:

- A pending approval has no `approver_id` and no `decided_at`.
- A final decision (`approved`, `rejected`, `expired`, or `revoked`) has both fields.
- The requester and approver identifiers must differ.

## What this does not prove

The validator does not authenticate either identity, determine whether the approver has the required role or authority, verify signatures, parse/validate timestamps, check expiry against a trusted clock, or persist an immutable decision. A trusted service must derive identities from verified authentication, apply role and scope policy, enforce any quorum/dual-control rule, validate time and expiry, and atomically append the decision and audit event.

This is a pure local policy primitive; it does not enable or execute approvals in a production environment.
