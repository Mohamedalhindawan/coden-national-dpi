# CODEN Agent Orchestration & Multi-Agent Workforce 1.0

**Status:** Draft architecture proposal  
**Version:** 1.0.0  
**Scope:** Isolated engineering workflows and synthetic-data pilots only.

## Purpose
Define a controlled multi-agent operating model: an orchestrator decomposes an approved task, delegates bounded work to specialist roles, validates outputs, and assembles an auditable result. Factory, Codex, Manus, OpenHands, or another provider may be evaluated as an adapter; none is assumed to be connected or available.

## Design principles
1. Human accountability: every workflow has one named human owner.
2. Least privilege: each agent receives only task-specific tools and resources.
3. Explicit contracts: inputs, outputs, acceptance criteria, and failure states are machine-readable.
4. Untrusted-by-default: model output, retrieved content, repository text, and tool results require validation.
5. Deterministic control plane: permissions, approvals, retries, budgets, and state transitions are enforced outside the model.
6. Evidence over claims: material results link to artifacts, tests, and run records.
7. Reversibility: changes remain in isolated workspaces and reviewable branches.
8. Data minimization: current TAMAM work uses synthetic data only.

## Reference architecture
Human task owner → Intake and policy gate → Orchestrator/state machine → Planner → Task DAG and contracts → Specialist agent pool → Independent validation/QA → Result assembly → Human review. Audit trail, traces, metrics, cost controls, and scoped sandbox tools surround the workflow.

The orchestrator is the policy enforcement point. Models propose plans and content; the control plane validates schemas, permissions, budgets, state transitions, and approvals.

## Workflow states
| State | Purpose | Exit condition |
|---|---|---|
| INTAKE | Capture objective, owner, scope, risk and budget | Required fields complete |
| POLICY_CHECK | Classify data and action risk | Policy permits isolated execution |
| PLANNING | Create task DAG, contracts and acceptance tests | Plan accepted where required |
| READY | Pin versions, tools, fixtures and workspace | Reproducible run envelope exists |
| EXECUTING | Run bounded specialist tasks | Tasks complete or explicit failure |
| VALIDATING | Schema, tests, security and independent review | Mandatory gates pass |
| REVIEW_REQUIRED | Present diff, evidence, costs and open risks | Human approves, requests changes or rejects |
| COMPLETED | Archive evidence and outcome | Run record complete |
| FAILED / BLOCKED | Stop safely and preserve evidence | Human-directed remediation |
| CANCELLED | Stop queued and active work | Cancellation confirmed |

Approval is scoped to a specific artifact, action, environment, and version. No state transition may grant new permissions.

## Delegation defaults
- Maximum delegation depth: 2.
- Maximum concurrent specialist tasks: 4 until measured otherwise.
- No agent may spawn unbounded agents or change its own permissions.
- Handoffs carry task ID, parent ID, contract version, artifact references, and deadline.
- A specialist returns a result package; it cannot mark the workflow complete.

## Mandatory human approval
Required before merging PRs, deploying, provisioning infrastructure, spending money, accessing real citizen or sensitive data, making decisions affecting eligibility/rights/health/identity/finance, sending external commitments, or changing security/data-sharing policy.

## Reliability and failure handling
Use bounded retries only for transient idempotent operations. Require idempotency keys for writes. Apply per-agent timeout, workflow deadline, concurrency cap, and circuit breaker. Preserve successful artifacts after partial failure while blocking dependent tasks. Stop and escalate on secrets, personal data, privilege escalation, or policy bypass. Never retry non-idempotent external actions automatically.

## Observability
Record run/task/agent IDs, parent-child links, provider/model/version, prompt and contract versions, tool allowlist, workspace commit, timestamps, state transitions, retries, usage/cost where available, latency, test outcomes, approvals, artifact hashes, and stop reason. Never log secrets or raw sensitive data.

## Rollout
1. Documentation and schema review.
2. Offline simulation with synthetic fixtures.
3. Single-agent sandbox pilot.
4. Two-specialist orchestration pilot.
5. Limited internal engineering workflows.
6. Reassessment before production or public-service use.

