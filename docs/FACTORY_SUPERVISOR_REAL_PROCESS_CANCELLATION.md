# CODEN AI Factory v1.0 — Explicit Worker Child Cancellation and Reconciliation Evidence

**Status:** Draft PR #172 — review only; stacks on #171 → #170 → #140. Frozen founder-approved Plan v1.0 (#168) is unchanged.

## Goal

Extend the already-tested operator-only **cancel request** in #171 into an actual **owned child-process stop attempt** in the existing, bounded `worker_supervisor.py`. Keep every failure reviewable; no automatic task replay, model invocation, remote permissions, privileged worker or production claim.

### Security-critical exact task binding

Prior supervisor supported one-shot FIFO execution but did not know which task its child claimed. It must not try to stop a process based on an unrelated cancellation request. This PR adds **optional explicit `task_id`** to the trusted SQLite `DurableQueue.claim`, the offline worker `--task-id` option and the supervisor `--task-id` option. The old operator-only FIFO path remains intact and unchanged by default.

The supervisor refuses to start a selected task that isn't currently `queued`. The worker's claim selects **only that task** inside SQLite `BEGIN IMMEDIATE`. Cross-task child receipts are rejected, and a child that exits without having claimed its task cannot report a successful worker run.

### Live owned-child monitoring

For **explicit task IDs only**, the supervisor checks the task's real SQLite state while its own fixed `offline_worker` child is alive. If it observes `cancel_requested`, `cancelled` or an externally quarantined `needs_review` state, it sends SIGKILL to **only its own child process group** (`start_new_session=True`) and waits for the process-group leader to exit. The separate supervisor test starts an **actual Linux child with a real sleeping grandchild**; requests cancellation through genuine `DurableQueue.request_cancel`, then checks that the leader exited and the descendant is no longer running.

**What this does NOT prove:** reaping one leader never establishes that all descendants everywhere were terminated. The receipt has `owned_process_leader_reaped=true` and **`process_tree_absence_verified=false`**, even if the dedicated synthetic regression independently checks one grandchild. It does not prove third-party execution, OpenHands, container escape protection or runtime cgroup limits.

On an observed stop, the supervisor attempts a hash-chained journal entry `blocked` with `next_action=inspect_cancel_stop` and fixed idempotency key. It returns `cancel_stop_review_required`, not `cancelled` or `completed`. **The original queue is left `cancel_requested`/quarantined; no automatic retry and no automatic reconciliation.** An operator must inspect the full queue/journal/artifact state and only use the separate explicit `recover_expired` quarantine procedure when applicable.

The existing read-only reconciler now distinguishes `consistent_cancelled_before_start` (queued task cancelled with untouched prepared journal) from `cancel_stop_reconciliation_required` (leased task whose cancellation was requested, regardless of whether its child leader was reaped). The latter remains `needs_attention=true` and `safe_to_auto_retry=false`; a generic `state_mismatch` is no longer the only operational signal.

If the group stop cannot be verified or journal append fails, the supervisor fails closed with no success receipt. This code has **no API endpoint** for untrusted clients, no extra credentials, and never imports the generated Qwen candidate from Draft PR #169.

## How to run the monitored operator-only pilot

For an **existing, operator-owned SQLite queue and synthetic task/checkpoint** on Linux:

```bash
python -m ai_factory.worker_supervisor \
  --queue-db /absolute/operator/queue.sqlite3 \
  --journal /absolute/operator/journal \
  --task-dir /absolute/operator/tasks \
  --output-root /absolute/operator/output \
  --worker-id operator_local_1 \
  --task-id KNOWN_SYNTHETIC_TASK_ID \
  --timeout-seconds 60 \
  --lease-seconds 120 \
  work-once
```

A trusted local operator can request cancellation in another process:

```bash
python -m ai_factory.offline_worker \
  --queue-db /absolute/operator/queue.sqlite3 \
  --journal /absolute/operator/journal \
  --task-dir /absolute/operator/tasks \
  request-cancel KNOWN_SYNTHETIC_TASK_ID
```

The two commands are **not authorized against real customer/citizen/government tasks**. Cancellation changes task state, does not confer model/provider permissions or production privileges.

## Verification and remaining gaps

`tests/test_factory_supervisor_cancel_stop.py` uses real SQLite and real Linux group signals for the stop path. Independent negative checks reject forged task IDs, unclaimed-result claims and unsafe external quarantine. Full `tests/test_worker_supervisor.py`, `tests/test_offline_worker.py`, `tests/test_factory_operator_cancellation.py` and repository CI remain required.

The remaining P0 OpenHands sandbox controls are tracked in issue #162: image/source provenance, cgroup CPU/RAM/PID limits, cap drop, network egress and confidential credential isolation. **This PR doesn't lift them.** Supabase PR #150 trusted-worker authentication/RLS and human-reviewed merge are independent tasks. Process monitoring is operator-invoked and bounded, **not** an always-on worker service.

**Governance:** zero paid model calls, zero production deployment, no automatic GitHub merge or source approval, no modifications to Master Plan v1.0, no automatic process relaunch.
