# CODEN AI Factory v1.0 — operator-controlled SQLite cancellation (Draft PR #171)

**Founder Plan v1.0** sections 19, 51, 66 and 72. **DRAFT; not production approved.** Based on the actual SQLite operator Worker PR #140 and read-only monitoring PR #170. **No effect on `main`.**

## Cancellation has two fundamentally different meanings

1. **Not yet started:** Operator explicitly requests cancel on a `queued` task. The SQLite transaction atomically changes the task to `cancelled`, clears any runnable path by removing it from the queue's `claim` predicate, leaves `attempts=0`, and records `next_action=cancelled_before_execution`. This transition is terminal. A duplicate request reads the same state without performing another write.
2. **Potentially running:** Operator requests cancel on a `leased` task. The atomic transition is only to `cancel_requested`, with `next_action=operator_stop_and_reconcile`. The original lease token and deadline remain in the database **until reconciliation/expiry**. This DOES NOT stop a process; the operator must terminate or verify the process stopped before declaring cancellation complete. The task cannot be newly claimed, heartbeated or marked finished. The existing worker's failure to finish a cancel-requested lease is an expected `needs_review` situation, not proof it was safely killed.
3. **Expired requested cancellation:** `recover_expired()` (a separate, explicit operator action) moves `cancel_requested` to `needs_review` and clears its expired lease, **never back to `queued`**. It does **not** certify process termination, and cannot auto-retry. This preserves uncertainty after crash/network failure.
4. **Already finished, blocked or under independent review:** cancellation is rejected, not used as a backdoor to rewrite historical outcomes. Unknown task IDs or invalid timestamps fail closed.

## Real implementation and safety scope

- **Source of truth:** `ai_factory/durable_queue.py`, existing SQLite. Uses `BEGIN IMMEDIATE` to serialize competing `claim` vs `request_cancel` commands, parameterized SQL, no extra services or dependencies.
- **Operator CLI:** `python -m ai_factory.offline_worker --queue-db /absolute/trusted/queue.sqlite3 --journal /absolute/trusted/journal --task-dir /absolute/trusted/tasks request-cancel TASK_ID`. This is a **local operator-owned administrative command**, NOT a customer/API endpoint. It uses existing OS file permissions and trusted operator context; it does not provide separate authentication, authorization delegation or public network access. **Never expose this command to untrusted agents.**
- **Read-only status report:** `python -m ai_factory.factory_worker_recovery_status --db /absolute/trusted/queue.sqlite3 --json`. It now reports `cancelled_before_start`, `cancel_requested_active`, `cancel_requested_expired`, and `manual_attention_total` including pending requests. `cancellation_support=REQUEST_ONLY_NO_PROCESS_TERMINATION` and `cancellation_process_termination_verified=false`. The report never returns task IDs, worker IDs or lease tokens.
- **Not implemented by this PR:** signal propagation to the real worker's process group, authenticated remote cancellation, Supabase RLS, atomic worker checkpoint cancellation, automatic compensation/replay, and live OpenHands SDK sessions. The operator must use the separate bounded supervisor and review journal/queue consistency before making any human decision.
- **Independent actual model evidence:** genuine Qwen CPU task #169 counted 80 synthetic lease/cancel flags but its candidate remains **quarantined**; this new state-machine implementation is independently written and tested against the real SQLite queue, **not code silently promoted from a model**.

## Fail-closed evidence

`tests/test_factory_operator_cancellation.py` uses a genuine local SQLite database and includes:

- Queued task cancellation remains terminal, idempotent, non-executable.
- Leased task cancellation only raises a review request; cannot be heartbeated, finished, re-claimed, treated as stopped or auto-retried.
- Expired cancel request goes to human quarantine (never auto re-enqueue).
- Rejected cancellation of missing/finished/blocked tasks; invalid timestamps and corrupt states.
- Atomic racing claims vs cancellations cannot permit a later double-claim or unsafe retry.
- Operator CLI emits only trusted metadata and does not invoke the Worker or AI model.
- Read-only monitoring returns aggregate counts and hides task IDs, hashes and lease credentials.
- The observer rejects malformed `cancel_requested` rows that have no valid lease data.

**CI:** uses all repository prototype tests plus a dedicated job with a real SQLite cancellation race and negative checks. It does not run a live OpenHands model or production worker.

**Mandatory remaining human actions:** approve/review PR stacks #140→#170→#171, prove real supervisor termination mechanics and idempotent process reconciliation, review plan #168 status, close source/SDK isolation blocker #162, and separately review Supabase #150 permissions before any multi-agent pilot.