## Related specifications
- Agent catalog: AGENT_CATALOG.md
- Task/result contracts: TASK_CONTRACTS.md
- Permission matrix: PERMISSION_MATRIX.md
- State machine: STATE_MACHINE.md
- Operations runbook: OPERATIONS_RUNBOOK.md
- Synthetic pilot cases: pilot/README.md
- Deterministic validators and JSON Schemas: validator.py and schemas/ (tested in skills/tests/test_orchestration_contracts.py).
- Integrated workflow facade: workflow.py and workflow/README.md (tested in skills/tests/test_workflow_orchestration.py).

## Implementation status
This is a design and governance package. It does not install or execute Factory AI, Manus, Codex, or other agents. No orchestration runtime, credentials, provider integration, or production deployment is created.

## Local runtime prototype

The repository now includes `runtime.py`, a minimal SQLite-backed workflow control plane. It validates task envelopes, persists workflow state, enforces the documented transition graph, requires an independent human reviewer and a SHA-256 artifact digest for approval, and records append-only audit events.

This is deliberately a control-plane prototype only. It does **not** execute agent models, invoke tools, manage credentials, provide distributed locking, or offer production-grade multi-user concurrency. Run tests with:

```bash
python -m pip install jsonschema==4.23.0
python -m unittest skills.tests.test_orchestration_contracts skills.tests.test_orchestration_runtime -v
```

## Execution adapter boundary (v1.0)

The `adapters/` package introduces a fail-closed registry for tool adapters. Dispatch requires a schema-valid task envelope, a tool explicitly present in that task's `constraints.allowed_tools`, and `network: disabled`. The only supported mode is `dry_run`; live execution is rejected. Adapter receipts must explicitly state `status: simulated` and `executed: false`.

The included `DryRunAdapter` is a no-op: it does not start processes, call model providers, access the network, or mutate the workspace. Receipts include a deterministic payload SHA-256 and run/task identifiers.

Tests: `python -m unittest skills.tests.test_execution_adapters -v`.

**Not production-ready:** there is no real Factory/Manus/Codex/OpenHands integration, credential broker, sandbox, distributed queue, resource metering, or live execution. A future live adapter requires a separately reviewed threat model, sandbox design, secrets isolation, human approval, and dedicated integration tests.

## Sandbox policy helpers (v1.0)

`sandbox.py` adds a local filesystem path-policy helper. It accepts only `workspace://` URIs, checks each operation against separate read/write scope prefixes, rejects traversal and symlink components, resolves paths under a configured workspace root, and provides basic credential-pattern redaction for log-bound text.

This is **not** an OS-level security boundary. It does not isolate processes, containers, kernels, networks, or credentials; callers must not treat it as a substitute for a hardened sandbox. The current runtime and adapters still do not execute untrusted code.

Focused tests: `python -m unittest skills.tests.test_sandbox_policy -v`.

## Agent observability and evaluation metrics (v1.0)

`observability.py` provides a local SQLite metrics store and per-agent scorecard. It records run/task/agent/provider identifiers, outcome, duration, token counts, estimated USD cost, normalized quality score (0–1), policy-violation count, retry count, and an evidence reference. Aggregates include success rate, total cost, average quality and duration, token volume, policy violations, and retries.

The store uses append-only database triggers and an allowlisted field set: arbitrary prompt text, secrets, and unrecognized input fields are not persisted. Callers remain responsible for validating metric provenance; cost and quality values are reported measurements, not independently verified facts. Compare providers only on equivalent task sets and disclose sample size.

Focused test command: `python -m unittest skills.tests.test_observability -v`.

**Limitations:** local SQLite prototype only; no live provider telemetry, token-meter integration, distributed ingestion, dashboards, alerting, retention policy, or independent benchmark harness. Do not use these metrics to rank Factory/Manus or other providers until representative, reproducible evaluations have actually been run.


## Integrated workflow orchestration 2.0

