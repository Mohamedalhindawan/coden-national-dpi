# CODEN Workflow Control Plane 1.0

**Status:** Experimental / Draft. Local single-process control facade.

The control plane unifies scheduler dispatch, worker admission pause/resume, task-state snapshots, dependency reconciliation, and per-task queue audit retrieval.

## Operations

- `pause()` blocks new dispatch requests before they claim a queue lease; existing work is not cancelled.
- `resume()` reopens worker admission.
- `dispatch(worker_id)` delegates to the DAG scheduler only while admission is open.
- `reconcile()` recalculates blocked descendants from durable queue state and reports state counts.
- `snapshot()` reports DAG task states and in-memory worker capacity.
- `task_audit(task_id)` returns the queue's append-only event history for a known graph task.

## Boundaries

This is a Python facade, not a web dashboard or remotely accessible API. Pause state, worker registrations, and active slots are in-memory and reset on process restart. Queue state remains durable in SQLite. The facade does not execute task payloads, call providers, perform network dispatch, or provide distributed control, authentication, or authorization. Operators must protect any future service wrapper with identity, role-based access, audit, and approval controls.

## Tests

```bash
python -m unittest skills.tests.test_workflow_control_plane -v
python -m unittest discover -s skills/tests -v
```
