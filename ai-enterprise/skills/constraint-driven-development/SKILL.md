---
name: constraint-driven-development
description: Enforce non-negotiable rules for CODEN Playbook V4.0
version: 0.1.0
status: draft
owner: CODEN Engineering Leadership
---
# constraint-driven-development

## Purpose
Enforce non-negotiable rules. This is a repository-local operating skill, not an installed autonomous agent.

## Scope and prerequisites
Read `AGENTS.md`, the applicable approved playbook sections, target source files and relevant tests. Use only explicitly authorized tools and synthetic data.

## Procedure
Read AGENTS.md and approved V4 playbook. Prevent real citizen data, secrets, autonomous spending, uncontrolled tool permissions, unreviewed production changes, and unsupported claims. Escalate any conflict to a human.

## Outputs
Constraint checklist and documented exceptions requiring approval.

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
