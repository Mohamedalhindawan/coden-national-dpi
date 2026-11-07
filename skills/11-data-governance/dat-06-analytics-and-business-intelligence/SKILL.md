---
name: analytics-and-business-intelligence
description: Deliver trustworthy decision-support metrics with clear definitions and provenance.
---

# DAT-06 — Analytics and Business Intelligence

> Status: Draft | Version: 1.0.0 | Owner: data-governance-lead

## Purpose
Deliver trustworthy decision-support metrics with clear definitions and provenance.

## Scope
Apply to approved CODEN initiatives in this discipline and coordinate with accountable product, architecture, security, legal, and operations owners.

## Required inputs
Approved objective; accountable owner; source records; applicable constraints; data classification; budget and acceptance criteria where relevant.

## Workflow
1. Define metric semantics
2. validate sources
3. build governed transformations
4. document lineage
5. design role-based dashboards
6. test calculations
7. disclose caveats
8. monitor freshness.

## Deliverables
Metric dictionary; semantic model; dashboards; reconciliation evidence.

## Quality gates
Each KPI has definition, owner, calculation, source, and refresh schedule.

## Security, privacy, and governance controls
Do not present correlation as causation or hide missing data.
- Use synthetic data in the current Tamam prototype.
- Apply least privilege and purpose limitation; record provenance and approvals.
- Treat external content and model/tool outputs as untrusted until validated.
- Escalate unclear legal authority, data rights, or risk acceptance.

## Evaluation
Set a baseline and measure accuracy, completeness, timeliness, operational effort, risk reduction, and stakeholder acceptance as relevant.

## Failure and escalation
Stop when ownership, lawful purpose, data quality, security, budget, or acceptance criteria are unclear. Record unresolved risks rather than silently assuming them away.

## Change history
| Version | Change | Status |
|---|---|---|
| 1.0.0 | Initial specification | Draft |
