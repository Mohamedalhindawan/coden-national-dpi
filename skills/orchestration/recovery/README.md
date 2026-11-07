# CODEN Durable Workflow Recovery 1.0

**Status:** Experimental / Draft.

The persistent SQLite queue is the durable source of task execution state. Recreating a scheduler with the same queue database and declared task graph reconstructs successful dependencies, running leases, and terminal queue states. On the next claim, the queue lazily expires leases whose deadline has passed, fences the old token, and makes the task pending again when attempts remain.

The scheduler recalculates blocked descendants from persisted failed/cancelled states using `refresh_blocked()`. The blocked overlay is reconstructed in memory from the durable queue and DAG on every process start; it is not a separate persisted state.

## Recovery sequence

1. Reopen the same SQLite queue database.
2. Recreate worker admission and the worker–queue integration.
3. Recreate `DAGAwareScheduler` with the same task graph.
4. Call `refresh_blocked()` to rebuild blocked descendants.
5. Call `enqueue_ready()` or `dispatch()`; expired leases are reconciled transactionally by the queue claim operation.
6. Treat all pre-restart in-memory claims as invalid. Workers must obtain a fresh claim and lease token.

## Guarantees and limits

- Queue state, attempt count, lease token, and append-only event history survive process restart in SQLite.
- Expired leases are recovered lazily on a subsequent queue claim, not by a background sweeper.
- An old claim cannot be completed through a new integration instance because its local ownership record is absent; queue lease fencing also rejects stale tokens.
- Worker registrations and active admission slots are in-memory and must be recreated.
- Recovery requires the same queue database and compatible task graph. Graph versioning/migration is not implemented.
- No payload execution, provider invocation, network dispatch, distributed locking, or exactly-once external side effects.
- This is a single-host prototype, not a production recovery service.

## Tests

```bash
python -m unittest skills.tests.test_durable_workflow_recovery -v
python -m unittest discover -s skills/tests -v
```
