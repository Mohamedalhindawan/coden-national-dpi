# CODEN Skills Validation & Benchmarking 1.0

Status: Draft — governance approval required.

## Purpose
Evaluate whether each skill is clear, safe, repeatable, useful, and supported by observable evidence. A passing structural test does not prove that a skill performs well in practice.

## Evaluation dimensions

| Dimension | Weight | Evidence expected |
|---|---:|---|
| Scope and applicability | 10 | Clear purpose, boundaries, trigger conditions, exclusions |
| Workflow completeness | 15 | Ordered steps, decision points, inputs, outputs, exception handling |
| Technical correctness | 15 | Current, internally consistent practices; verified references where needed |
| Security and privacy | 15 | Threat awareness, least privilege, data minimization, escalation |
| Governance and human control | 10 | Accountable owner, approval boundaries, auditability |
| Deliverable quality | 10 | Concrete artifacts with acceptance criteria |
| Testability and evaluation | 15 | Reproducible scenarios, expected results, measurable criteria |
| Maintainability | 10 | Versioning, ownership, change history, dependencies |
| **Total** | **100** | |

## Rating bands

- 90–100: Candidate for approval, only after independent review and all mandatory gates pass.
- 80–89: Strong draft; targeted revisions required.
- 70–79: Material gaps; revise and retest.
- Below 70: Not ready for operational use.

A numeric score never overrides a failed mandatory gate.

## Mandatory gates (pass/fail)

1. No secret, credential, or real citizen data in the skill or test fixtures.
2. No unsupported legal, regulatory, certification, or partnership claims.
3. Explicit owner, scope, inputs, outputs, and escalation path.
4. Human approval required for consequential production actions.
5. No autonomous decision on eligibility, legal rights, health, money, or essential-service access.
6. Test cases use synthetic data and do not contact production systems.
7. No unresolved critical security or privacy finding.

## Test protocol

1. Select a skill and freeze its version and commit SHA.
2. Prepare at least three cases: normal, edge/failure, and adversarial or misuse.
3. Provide identical inputs to each candidate agent/model under the same tool permissions.
4. Capture output, tool actions, evidence, elapsed time, cost, and errors.
5. Score independently against a case-specific answer key.
6. Have a human reviewer resolve disagreements and record rationale.
7. Open remediation issues for failures; rerun after changes.
8. Preserve results; never silently replace failed runs.

## Status transitions

Draft → Reviewed → Tested → Approved → Published → Monitored → Retired.

- Reviewed requires named reviewer and completed checklist.
- Tested requires recorded cases, results, version, and evidence.
- Approved requires accountable human approval and all mandatory gates.
- Published requires an owner, support route, and release note.
- Status changes must be made in the registry through a reviewed change.

## Benchmark record fields

Skill ID; skill version; repository commit; test case ID; evaluator; model/agent and version; tool permissions; input fixture; expected criteria; observed result; dimension scores; mandatory gate outcomes; cost; latency; defects; reviewer decision; remediation link.

## First pilot scope

Start with five risk-representative skills:
- PRD-01 Digital Product Management
- DPI-02 Digital Identity Architecture
- AI-01 AI Agent Engineering
- SEC-02 Cybersecurity Architecture
- QA-01 Quality Engineering

Use only synthetic scenarios based on the Tamam demonstration. Do not infer production readiness from this pilot.
