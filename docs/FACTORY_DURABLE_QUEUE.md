# CODEN Factory — Durable Offline Task Queue (Draft)

**Status:** real SQLite task-tracking and lease primitives, **not** a running worker or an approval gateway. This library does **not** execute model calls, project tasks, GitHub actions, paid operations, or automatically retry unsafe work.

## Purpose

The original factory pilot (#126) has offline, bounded Python project execution but no persistent queue. PR #132 adds a tamper-evident checkpoint *journal* and failure-policy planning. This file documents the additional, separate SQLite queue for atomically assigning **metadata-only** synthetic tasks to local workers when an operator eventually connects a safe execution service.

File: \`ai_factory/durable_queue.py\`, tests \`tests/test_durable_queue.py\`.

## Implemented state machine

\`\`\`text
   enqueue                  claim (atomic)              finish (review gate)
     |                            |                            |
   queued ---------------------> leased ----------------> awaiting_human_review
                                    |         \----------> failed / blocked
                                    |
                     lease expires / worker disappears
                                    |
                                    v
                                needs_review
                           (never auto-requeued)
\`\`\`

Features verified by tests:

- SQLite transaction with \`BEGIN IMMEDIATE\` makes claiming a queued task exclusive across connections.
- Durable local metadata: task ID, Git branch, full commit SHA, task specification SHA-256, current state, attempts and next-action identifier.
- No project prompt, description, identity, raw user data, API token, or source artifact stored in this queue.
- Random lease token for acknowledgements and bounded lease durations.
- Heartbeats only while the lease is valid.
- Expired lease **quarantined for human review**, not silently sent to another worker. This is essential because a crashed worker may have already created files or PRs.
- \`finish()\` accepts only \`awaiting_human_review\`, \`failed\`, or \`blocked\`; never \`approved\` or \`deployed\`.
- Returns \`execution_authorized: false\`; queue availability alone never grants execution rights.
- Tests include 2 competing workers, stale lease, persisted state, duplicate submission, invalid token, and broken symlink rejection.

## Try offline without running any coding task

\`\`\`bash
python - <<'PY'
from ai_factory.durable_queue import DurableQueue
from hashlib import sha256
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as root:
    q = DurableQueue(Path(root) / "operator" / "tasks.sqlite3")
    fingerprint = sha256(b"synthetic-task-v1").hexdigest()
    q.enqueue("demo_job", "feat/synthetic", "a"*40, fingerprint)
    lease = q.claim("demo_worker", now=1000, lease_seconds=15)
    print(q.read("demo_job"))
    # Simulate a worker crash without completing any task.
    q.recover_expired(now=1016)
    print(q.read("demo_job"))  # needs_review, never automatically executed
PY
\`\`\`

\`\`\`bash
python -m unittest discover -s tests -p 'test_durable_queue.py' -v
python -m unittest discover -s tests -v
\`\`\`

## Operational boundaries

- The SQLite DB must live in an operator-owned private directory. The check against symlinked paths is defensive, not a complete protection against hostile filesystem races; do not put the DB in an untrusted agent-writable directory.
- SQLite supports durable local transactions, not distributed high availability, offsite backup or production approval by itself. For many machines, evaluate PostgreSQL/Temporal/Hatchet only after baseline requirements and actual concurrency demand.
- Lease expiry does **not** prove that execution stopped. It only marks the task for inspection. Never use this queue to directly trigger irreversible actions.
- The task SHA-256 is a reference, not a content verification of a task payload (the queue never stores that payload). A future worker must verify the supplied artifact hash, scope, classification and approval **before** sandbox execution.
- Do not persist lease tokens in GitHub issues, CI logs or chat. Leases are for task ownership, not model permissions.
- This module is currently a **building block**. A trusted worker, manual approval source, audit trail, queue/checkpoint reconciliation and backup/recovery tests are not yet implemented.

## Next Codex work

1. Add task lookup from a protected operator-controlled repository or artifact store and verify \`task_sha256\`.
2. Connect lease management to the approved offline synthetic \`checkpoint_project\` runner only, including well-scoped cancellation/heartbeat and independent replay protection.
3. Reconcile queue state with checkpoint journal state; protect against crash windows between code changes, artifact writes and the DB transaction.
4. Add bounded retries **only for idempotent** tools. Never auto-replay PR creation, payment, deployment, credentials or data writes.
5. Integrate an authorized model transport and gateway with typed failures (see \`FACTORY_OFFLINE_RECOVERY_POLICY.md\`).
6. Conduct fault injection on a real worker with a sandbox, then report explicit results before production claims.