`workflow.py` composes policy routing, task validation, the SQLite state machine, result validation, and independent human review into one explicit lifecycle. See `workflow/README.md` for the lifecycle and API sketch. It is still recommendation/dry-run control-plane code: no provider or tool is invoked, no code is executed, and high-impact routes remain recommendation-only.

Focused test command: `python -m unittest skills.tests.test_workflow_orchestration -v`.


## Task DAG & dependency engine 1.0

`dag.py` validates dependency graphs, detects cycles, creates deterministic topological waves, derives ready tasks, propagates blocked descendants, and evaluates bounded retry eligibility. It is a planner only: no scheduler, workers, execution, or provider calls. See `dag/README.md` and `schemas/task-graph.schema.json`. Tests: `python -m unittest skills.tests.test_task_dag -v`.


## Persistent execution queue 1.0

`queue.py` adds a durable local SQLite queue with idempotent enqueue, priority claims, worker leases and fencing tokens, heartbeat, bounded attempts, cancellation, and append-only audit events. It stores envelopes only and does not execute work or launch workers. See `queue/README.md`. Focused tests: `python -m unittest skills.tests.test_persistent_queue -v`.


## Worker admission runtime 1.0

`worker_runtime.py` adds a thread-safe in-process admission controller with allowlisted worker IDs/capabilities, per-worker and global concurrency caps, and pause/resume. It does not execute jobs, poll the persistent queue, or create worker processes. See `workers/README.md`. Tests: `python -m unittest skills.tests.test_worker_runtime -v`.


## Worker–queue integration 1.0

`worker_queue.py` connects the persistent SQLite queue to bounded worker admission: capability-filtered claims, lease heartbeat, completion/failure, and slot release. It does not execute payloads or enforce DAG dependencies. See `worker-queue/README.md`. Tests: `python -m unittest skills.tests.test_worker_queue_integration -v`.


## DAG-aware scheduler 1.0

`scheduler.py` gates queue admission on successful DAG dependencies and dispatches through `worker_queue.py`. See `scheduler/README.md`. It is an experimental local control-plane prototype, not a durable distributed scheduler.


## Durable workflow recovery 1.0

Recovery reconstructs scheduler state from the same SQLite queue and declared DAG. Expired leases are lazily reconciled on claim; blocked descendants are recalculated with `refresh_blocked()`. See `recovery/README.md`.


## Workflow Control Plane 1.0

The local control facade unifies pause/resume, guarded dispatch, state snapshots, dependency reconciliation, and task audit retrieval. See `control-plane/README.md`.


## Workflow API & Operator Interface 1.0

`operator_api.py` exposes a minimal authenticated WSGI API for status, pause/resume, DAG-ready dispatch, and task audit. Authentication is injected by the host application; see `operator-api/README.md`. It is not a standalone production service.


## Operator Dashboard 1.0

`operator-dashboard/index.html` is a self-contained Arabic RTL dashboard for workflow status, pause/resume, worker capacity, and manual dispatch. It is a static asset, not a deployed service; see `operator-dashboard/README.md` for security and API compatibility notes. Static contract test: `python -m unittest skills.tests.test_operator_dashboard -v`.


## Agent Provider Integration 1.0

`providers.py` defines provider profiles, capability allowlists, secret references, policy gates, and simulated-only receipts. No vendor API or live model is invoked. See `providers/README.md` for onboarding and production gaps; tests: `python -m unittest skills.tests.test_provider_integration -v`.


## AI Model Gateway & Intelligent Routing 1.0

`model_gateway.py` selects an eligible model by capability, context window, and estimated request cost. It is simulated-only and never invokes providers or network. See `model-gateway/README.md`; tests: `python -m unittest skills.tests.test_model_gateway -v`.


## AI FinOps & Budget Control 1.0

`finops.py` provides a local SQLite budget ledger with atomic project/team daily and monthly reservations, reconciliation, snapshots, and threshold alerts. It is not yet wired into model/provider execution. See `finops/README.md`; tests: `python -m unittest skills.tests.test_finops -v`.
