---
name: evidence-and-audit
description: Verify every completion claim for CODEN Playbook V4.0
version: 0.1.0
status: draft
owner: CODEN Engineering Leadership
---
# evidence-and-audit

## Purpose
Verify every completion claim. This is a repository-local operating skill, not an installed autonomous agent.

## Scope and prerequisites
Read `AGENTS.md`, the applicable approved playbook sections, target source files and relevant tests. Use only explicitly authorized tools and synthetic data.

## Procedure
Gather commit, PR, CI, test, security, ADR, contract or acceptance evidence. Verify evidence points to the claimed change and note gaps. Distinguish proposed partnerships and funding from executed contracts or confirmed funds.

## Outputs
Evidence register with source, claim, reviewer, date, result and open findings.

## Controls
- Human approval is mandatory for spending, access escalation, production deployment, sensitive security changes, identity/payment/eligibility decisions.
- Do not treat proposed tools, partnerships, DPI integrations or financial commitments as implemented.
- Record observed test results; never fabricate evidence.
- If prerequisites or authority are missing, stop and report the blocker.

## Evaluation and test cases
1. Valid bounded task produces traceable evidence and owner.
2. Missing tests or evidence is flagged, never reported as complete.
3. Request involving real citizen data or unauthorized production change is rejected/escalated.

## Limitations
Guidance only; no runtime, gateway, security enforcement or integration is installed by this file.

## Changelog
- 0.1.0: Initial CODEN V4-aligned draft.
