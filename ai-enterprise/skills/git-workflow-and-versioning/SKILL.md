---
name: git-workflow-and-versioning
description: Safe branch and release workflow for CODEN Playbook V4.0
version: 0.1.0
status: draft
owner: CODEN Engineering Leadership
---
# git-workflow-and-versioning

## Purpose
Safe branch and release workflow. This is a repository-local operating skill, not an installed autonomous agent.

## Scope and prerequisites
Read `AGENTS.md`, the applicable approved playbook sections, target source files and relevant tests. Use only explicitly authorized tools and synthetic data.

## Procedure
Work on feature branches, open reviewable pull requests, link issues and evidence, follow semantic versioning, and require authorized human approval for high-impact changes. Never self-merge or deploy production.

## Outputs
PR description, verification record, release notes when applicable.

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
