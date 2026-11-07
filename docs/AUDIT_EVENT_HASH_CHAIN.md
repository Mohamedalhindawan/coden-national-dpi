# Audit event hash-chain integrity

The local helper in `coden_enterprise.audit` appends canonical-JSON SHA-256 digests to an in-memory event list. Each event contains a 1-based sequence, the previous event digest, and its own digest. Verification checks event order, linkage, unique IDs, and content digests.

## Security properties and limitations

This detects accidental or partial modification, removal, insertion, and reordering when a trusted prior chain head is retained. It does **not** prevent an attacker with write access to the entire chain from rewriting all events and recomputing all hashes. It does not provide a digital signature, external timestamp, WORM storage, access control, durability, replication, or key management.

## Production requirements

A production audit service must persist events append-only, enforce authorization independently, protect checkpoints outside the event store, sign or externally anchor periodic chain heads, use trusted time, restrict and log administrative access, encrypt sensitive data, define retention/legal hold, and test backup/restore and tamper response. Audit payloads must be minimized and redacted; secrets and citizen sensitive data must never be copied into metadata.

The current implementation is an in-memory integrity primitive for synthetic tests only. It is not a production audit service.
