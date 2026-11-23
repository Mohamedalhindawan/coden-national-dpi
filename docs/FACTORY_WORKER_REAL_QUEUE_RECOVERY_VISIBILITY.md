# CODEN AI Factory — real offline Worker queue recovery visibility

**Stage:** DRAFT / operator-only / no data from production. **PR #170** stacked on existing Worker PR #140, not merged into `main`.

**Founder-approved v1.0 references:** sections **19** Task Management Engine, **51** Worker/cancellation/recovery, **66** safe control batch, **72** self-development acceptance. This is implementation evidence **towards** those sections, not proof that the whole section or factory is complete.

## Why this matters

The earlier genuine Qwen CPU pilot (Draft PR #169) generated a function that counted exact `lease_expired` and `cancel_requested` labels on **80 synthetic string flags**. It proved model-generated code could pass visible/hidden tests under bubblewrap; it **did not** connect to a Worker or implement cancellation. This new PR reads the actual SQLite schema supplied by `ai_factory.durable_queue.DurableQueue` to observe genuinely expired leases **without executing or importing that generated model code**.

In the actual queue, an expired leased task is still `status=leased` with `lease_until < now`. It only becomes `status=needs_review` after the distinct, operator-controlled `recover_expired()` operation. The queue has **no `cancel_requested` task status/cancellation API**; the report calls cancellation `NOT_IMPLEMENTED` instead of inventing functionality. Neither state can trigger an automatic retry.

## New checked-in module

`ai_factory/factory_worker_recovery_status.py` is a bounded read-only Linux SQLite inspector. It:

- Reads a **pre-existing, local, operator-owned** database using `O_RDONLY|O_NOFOLLOW`, an already-open `/proc/self/fd` descriptor and SQLite `mode=ro` / `query_only`.
- Checks known `tasks` schema, known queue statuses, lease tokens and finite deadlines; fails closed on unknown/corrupt state.
- Caps input database size at 64 MiB and row count at 10,000 for this pilot; refuses oversized inputs rather than reporting a misleading partial count.
- Counts `queued`, `leased_active`, `leased_expired_pending_review`, `needs_review_quarantined`, `blocked`, `failed` and `awaiting_human_review`. The human recovery backlog is **expired leases + previously quarantined tasks**.
- Returns only aggregate counts, **not task identifiers, lease tokens, branches, commit hashes, payloads or user data**.
- Never imports model-generated source, calls an LLM, installs dependencies, creates a Worker process, changes queue state, calls `recover_expired()` or grants approval.

`tests/test_factory_worker_recovery_status.py` uses the **real SQLite queue**, not a mock. It verifies expiration at exact time boundaries, actual quarantines, invalid statuses and timestamps, symlink/schema guards, CLI output, no information leaks, and unchanged database bytes/mtime after the inspection.

## Reproduction

Only with an **existing synthetic local queue DB** on Linux:

```bash
python -m unittest discover -s tests -p 'test_factory_worker_recovery_status.py' -v
python -m ai_factory.factory_worker_recovery_status \
  --db /absolute/path/to/operator/queue.sqlite3 --json
```

The CLI does not create an absent database and returns BLOCKED on invalid input. A separate GitHub Actions job builds a **new temporary synthetic real SQLite DB**, uses the actual DurableQueue lease/recovery methods, checks the read-only receipt against independently expected counters and exports a sanitized JSON artifact.

## Remaining gates

- **OpenHands issue #162: BLOCKED.** Upstream pinned DockerWorkspace lacks independently proven hard CPU/RAM/PIDs, capability-drop and read-only-root limits. This PR does not start an OpenHands container.
- **Worker Draft #140:** still requires full operator review before merge. This PR is stacked on it and is not automatically in `main`.
- **Cancellation:** NOT_IMPLEMENTED in current DurableQueue; an explicit cancellable state machine, API, authorization and real idempotency tests are still required. This report must never claim it can cancel tasks.
- **Qwen Draft #169:** real model-generated candidate remains quarantined; the read-only operator telemetry implementation is independently reviewed code, not generated code promoted automatically.
- **Supabase Draft #150:** remote worker auth/RLS/control plane is not wired by this PR.
- All tests and evidence are synthetic in content, all provider/API spend is zero, no private records or production access, no automatic merging or release; **human review required**.
