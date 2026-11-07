# CODEN Agent Task Contracts 1.0

## Contract envelope
Each delegated task must have a validated envelope. Example values below are synthetic and illustrative.

    {
      "contract_version": "1.0.0",
      "run_id": "run-synth-0001",
      "task_id": "task-synth-0002",
      "parent_task_id": "task-synth-0001",
      "role_id": "QA-01",
      "objective": "Validate the synthetic demonstration workflow",
      "inputs": [{"artifact_id": "fixture-001", "uri": "workspace://fixtures/demo.json", "classification": "synthetic"}],
      "constraints": {
        "allowed_tools": ["read_workspace", "run_tests"],
        "network": "disabled",
        "write_scope": ["workspace://reports/"],
        "max_runtime_seconds": 600,
        "max_retries": 1
      },
      "acceptance_criteria": ["Required checks are reported", "No real personal data is introduced"],
      "status": "ready"
    }

Any hash field in an actual envelope must contain a verified digest; placeholders are not evidence.

## Result envelope
A result must include contract version, run/task/role IDs, status, summary, artifact references, criterion-level outcomes and evidence references, risks, tool trace reference, usage metadata where available, and whether human approval is required.

Allowed statuses: succeeded, needs_revision, blocked, failed, cancelled. Missing evidence is not a pass.

## Validation rules
- Reject unknown contract versions and role IDs.
- Reject missing owner, objective, acceptance criteria, or deadline.
- Reject permissions outside the approved role policy.
- Reject artifacts above the run's permitted data classification.
- Reject paths outside the task workspace.
- Validate output structure before downstream handoff.
- Require evidence for every claimed acceptance pass.
- Treat free text and external artifacts as untrusted input.
- Never put credentials, citizen data, or secrets in contract fields.

## Handoff protocol
1. Parent creates task envelope and pins input artifact hashes.
2. Policy gate checks role, tools, classification, budget and deadline.
3. Child receives only referenced inputs and scoped workspace access.
4. Child returns result envelope and immutable artifact references.
5. Orchestrator validates schema, evidence and policy.
6. Parent accepts, requests bounded revision, or marks blocked/failed.
7. Audit log records transition and artifact digests.

## Idempotency
Every write-capable task needs an idempotency key scoped to run, task, and operation. Reuse with a different payload must be rejected. Read-only tasks may be retried within their retry budget.
