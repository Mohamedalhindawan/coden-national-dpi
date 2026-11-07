# CODEN 31-Batch Execution Workflow

**Status:** Execution framework proposed; the original 31-batch source list must be attached before batches are named or scheduled.  
**Repository:** `Mohamedalhindawan/coden-national-dpi`  
**Project status:** Proposal/prototype only; not an approved production system.

## Purpose

Turn the project's original 31 implementation batches into traceable, reviewable work in GitHub without inventing or silently changing the source plan.

This document defines the workflow only. It is **not** the original list of 31 batches and does not claim that any batch has been implemented.

## Source-of-truth rule

1. Import the exact original 31-batch list from the Word-preparation conversation or its source document.
2. Preserve original order, names, system/tool lists, and dependencies.
3. Record the source document/conversation and revision date when known.
4. If a batch detail cannot be recovered, mark it `BLOCKED: SOURCE NEEDED`; do not infer it from sector counts or substitute a newly invented list.
5. Distinguish the 31 implementation batches from the project's 31 planned sectors. They are not assumed to be the same list.

## GitHub tracking model

- **One parent tracking issue:** links to the authoritative plan and summarizes overall progress.
- **One issue per batch:** exact scope, dependencies, acceptance criteria, test evidence, risks, and status.
- **One branch and pull request per bounded code change:** avoid mixing unrelated batches.
- **Project board fields:** Batch ID, source name, status, owner/agent role, dependencies, risk, PR, test result, and human approval.
- **Evidence:** every completed item links to changed files, CI run, and reviewed pull request.

Recommended statuses: `SOURCE NEEDED`, `READY`, `IN PROGRESS`, `BLOCKED`, `IN REVIEW`, `TESTED`, `ACCEPTED`.

## Required batch issue template

Each batch issue must contain:

- **Original batch ID and exact title**
- **Source excerpt/reference** (preserve source wording)
- **Goal and out-of-scope items**
- **Systems/tools named by the original plan**
- **Dependencies** (previous batches or prerequisites)
- **Deliverables and exact repository paths**
- **Acceptance criteria** written as observable checks
- **Test plan** and expected CI checks
- **Security/privacy review**
- **Human approval gate** for identity, payments, eligibility, security, legal/policy, deployment, or spending
- **Evidence links** (PR, commit, CI run, docs)
- **Known limitations / next step**

## Agent execution protocol

1. Read `AGENTS.md`, `CODEN_MASTER_ENGINEERING_PLAYBOOK.md`, the relevant docs, target code, and tests.
2. Select only a `READY` task whose dependencies are satisfied.
3. State a short implementation plan and files in scope.
4. Use test-driven development where practical; never claim a check passed unless it ran and the result was observed.
5. Use synthetic/demo data only. Never add citizen, beneficiary, identity, financial, or health data or secrets.
6. Make a small, isolated branch/PR. Do not push directly to `main`.
7. Run relevant tests and CI, review the diff and dependency/security implications, and report exact results.
8. Stop and request human review for high-impact decisions or changes. Agents must not self-approve or merge their own consequential work.
9. Mark a batch accepted only when its acceptance criteria and required approvals have evidence.

## Current verified boundaries

- The repository currently contains a static Tamam web prototype and an OpenAPI draft; this is not a complete backend or national DPI implementation.
- X-Road is a planned option whose fit and integration need architecture validation.
- No real beneficiary data, identity/payment production integration, or production deployment is authorized by this workflow.
- A GitHub connection or agent instruction file alone does not create a persistent autonomous agent. Agent runtime, credentials, permissions, quotas, and automation must be configured and verified separately.
- The goal of high automation is not a guarantee of 95% autonomous delivery. Measure actual throughput, defect rate, review findings, and rollback rate before expanding autonomy.

## Readiness checklist

- [ ] Recover and attach the original 31-batch list.
- [ ] Verify the original ordering and dependencies with the project owner.
- [ ] Create a parent tracking issue and 31 batch issues from the source text.
- [ ] Define project-board fields and status transitions.
- [ ] Verify CI and test baseline before implementation work.
- [ ] Configure least-privilege agent access and branch/PR protections.
- [ ] Pilot one low-risk, bounded batch before scaling.
- [ ] Review measured quality and security outcomes before increasing automation.

## First next step

Populate the exact source list first. Until then, batch-specific issues and implementation assignments remain blocked to avoid fabricating the user's original plan.
