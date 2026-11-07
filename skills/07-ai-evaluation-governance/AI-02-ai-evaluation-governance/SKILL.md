---
name: ai-evaluation-governance
description: Evaluate AI models and agent workflows for quality, safety, robustness, privacy, and cost before deployment.
---

# AI-02 — AI Evaluation and Governance

> Status: Draft | Version: 1.0.0 | Owner: AI Governance Lead

## Purpose
Make AI quality measurable and govern model/agent use according to risk rather than marketing claims.

## Scope
Use-case inventory, model selection, benchmark design, red teaming, human evaluation, model/data documentation, monitoring, and retirement.

## Required inputs
Use case; affected users; model/provider; data sources; risk classification; intended decisions; baseline workflow; deployment environment.

## Workflow
1. Register the AI use case, owner, provider, model/version, and purpose.
2. Classify impact and identify affected people, data, and rights.
3. Build representative evaluation datasets with lawful, minimized, synthetic or appropriately de-identified data.
4. Define task-specific metrics, thresholds, and failure severity.
5. Test accuracy, groundedness, robustness, bias, privacy leakage, prompt injection, tool misuse, latency, and cost.
6. Compare candidate models on the same evaluation set.
7. Document limitations, human oversight, escalation, and monitoring.
8. Re-evaluate after model, prompt, data, tool, or workflow changes.

## Deliverables
AI use-case register; model card; dataset documentation; benchmark report; red-team report; approval record; monitoring plan.

## Quality gates
No high-impact use case proceeds without documented risk assessment, human accountability, representative evaluation, incident process, and explicit approval.

## Controls
Do not use model confidence as proof of correctness. Do not permit AI-only decisions that determine citizen eligibility, access to essential services, or legal rights.

## Evaluation
Track task quality, harmful error rate, subgroup performance where lawful, privacy/security incidents, drift, escalation rate, latency, and unit cost.
