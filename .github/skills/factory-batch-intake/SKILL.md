---
name: factory-batch-intake
description: Turn a CODEN Factory development request into one small synthetic-only acceptance-ready task, with cost zero and human-review gate. Use before an agent writes or changes code.
---
# CODEN Factory — Fast task intake and specification

## Trigger
Use for a new feature, factory improvement request, task handoff or issue that is not yet a verified engineering task. This skill is a **DRAFT** procedure, not an executor.

## Steps
1. Read `AGENTS.md`, the relevant existing implementation, CI, tests and the active Draft PR chain. Reuse existing modules before proposing tools.
2. State the smallest user-visible outcome and acceptance criteria (not an entire seven-engine rebuild). Identify the exact input/output and relevant file names.
3. Specify a synthetic-only data contract. Never pass private, citizen, donor, financial or production data. Record allowed files, budget_usd=0, paid_calls=0 and a bounded execution window.
4. Split the task into: preflight, a RED test, smallest GREEN implementation, independent hidden acceptance, risk checks and review-only artifact. Include at least three visible and three hidden test cases where practical; never expose hidden cases to the coding model.
5. Specify required skill handoffs to `factory-tdd-multifile`, `factory-sandbox-preflight`, `factory-independent-review`, and/or `factory-adopt-first-gate`.
6. Deliver a one-page work order: scope, invariants, dependencies, success/failure evidence, rollback and branch/PR target.

## Acceptance/evidence
Evidence must identify the task ID, actual test run and artifact SHA. If missing, report BLOCKED and do not claim success. Human review is mandatory. The task has **no automatic merge**, no production deployment, no authorization to enable a model/provider, and no license/security approval.

Example pilot reference: `ai_factory/examples/factory-oss-admission-blockers.json` and its genuine model evidence in Draft PR #164. Do not claim that a one-function success proves multi-file execution.
