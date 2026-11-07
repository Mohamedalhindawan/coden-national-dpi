---
name: data-quality-management
description: Measure and improve data fitness for defined uses.
---

# DAT-04 — Data Quality Management

> Status: Draft | Version: 1.0.0 | Owner: data-governance-lead

## Purpose
Measure and improve data fitness for defined uses.

## Scope
Apply to approved CODEN initiatives in this discipline and coordinate with accountable product, architecture, security, legal, and operations owners.

## Required inputs
Approved objective; accountable owner; source records; applicable constraints; data classification; budget and acceptance criteria where relevant.

## Workflow
1. Define dimensions and thresholds
2. profile data
3. establish validation rules
4. monitor drift
5. trace defects to source
6. assign remediation
7. publish quality status.

## Deliverables
Quality rules; profiling reports; issue register; scorecards.

## Quality gates
Quality thresholds are purpose-specific and owned.

## Security, privacy, and governance controls
Preserve traceability for disputed or corrected records.
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
