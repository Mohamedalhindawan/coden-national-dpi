# CODEN Orchestration State Machine 1.0

## Allowed transitions
| Current state | Event | Next state | Guard |
|---|---|---|---|
| INTAKE | Submit | POLICY_CHECK | Owner and objective present |
| POLICY_CHECK | Allow | PLANNING | Risk/data/tool policy passes |
| POLICY_CHECK | Deny | BLOCKED | Reason recorded |
| PLANNING | Plan accepted | READY | Required approvals exist |
| READY | Start | EXECUTING | Workspace and run envelope pinned |
| EXECUTING | Tasks done | VALIDATING | No dependency missing |
| EXECUTING | Retryable error | EXECUTING | Idempotent and retry budget remains |
| EXECUTING | Fatal/policy error | FAILED or BLOCKED | Stop and preserve evidence |
| VALIDATING | Mandatory checks pass | REVIEW_REQUIRED | Evidence complete |
| VALIDATING | Checks fail | PLANNING | Remediation task created |
| REVIEW_REQUIRED | Human approves | COMPLETED | Approval bound to exact artifact/action |
| REVIEW_REQUIRED | Human requests changes | PLANNING | Feedback recorded |
| REVIEW_REQUIRED | Human rejects | CANCELLED | Decision recorded |
| Any non-terminal | Cancel | CANCELLED | Cancellation recorded |

Terminal states: COMPLETED, FAILED, BLOCKED, CANCELLED. No agent may transition directly from REVIEW_REQUIRED to COMPLETED.

## Retry policy
- Retry only transient failures such as rate limits or temporary service unavailability.
- Default maximum: one retry per task; configure explicitly.
- Never retry validation failures, policy denials, permission errors, schema violations, or non-idempotent writes.
- Backoff must be bounded and jittered by the runtime.
- Exhausted retries produce FAILED or BLOCKED with evidence.

## Circuit breakers and bulkheads
Isolate provider adapters, tool adapters, and task workspaces. Limit concurrency per provider and workflow. Provider outages must not corrupt state or trigger unbounded fallback spending. Provider fallback requires an explicit allowlist and records model/version changes. Stop when budget, latency, or error thresholds are exceeded.

## Cancellation and compensation
Cancellation prevents new scheduling and signals active tasks to stop. Only explicitly defined reversible operations may have compensation actions. External writes are never automatically compensated unless an approved reversal procedure exists.

## Required invariants
1. A terminal run cannot accept child tasks.
2. A child cannot access undeclared artifacts or tools.
3. A failed mandatory safety gate cannot be overridden by a numeric score.
4. A retry cannot duplicate a non-idempotent side effect.
5. Approval is tied to immutable artifact hashes and exact action scope.
6. State changes and policy decisions are append-only in the audit record.
