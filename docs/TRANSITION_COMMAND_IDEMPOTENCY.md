# Transition command envelope and idempotency

A transition request must carry three fields before a future service considers changing a WorkItem:

- `idempotency_key`: caller-generated request key, 16–128 characters.
- `expected_version`: positive integer version observed by the caller.
- `requested_by`: non-empty principal identifier supplied by the trusted application layer.

The pure validator rejects missing/malformed fields and booleans masquerading as integer versions. It does not authenticate the principal or make a request idempotent by itself.

## Required future persistence semantics

A production service must execute the following atomically:

1. Authenticate the caller and derive the principal from a verified identity context (never trust a body-supplied identity alone).
2. Look up the idempotency key within a defined tenant/project/principal scope.
3. If the key already exists, return the original recorded result and do not repeat the transition.
4. Compare the persisted WorkItem version with `expected_version`; reject stale writes with a conflict response.
5. Validate the lifecycle transition and any required approval using trusted records.
6. Persist the new state, incremented version, idempotency result, and append-only audit event in one transaction.
7. Enforce key-retention and collision policy, and never allow the same key to authorize a different payload.

No persistence, transaction, locking, authentication, or replay store is implemented in this contract PR.