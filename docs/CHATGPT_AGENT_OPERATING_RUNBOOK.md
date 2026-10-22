# ChatGPT + AI Agent Operating Runbook

**Status:** Proposed operating runbook for review  
**Scope:** CODEN / Tamam prototype only  
**Cost target:** Start at $0 incremental spend; verify all current plan limits before relying on a service  
**Data rule:** Synthetic/demo data only  
**Production status:** Not authorized for production

## 1. What this runbook establishes

Use ChatGPT as the planning, product, architecture, and review interface. Use a separate coding agent only when an execution environment is available and connected to the repository. GitHub remains the source of truth for code, tasks, review, and test evidence.

A tool being connected to ChatGPT does not mean every operation is enabled, and it does not mean a background agent is running continuously. Confirm the actual permissions and test one small operation before relying on a connector.

## 2. Initial toolchain

- **ChatGPT:** clarify requirements, create acceptance criteria, inspect repository content through available connectors, review diffs, explain test results.
- **GitHub:** source control, issues, branches, pull requests, CI results.
- **Codex or another coding agent:** optional implementation in a controlled branch/workspace. Verify account eligibility, quotas, and environment access before relying on it.
- **GitHub Actions:** run the existing prototype contract tests and OpenAPI validation.
- **Supabase:** no project is currently identified through the connected accounts. Do not create a project or add a backend until the user approves the design, budget, and data boundaries.
- **n8n:** defer until a real repeatable workflow needs orchestration. It is not required for the first milestone.

## 3. Safe first workflow

1. Open the repository and read `AGENTS.md`, `README.md`, `docs/PROJECT_OVERVIEW.md`, and the relevant tests.
2. Create or select one GitHub Issue for a narrowly scoped task.
3. Write acceptance criteria and list files allowed to change.
4. Create a short-lived feature branch; never let an agent work directly on `main`.
5. Ask the coding agent to inspect first, propose tests, then implement only the approved task.
6. Run `python -m unittest discover -s tests -v` from the repository root.
7. Run the OpenAPI validator used by the existing CI workflow.
8. Review the complete diff for correctness, accessibility, RTL behavior, privacy, secrets, and dependencies.
9. Open a pull request with test evidence and known limitations.
10. Merge only after checks pass and a human reviews and approves the changes.

If a local/cloud execution environment is not available, use ChatGPT and GitHub to prepare the task and review artifacts; do not claim the code or tests ran.

## 4. Existing CI

The current workflow is `.github/workflows/prototype-checks.yml`. It runs on pushes to `main`, pull requests, and manual dispatch. It has read-only repository contents permission and runs:

- `python -m unittest discover -s tests -v`
- `python -m pip install openapi-spec-validator==0.7.2`
- `python -m openapi_spec_validator api/openapi.yaml`

A workflow definition is not evidence of a successful run. Verify the actual run status and logs in GitHub Actions before reporting that checks passed.

## 5. Agent responsibilities

| Role | Allowed work | Must not do autonomously |
|---|---|---|
| Coordinator | Break approved goals into issues and tasks | Expand scope without approval |
| Product/Requirements | Draft user stories and acceptance criteria | Declare institutional policy |
| Architecture | Propose interfaces, boundaries, threat model | Connect real government systems |
| Implementation | Edit scoped files and add tests on a branch | Merge to main or deploy production |
| QA | Run tests and report reproducible results | Claim unrun tests passed |
| Security/Privacy | Review permissions, data minimization, dependencies, secrets | Approve its own high-impact changes |
| Documentation | Update guides and record decisions | Represent planned work as implemented |
| Release/Ops | Prepare release checklist and rollback plan | Deploy production without explicit approval |

These roles may initially be checklists or separate prompts, not separate running agents. Add multi-agent orchestration only after the single-agent workflow is reliable.

## 6. Permission model

- Begin with read access; grant write access only to the repository and branch needed for the task.
- Keep production credentials, payment credentials, private keys, and personal data out of prompts, source files, issues, and logs.
- Do not use real citizen, beneficiary, identity, financial, or health data in the prototype.
- Require explicit human approval before changes involving identity, payments, eligibility, security policy, legal commitments, spending, external data sharing, merging, or production deployment.
- Prefer pull requests over direct commits to `main`.
- Keep CI permissions at the minimum required and avoid privileged third-party actions.
- Store secrets only in an approved secrets manager or protected CI secret store when truly needed; never place them in repository files.

## 7. CODEN/Tamam boundaries

Current prototype is a browser-only demo with synthetic data. It has no production backend, real authentication, server persistence, official benefit application, or payment capability. Do not introduce any of those as part of the first agent setup.

The next product milestone should remain a single synthetic-data Tamam workflow with clear states, accessibility, Arabic RTL support, validation, and tests. Evaluate real backend and identity/data-exchange architecture separately after institutional authority, privacy requirements, security design, operational ownership, and budget are documented.

## 8. Cost and reliability measurements

Track per task:

- elapsed time from issue creation to reviewed pull request;
- tests passed/failed and the exact command or CI run;
- number of human corrections and rework cycles;
- model/tool usage and any paid charges;
- security/privacy findings;
- whether the task met its acceptance criteria.

Do not promise a fixed automation percentage in advance. Expand autonomy only when measured quality and review effort justify it.

## 9. First milestone checklist

- [ ] Confirm repository and account permissions.
- [ ] Inspect current workflow and verify one actual CI run.
- [ ] Choose one small UI or documentation task.
- [ ] Work on a branch and submit a reviewable PR.
- [ ] Record real test outcomes.
- [ ] Review access controls and public-repository contents.
- [ ] Decide whether an external coding-agent environment is needed.
- [ ] Keep new paid services and backend creation on hold pending explicit approval.

## 10. Definition of done

A milestone is complete only when its acceptance criteria are met, test outcomes are evidenced, the diff is reviewed, no secrets or real personal data are included, limitations are documented, and any required human approval is recorded.
