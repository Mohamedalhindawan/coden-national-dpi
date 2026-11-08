# CODEN Worker Admission Runtime 1.0

**Status:** Experimental / Draft. In-process admission controller.

## Purpose

Provide a deterministic, thread-safe admission boundary for a bounded worker pool. It enforces configured worker identities, task-kind capabilities, per-worker concurrency, a global concurrency ceiling, and pause/resume controls.

## Example

```python
controller = WorkerAdmissionController(
    max_workers=4,
    allowed_worker_ids=["worker-a", "worker-b"],
    allowed_task_kinds=["synthetic-test"],
)
controller.register_worker("worker-a", ["synthetic-test"], max_concurrency=2)
controller.acquire_slot("worker-a", "job-001", "synthetic-test")
controller.release_slot("worker-a", "job-001")
```

## Guarantees and limits

- All in-process state transitions are protected by a re-entrant lock.
- Unregistered workers, unapproved capabilities, duplicate active job IDs, over-capacity requests, and cross-worker releases are rejected.
- Pause blocks new admissions while existing slots remain accounted for; resume reopens admission.
- Limits: global workers 1–32, per-worker concurrency 1–8.
- This module does not poll the SQLite queue, execute task payloads, create threads/processes, renew leases, or persist worker registrations.
- It is not a distributed scheduler or a security sandbox. Worker identity is a configured string, not cryptographic authentication.
- A process restart clears its in-memory admission state. Coordinate this only with a separately managed durable queue and lease lifecycle.

## Tests

```bash
python -m unittest skills.tests.test_worker_runtime -v
python -m unittest discover -s skills/tests -v
```

Production readiness requires authenticated workers, durable worker heartbeats, queue/lease integration, graceful shutdown, resource isolation, process supervision, metrics, and chaos/concurrency testing.
