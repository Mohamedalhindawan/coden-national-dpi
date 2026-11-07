# WorkItem lifecycle transition policy

The policy primitive in `coden_enterprise.workflow` validates a single requested state change against an explicit allow-list. It is deterministic and has no I/O or side effects.

## Allowed transitions

| Current state | Allowed next states |
|---|---|
| draft | submitted, cancelled |
| submitted | approved, rejected, blocked, cancelled |
| approved | ready, blocked, cancelled |
| ready | in_progress, blocked, cancelled |
| in_progress | validating, blocked, failed, cancelled |
| validating | human_review, blocked, failed |
| human_review | accepted, rejected, blocked |
| blocked | ready, cancelled |
| accepted, rejected, cancelled, failed | none (terminal) |

The transitions submitted → approved and human_review → accepted require an approval status of `approved`.

## Security boundary

This is a policy check, not an authorization system. It does not establish who supplied the approval status, authenticate an approver, enforce separation of duties, prevent replay, persist a transition, or provide concurrency/idempotency guarantees. A future service must perform those checks using trusted identity and approval records before calling this policy, then persist state and audit evidence atomically.

## Validation

Unit tests cover allowed transitions, skipped review, missing/rejected/pending approval, terminal-state reopening, unknown states, and self-transitions. CI executes the suite through unittest discovery.
