# CODEN Enterprise Skills Library

Version: 1.0.0  
Status: Draft for review  
Parent framework: CODEN Enterprise Operating & Engineering Playbook 2.2

This library contains **60 registered draft skill specifications** for CODEN teams and AI agents. The registry is the inventory of record. A skill is not approved merely because its file exists.

## Structure

- `registry.yaml`: inventory, IDs, owners, paths, and lifecycle status.
- `templates/SKILL_TEMPLATE.md`: required structure for new skills.
- `tests/test_registry.py`: automated checks for the 60-skill count, unique IDs, file existence, required sections, and draft status.
- `validation/`: scoring rubric, mandatory safety gates, benchmark protocol, and case template.
- `orchestration/`: multi-agent architecture, workforce roles, task contracts, permission matrix, state machine, operations runbook, synthetic pilot scenarios, runtime controls, adapters, sandbox, observability, benchmark evaluation, policy-first routing, and integrated workflow orchestration.
- `01-strategy-governance/`: strategy and governance.
- `02-dpi-architecture/`: DPI and GovTech architecture.
- `03-product-management/`: product and service design.
- `04-software-architecture/`: software and solution architecture.
- `05-platform-engineering/`: platform and delivery engineering.
- `06-ai-agent-engineering/`: AI agent engineering.
- `07-ai-evaluation-governance/`: AI evaluation and governance.
- `08-devsecops/`: secure software delivery.
- `09-cybersecurity-architecture/`: cybersecurity architecture.
- `10-quality-engineering/`: quality engineering.
- `11-data-governance/`: data architecture, engineering, governance, privacy, and analytics.
- `12-cloud-finops-procurement/`: cloud, FinOps, financial modeling, procurement, and IP.
- `13-management-delivery/`: project and change management.

## Lifecycle

Draft → Reviewed → Tested → Approved → Published → Monitored → Updated/Retired.

Every skill must have an owner, version, scope, inputs, workflow, deliverables, quality gates, security controls, and evaluation evidence before approval.

## Safety and project boundaries

- This repository is a proposal/prototype workspace, not an approved national production environment.
- Use synthetic data only in the current Tamam prototype.
- Never place credentials, secrets, or real citizen records in skills or examples.
- AI agents must use least-privilege, short-lived access and isolated workspaces.
- Require human approval for production changes and high-impact decisions involving identity, benefits, money, health, legal rights, or citizen data.
- Do not assume any listed tool, cloud credit, partnership, certification, or government authority has been approved.

## Agent benchmark and provider evaluation

The experimental benchmark suite is documented in `orchestration/benchmark/README.md`. It evaluates submitted evidence receipts only; it does not execute external providers. No provider performance results are currently established.

## Agent routing and model selection

The experimental policy-first router is documented in `orchestration/routing/README.md`. It recommends logical roles only; it does not invoke providers, execute tools, or rank models.

## Integrated workflow orchestration

The experimental workflow facade is documented in `orchestration/workflow/README.md`. It composes task validation, routing, local state transitions, result checks, and independent human review; it does not execute providers or tools.

## How to add a skill

Copy the template, assign a unique ID, name an accountable owner, define acceptance tests, and submit the skill for review. Do not change a skill to Approved without evidence and an authorized reviewer.

## Validation

Run from the repository root:

```bash
python -m unittest discover -s skills/tests -v
```


### Task DAG & dependency planning

The experimental dependency planner is in `orchestration/dag.py`, with its contract in `orchestration/schemas/task-graph.schema.json`. It plans dependency waves and readiness; it does not execute or schedule work. See `orchestration/dag/README.md`.


### Persistent execution queue

See `orchestration/queue.py` and `orchestration/queue/README.md` for the experimental SQLite task queue. It manages durable task state and worker leases but does not execute jobs.


### Worker admission runtime

See `orchestration/worker_runtime.py` and `orchestration/workers/README.md` for bounded in-process worker admission. This is not a job executor or distributed scheduler.


### Worker–queue integration

See `orchestration/worker_queue.py` and `orchestration/worker-queue/README.md` for the experimental in-process bridge between durable queue claims and worker admission. No task execution is performed.


### DAG-aware scheduler

`orchestration/scheduler.py` connects DAG readiness and blocked-state propagation to the persistent queue and worker integration. See `orchestration/scheduler/README.md`.


### Durable workflow recovery

See `orchestration/recovery/README.md` for restart recovery behavior and limitations.


### Workflow Control Plane

See `orchestration/control-plane/README.md` for the unified local operations facade and its limitations.


### Workflow Operator API

See `orchestration/operator-api/README.md` for the minimal WSGI API, route contract, and security boundaries.


### Operator Dashboard

See `orchestration/operator-dashboard/README.md` for the Arabic RTL static dashboard asset, its API integration, and security boundaries.


### Agent Provider Integration

See `orchestration/providers/README.md` for the provider-neutral, simulated-only integration contract and security boundaries.


### AI Model Gateway & Intelligent Routing 1.0

See `orchestration/model-gateway/README.md` for simulated model selection, request cost ceilings, and security limitations.


### AI FinOps & Budget Control 1.0

See `orchestration/finops/README.md` for project/team daily and monthly budgets, atomic reservations, spend reconciliation, and threshold alerts.
