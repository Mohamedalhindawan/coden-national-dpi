# CODEN Persistent Execution Queue 1.0

**Status:** Experimental / Draft. Single-host SQLite queue primitive.

## Capabilities

- Durable task envelopes and status across process restarts.
- Idempotent enqueue keyed by `task_id`; reuse with different payload or policy is rejected.
- Priority-based claiming with deterministic FIFO/task-ID tie breaks.
- Worker leases with opaque fencing tokens; heartbeat, completion, and failure require the current worker and token.
- Expired leases are recovered on the next claim; attempts are bounded by `max_attempts` (1–4).
- Cancellation invalidates the active lease so a late worker cannot commit a result.
- Append-only event log for enqueue, claim, heartbeat, lease expiry, failure, completion, and cancellation.

## Minimal API

```python
queue.enqueue("task-001", {"kind": "synthetic"}, max_attempts=2, priority=10)
claim = queue.claim("worker-01", lease_seconds=60)
queue.heartbeat("task-001", "worker-01", claim["lease_token"])
queue.complete("task-001", "worker-01", {"status": "simulated"},
               lease_token=claim["lease_token"])
```

A worker must keep its lease token private and supply it for every state-changing action. A reclaimed task receives a new token, fencing the previous worker.

## Tests

```bash
python -m unittest skills.tests.test_persistent_queue -v
python -m unittest discover -s skills/tests -v
```

## Operational and security boundaries

- SQLite is suitable here as a local prototype, not a distributed multi-host queue.
- No worker process, scheduler daemon, DAG dependency gate, execution sandbox, provider adapter, or network dispatch is started by this module.
- Lease recovery is lazy: expired leases are reconciled when a worker calls `claim`.
- A worker can still perform an external side effect before losing its lease. Fencing prevents stale queue commits, not duplicate external side effects; downstream systems need idempotency keys.
- Queue payloads/results are JSON objects. Do not put prompts, credentials, personal data, health records, identity data, financial data, or secrets in them.
- Audit triggers protect against ordinary SQL updates/deletes, not privileged database/file tampering.
- Production use requires a reviewed distributed queue, authenticated worker identity, authorization, encryption, retention, monitoring, backup/recovery, and tested disaster procedures.

This is queue state management only, not production execution infrastructure.
