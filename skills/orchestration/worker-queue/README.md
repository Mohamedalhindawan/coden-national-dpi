# CODEN Worker–Queue Integration 1.0

**Status:** Experimental / Draft. In-process integration of the local SQLite queue and worker admission controller.

## Flow

1. The integration reads the worker's configured capabilities.
2. The queue claims only pending tasks whose JSON `kind` matches those capabilities.
3. The worker admission controller reserves a concurrency slot.
4. Heartbeat renews the queue lease.
5. Completion or failure updates the queue and releases the worker slot.
6. A reclaimed lease fences stale completion using the queue's lease token.

## Example

```python
integration = WorkerQueueIntegration(queue, workers)
claim = integration.dispatch("worker-a", lease_seconds=60)
if claim is not None:
    integration.heartbeat(claim)
    integration.complete(claim, {"status": "simulated"})
```

## Safety and limitations

- Task payloads remain data only; this integration never executes them.
- Queue claim filtering is based on the top-level JSON `kind` field.
- Worker IDs are configured labels, not authenticated identities.
- This integration is in-process; its claim map is not durable or distributed.
- If a queue claim succeeds but admission fails, the claim is not silently discarded; its lease expires and can be reclaimed.
- External side effects are not made exactly-once by lease fencing. Any future executor must use idempotency at the side-effect boundary.
- No DAG readiness/dependency enforcement is performed here; DAG planning remains a separate control.
- Not production-ready: no process supervision, distributed coordination, sandboxed execution, provider calls, or network dispatch.

## Tests

```bash
python -m unittest skills.tests.test_worker_queue_integration -v
python -m unittest discover -s skills/tests -v
```
