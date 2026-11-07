# CODEN Agent Task DAG & Dependency Engine 1.0

**Status:** Experimental / Draft. Deterministic planning logic only.

## Capabilities

- Validates unique task identifiers, dependency references, and duplicate/self dependencies.
- Detects directed cycles and rejects invalid graphs.
- Produces deterministic topological execution waves. Tasks in the same wave have no dependency ordering between them and are candidates for parallel work.
- Derives ready tasks only when every dependency has succeeded.
- Propagates blocked status to transitive descendants of failed, blocked, or cancelled tasks.
- Evaluates bounded retry eligibility against the task's declared `max_retries` (0–3).

## Example

```python
from skills.orchestration.dag import build_execution_plan, ready_tasks

tasks = [
    {"task_id": "design", "depends_on": []},
    {"task_id": "api", "depends_on": ["design"]},
    {"task_id": "ui", "depends_on": ["design"]},
    {"task_id": "integration", "depends_on": ["api", "ui"]},
]
plan = build_execution_plan(tasks)
# waves: [["design"], ["api", "ui"], ["integration"]]
ready = ready_tasks(tasks, {"design": "succeeded"})
# ready: ["api", "ui"]
```

## Validation

```bash
python -m unittest skills.tests.test_task_dag -v
python -m unittest discover -s skills/tests -v
```

## Safety and limitations

This engine does not create workers, schedule jobs, execute tasks, perform retries, or invoke providers. A retry decision is only an eligibility calculation. Parallel waves are a plan, not evidence that concurrency was safely provisioned. It has no durable DAG run store, distributed locking, resource quotas, cancellation propagation to live processes, or integration with the workflow runtime yet.

Use synthetic fixtures for development. Do not use it to orchestrate production, personal, health, identity, financial, or government data workflows.
