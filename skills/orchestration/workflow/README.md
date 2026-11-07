# CODEN Workflow Orchestration 2.0

**Status:** Experimental / Draft. Local control-plane integration only.

## End-to-end lifecycle

1. **Intake:** validate the task contract and synthetic-only input boundary.
2. **Route:** derive a logical role and policy route from the task profile.
3. **Policy gate:** reject role mismatch, network access, and unsupported data classification.
4. **Planning:** require an explicit plan-acceptance transition.
5. **Execution boundary:** only low-risk dry-run routes can enter the execution state. No provider or adapter is invoked by this workflow facade.
6. **Validation:** validate the result contract and require an exact match to task acceptance criteria.
7. **Review:** successful validation enters independent human review; failed checks return to planning.
8. **Approval:** a reviewer distinct from the task owner binds approval to a 64-character SHA-256 artifact digest.
9. **Audit:** every state transition is recorded in the local append-only SQLite audit table.

## API sketch

```python
flow = WorkflowOrchestrator()
flow.intake(task_contract, routing_profile)
flow.accept_plan(run_id, actor="planner")
flow.start_dry_run(run_id, actor="operator")
flow.submit_validation(run_id, result_contract, actor="validator")
flow.approve(run_id, actor="independent-reviewer", artifact_hash="<64 hex chars>")
```

Use `reject` or `request_changes` for independent review decisions. The latter returns the workflow to planning.

## Tests

Run from repository root:

```bash
python -m unittest skills.tests.test_workflow_orchestration -v
python -m unittest discover -s skills/tests -v
```

## Explicit non-capabilities

- Does not invoke Factory AI, Manus, Codex, OpenHands, or any other provider.
- Does not dispatch tools or execute code.
- Does not create an OS/container/network sandbox.
- Does not verify artifact bytes; it records the supplied digest only.
- Does not persist routing profiles separately from runtime state; route metadata is held in process memory.
- Does not provide distributed transactions, multi-worker locking, queueing, retries, or production-grade identity and authorization.
- SQLite audit triggers protect against ordinary update/delete statements, not a privileged database administrator or file replacement.

Treat this as a tested design prototype only after the repository's CI run succeeds. It is not approved for government, citizen-data, financial, health, identity, or production workflows.
