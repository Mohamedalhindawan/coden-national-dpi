# CODEN DAG-Aware Scheduler 1.0

**Status:** Experimental / Draft. This component gates queue admission using the declared task dependency graph.

## Contract

Each task is declared as:

```python
{
    "task_id": "task-b",
    "depends_on": ["task-a"],
    "payload": {"kind": "synthetic-test"}
}
```

The scheduler validates the graph with the DAG planner, enqueues only tasks whose dependencies have succeeded, and dispatches through the worker–queue integration. Completion can unlock downstream tasks on the next `enqueue_ready()` or `dispatch()` call. Failed, cancelled, or blocked dependencies propagate a blocked state to descendants through `refresh_blocked()`.

## Example

```python
scheduler = DAGAwareScheduler(queue, worker_queue_integration, task_graph)
scheduler.enqueue_ready()
claim = scheduler.dispatch("worker-a")
if claim:
    scheduler.complete(claim, {"status": "simulated"})
scheduler.enqueue_ready()  # newly ready descendants are now eligible
```

## Safety and limitations

- It never executes task payloads and never invokes providers, subprocesses, or networks.
- Queue task IDs must be unique within this scheduler graph.
- This prototype uses an in-memory blocked-state overlay; restart reconstruction and durable DAG state are not yet implemented.
- The queue and worker integration are local SQLite/in-process components; there is no distributed scheduler or atomic transaction across queue and worker slots.
- Retries remain governed by queue attempt limits. A retryable failure remains pending; downstream tasks remain gated until success or terminal failure.
- Call `refresh_blocked()` after a dependency reaches failed/cancelled status to mark descendants blocked in the scheduler view.
- This is not a production workflow engine. It lacks durable graph versioning, multi-process coordination, fairness policy, dead-letter management, and execution sandboxing.

## Tests

```bash
python -m unittest skills.tests.test_dag_scheduler -v
python -m unittest discover -s skills/tests -v
```
