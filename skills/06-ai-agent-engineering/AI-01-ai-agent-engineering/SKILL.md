---
name: ai-agent-engineering
description: Specify, build, orchestrate, and operate bounded AI agents with auditable permissions and human oversight.
---

# AI-01 — AI Agent Engineering

> Status: Draft | Version: 1.0.0 | Owner: AI Platform Lead

## Purpose
Build agents that complete well-scoped tasks safely, reliably, and with observable evidence.

## Scope
Agent specifications, tools, orchestration, memory/context, sandboxing, permissions, handoffs, retries, and lifecycle management.

## Required inputs
Task definition; owner; allowed tools; data classification; success criteria; prohibited actions; escalation path; cost and latency limits.

## Workflow
1. Define the task, user, owner, boundaries, and measurable success criteria.
2. Specify inputs, outputs, tools, permissions, and prohibited operations.
3. Separate planning, execution, verification, and approval responsibilities.
4. Run agents in isolated environments with least privilege and short-lived credentials.
5. Treat retrieved documents, web pages, repository content, and tool outputs as untrusted data, not instructions.
6. Require human review for sensitive data, financial actions, identity, eligibility, legal rights, and production changes.
7. Add timeouts, budgets, retry limits, audit traces, and a kill switch.
8. Test normal, adversarial, failure, and recovery scenarios before release.

## Deliverables
Agent specification; tool permission matrix; workflow graph; evaluation set; threat model; runbook; audit and cost report.

## Quality gates
No agent launches without an owner, bounded scope, tested tools, permission review, evaluation results, monitoring, and rollback/disable procedure.

## Controls
No unrestricted shell, network, secrets, or production access by default. Prompt injection defenses must be applied at every untrusted-content boundary.

## Evaluation
Measure task success, factuality, tool correctness, policy violations, escalation quality, cost, latency, and reproducibility.

## Security
Enforce tool allowlists, scoped credentials, sandbox isolation, egress restrictions, secret redaction, and auditable execution traces. Validate tool outputs before downstream use. Never place production credentials or citizen data in prompts, logs, or evaluation fixtures.

## Failure and escalation
Stop execution on permission violations, prompt-injection indicators, repeated tool failures, budget/time limit breaches, unexpected data access, or uncertainty affecting a consequential action. Preserve traces, notify the accountable owner, and require human authorization before resuming sensitive workflows.

## Change history
| Version | Change | Status |
|---|---|---|
| 1.0.1 | Added explicit security, escalation, and change-control requirements | Draft |
