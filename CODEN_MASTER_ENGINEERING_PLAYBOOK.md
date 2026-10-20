# CODEN_MASTER_ENGINEERING_PLAYBOOK.md

**Status:** Active master guide | **Version:** 1.0.0 | **Last Updated:** 2026-10-20  
**Repository:** [Mohamedalhindawan/coden-national-dpi](https://github.com/Mohamedalhindawan/coden-national-dpi)  
**Scope:** CODEN National Digital Public Infrastructure (DPI) / Tamam Super App / Social Protection Prototype

> **Important:** This repository is a proposal and prototype, not an approved national production system. Use synthetic data only. No real beneficiary records, identity data, financial data, or production systems may be used. All high-impact changes require explicit human approval.

---

## 1. Project Vision, Scope, Principles, and Architecture

### Vision
Build reusable, secure, open-source digital foundations for Yemen that help citizens access public services and social support more easily through a unified, interoperable approach.

### Full Scope (Must Remain Visible)
- **All 31 planned sectors** and their digital systems *(see Section 2 - inventory gaps documented if missing)*.
- **National Digital Public Infrastructure (DPI)** - shared platform and interoperability architecture.
- **Tamam Super App** - citizen-facing super-app (web prototype in `app/`, Arabic RTL).
- **Shared APIs, data exchange, identity, payments, interoperability, security, and governance** capabilities.
- **X-Road** - planned secure data-exchange solution (subject to architecture and integration validation).
- **Social protection** as the initial prototype using synthetic data only.
- **AI-assisted engineering, automated testing, continuous improvement, and documentation**.

**Do not** reduce CODEN to social protection alone. **Do not** claim all 31 sectors or full DPI are implemented when planned only.

### Core Principles
1. **Start small, measure results, scale only with evidence** - narrow workflows first.
2. **Reuse proven open-source** - verify fit, license, maintenance, security before adding.
3. **Minimize data** - privacy by design, least privilege, consent/legal basis where applicable.
4. **Human oversight** - require human review for high-impact identity, financial, eligibility, security decisions.
5. **No automated final determinations** - AI suggestions never replace human judgment for eligibility/payments.
6. **Security-first** - threat model, test, document, review.
7. **Arabic RTL first** for citizen-facing interfaces.
8. **Free-first** - prefer genuinely free tools, respect quotas.
9. **Synthetic data only** in current prototype.
10. **Traceability** - distinguish planned vs implemented.

### Architecture (Current State)
- **Frontend (current):** Static HTML/CSS/JS in `app/index.html` (Tamam prototype). Arabic RTL, browser-only, in-memory storage.
- **API Contract:** OpenAPI draft in `api/openapi.yaml` (contract-first). No backend implemented.
- **Tests:** Contract tests in `tests/`, agent workflow tests, preflight tests.
- **CI:** GitHub Actions workflow `.github/workflows/prototype-checks.yml` with preflight gate.
- **Docs:** Comprehensive documentation in `docs/` and root.

See [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md) for full project context.

---

## 2. The 31-Sector Requirement and Traceable Sector Inventory

### Requirement
The master playbook must account for all 31 planned sectors. As of this document's creation, **no explicit enumerated list of all 31 sectors is present in the repository**. 

### Gap Documentation
**Status:** **GAP IDENTIFIED** - Sector inventory not found in current docs (`docs/PROJECT_OVERVIEW.md`, `README.md`, etc.).  
**Action Required:** Obtain and document the official 31-sector list from authoritative sources (project stakeholders/governance). Do **not** invent an official inventory.

### Tracking Template
When sectors are identified, track each as: Planned | In Progress | Implemented | Tested | Reviewed | Blocked, with evidence links (files, tests, PRs).

---

## 3. DPI Shared Capabilities and System Boundaries

### Planned Shared Capabilities
- **Digital Identity & Authentication** (subject to legal authority)
- **Payments & Social Assistance Delivery** (coordination with authorized institutions)
- **Secure Interoperability & Data Exchange** (X-Road under evaluation)
- **Public Service Access & Case Tracking**
- **Social Protection with Privacy/Auditability/Human Review**
- **VSLA/Community Finance** (where appropriate)
- **Shared APIs, Data Exchange Standards, Security, Governance**

### System Boundaries (Current)
- **In Scope (Prototype):** Static Tamam demo with synthetic social assistance workflow
- **Out of Scope (Now):** Real auth, databases, backends, production systems, real PII/financial data
- **Evaluation:** X-Road integration pending architecture validation

See [docs/OPENAPI_CONTRACT_REVIEW.md](docs/OPENAPI_CONTRACT_REVIEW.md) for backend implementation gates.

---

## 4. Tamam Super App Development Principles
- **Citizen-first:** Arabic RTL, mobile-first, accessible
- **Privacy-preserving:** Minimize data, no server submission in current prototype
- **Human-in-the-loop:** No automated eligibility decisions
- **Synthetic only:** Demo data, clearly labeled
- **Progressive enhancement:** Works without JS where feasible (with security safeguards)
- **No `innerHTML` with user input** (per workflow)
- **Clear limitations** stated in UI and docs

Current implementation: `app/index.html`, `app/README.md`. Tests in `tests/test_prototype_contract.py`.

---

## 5. Agent Roles and Task Coordination

### Available Roles (Single-agent staged model)
Per [docs/AGENT_WORKFLOW.md](docs/AGENT_WORKFLOW.md):

| Role | Responsibility | Output |
|---|---|---|
| Coordinator | Plan bounded tasks, acceptance criteria, scope | Checklist, files in scope |
| Frontend | Arabic RTL accessible UI | UI changes, no unsafe DOM manipulation |
| Backend/API | API changes per contract | Only if OpenAPI supports; else stop for approval |
| Testing | Tests first, run checks, report results | Test commands + exact outcomes |
| Security Reviewer | Secret scan, data review, diff review | Security assessment |
| Documentation | Keep docs accurate | Updated docs, limitations noted |

### Coordination Rules
- **Sequential by default:** One agent, six stages in order.
- **Parallel only if safe:** Only when platform demonstrably supports and changes cannot conflict.
- **Never assume:** Don't claim parallel/background/persistent execution unless observable.
- **Handoff required:** Each stage produces the required report (files, checks+results, security, limitations/next step).
- **Continue autonomously:** When previous task verified and tools/quotas available, proceed to next eligible bounded task.

---

## 6. GitHub-First Development and Pull-Request Workflows

### Workflow
1. Inspect repo state, branches, recent commits, PRs, workflows, issues
2. Create isolated branch
3. Research libraries before adding deps
4. Implement bounded change
5. Run tests/security/build validation
6. Review diff/deps
7. Open PR with evidence
8. Fix failures, re-run
9. Wait for human approval before merging sensitive changes

### Branch/Commit Rules
- Work on dedicated branch, never rewrite `main`
- One task per branch/PR
- Conventional commits: `feat:`, `fix:`, `test:`, `docs:`, `ci:`
- No generated caches/env/credentials
- No merge without human review
- No modifying repo settings/permissions/secrets

### Preflight Gate (Required)
```bash
python -m pip install -r requirements-dev.txt
python tools/agent_preflight.py
```
Runs secret scan, full test suite, OpenAPI validation. Fails if anything fails/cannot run. Never prints secret values.

See [docs/AGENT_WORKFLOW.md](docs/AGENT_WORKFLOW.md) for full Android runbook.

---

## 7. Professional Open-Source Library Evaluation

### Evaluation Criteria
For any candidate library/repo:
- **Maintenance:** Release activity, recent commits, issue response
- **Security:** Advisories, CVEs, dependency health
- **License:** Compatibility with project (prefer permissive), commercial use OK
- **Architecture:** Fits codebase, version compatibility
- **Docs/Tests:** Quality of documentation and tests
- **Performance:** Resource consumption, suitable for low-bandwidth
- **Accessibility/RTL/i18n:** Arabic RTL support where relevant
- **Mobile/Offline:** Suitability for Yemen context
- **Long-term cost:** Maintenance burden, not just stars

### Rules
- Inspect existing codebase before adding deps
- Research via GitHub + official docs
- Prefer proven free/open-source
- No deps without clear documented benefit
- Check license before copying code
- Review security/suitability before integrating into sensitive workflows
- Don't assume production-ready just for stars
- Avoid abandoned packages, duplicates, unapproved paid services

---

## 8. Testing, Debugging, Security, and Quality Assurance

### Testing Requirements
- TDD where feasible: add/update tests first, see fail, implement, pass
- Never claim tests passed without execution and observed results
- Run relevant tests + full suite as appropriate
- Regression tests for fixes when practical

### Issue Classification
Distinguish: confirmed defects, brittle tests, CI config issues, environment/infrastructure failures, missing features, security risks, architectural gaps.

### Fix Requirements
For every fix: reproduce, root cause, smallest fix, regression test if practical, run checks, review diff, document results/limitations.

### Security
- Synthetic data only
- No secrets in code/prompts/logs
- Secret scanning (preflight)
- Least privilege, read-only CI permissions where possible
- No automated eligibility decisions
- Threat model considerations
- Report exposures immediately

### QA
- HTML validation, a11y checks (axe-core) where applicable
- OpenAPI validation
- Contract tests
- Manual verification for UI changes
- Review for unrelated changes

---

## 9. Free-First Model and Tool Selection

### Policy
- Prefer genuinely free tools/libraries/models
- Respect daily quotas/limits
- No purchasing credits/subscriptions
- No private API keys/passwords requested/exposed
- If quota exhausted: use GitHub operations, existing CI, static analysis, docs, other free capabilities
- Report blocked tasks due to unavailable infrastructure
- Don't assume free access unlimited

### Verified Available (Current Environment)
- Git repo read/write, branches, commits, diffs (via tools)
- Push via authenticated mechanism (cloud_git)
- Python 3.12, Node 24
- GitHub Actions workflow exists
- Local testing
- Web research agent available

### Not Verified / Limitations
- GitHub API via gh CLI (needs auth)
- Parallel agents (limited - only researcher-web confirmed)
- Persistent background processes
- Unlimited quotas

---

## 10. Safe Deployment and Human Approval Requirements

### Human Approval Required
Explicit approval before:
- Merging consequential changes
- Modifying production systems
- Connecting real beneficiary/government data
- Changing identity/payment/eligibility/security policy behavior
- Regulatory/high-impact decisions
- Incurring costs/activating paid services

### Safety Rules
- Synthetic data only
- Isolated branches/PRs
- No force-push, no deleting important branches
- No merging just to green CI
- Least privilege
- Never bypass repo protections
- Prepare reviewable patches, agent doesn't self-approve

---

## 11. Documentation, Progress Reporting, and Continuous Improvement

### Documentation Requirements
- Update docs when behavior changes
- Document limitations clearly
- Link to evidence (files, tests, commits, PRs)
- Don't confuse docs with implementation
- Arabic explanations where practical (per AGENTS.md)

### Progress Reporting
Each task completion report must include:
1. What changed (file paths)
2. Tests actually run and exact outcomes
3. Security/privacy considerations
4. Known limitations and next step

### Continuous Improvement
- Inspect → learn → improve incrementally
- Track gaps
- Fix brittle tests appropriately (don't weaken valid tests)
- Improve tooling (like preflight) when beneficial

---

## 12. Definition of Done and Acceptance Criteria

### Definition of Done
A change is complete only when:
- [ ] Intended behavior implemented
- [ ] Relevant tests actually run
- [ ] Test outcomes reported accurately
- [ ] Diff reviewed (no unrelated changes, no secrets)
- [ ] Security/dependency implications considered
- [ ] Documentation updated if needed
- [ ] Remaining failures/limitations clearly stated

### Acceptance Criteria Template
- Observable behavior specified
- Tests added/updated as needed
- All checks pass or failures documented with reasons
- No regressions
- Follows all guardrails

---

## 13. Current Implementation Status, Known Failures, and Next Priorities

### Implementation Status

| Component | Status | Evidence | Notes |
|-----------|--------|----------|-------|
| Tamam prototype (static) | Implemented/Tested | `app/index.html`, `app/README.md`, tests pass | No-JS leak fixed; HTML/a11y validated |
| API contract (OpenAPI) | Implemented (draft) | `api/openapi.yaml`, validated | No backend yet |
| Contract tests | Tested | `tests/test_prototype_contract.py` (16 tests) | All pass |
| Agent workflow docs | Implemented | `docs/AGENT_WORKFLOW.md`, etc. | Comprehensive |
| Preflight gate | Implemented/Tested | `tools/agent_preflight.py`, tests pass | Secret scan + tests + OpenAPI |
| CI workflow | Implemented | `.github/workflows/prototype-checks.yml` | Uses preflight |
| 31-sector inventory | **Planned/Blocked** | **GAP** | Not found in repo - needs official list |
| DPI backend/services | **Planned** | Docs only | No implementation |
| X-Road integration | **Planned/Blocked** | Under evaluation | Needs validation |
| Tamam mobile app | **Planned** | Not present | Web prototype only |

### Known Failures and Verification Status
- The authoring agent reported 35 tests passing, preflight passing, HTML validation passing, and zero axe-core violations in its environment; those results were not independently verified by this PR's initial CI run.
- The latest GitHub Actions run for the clean playbook PR failed one existing contract test: `test_submission_and_review_have_accessible_feedback`. The test expects `id="feedback" aria-live="polite"` to be contiguous, while the valid HTML includes `role="status"` between attributes. The other 10 tests in that run passed.
- A separate proposed fix is available in [PR #16](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/16), whose CI run succeeded. Review and merge decisions remain human-controlled.

### Blocked/Limitations
- The repository does not contain an authoritative enumerated list of all 31 sectors; this gap is documented rather than guessed.
- Backend/DPI services, native mobile app, and X-Road integration are not implemented in the current prototype.
- Agent parallelism and background execution must be treated as unavailable unless the active tool explicitly demonstrates otherwise.
- Check GitHub Actions directly for current CI status; local tool access may vary by environment.

### Next Priorities (Ranked by Impact/Risk)
1. **[HIGH/LOW-RISK]** Review the clean playbook PR and resolve the known baseline test failure by reviewing [PR #16](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/16); re-run CI after the fix reaches the base branch.
2. **[HIGH/MED]** Obtain and document the authoritative 31-sector inventory with traceability.
3. **[MED/MED]** Consider compatible integration of improved validation UX from `feat/tamam-form-validation-feedback` branch without breaking security.
4. **[MED/MED]** Address OpenAPI contract review items as backend design progresses.
5. **[MED/LOW]** Enhance preflight with optional dependency scanning if needed.

---

## References
- [README](README.md)
- [AGENTS.md](AGENTS.md)
- [Project Overview](docs/PROJECT_OVERVIEW.md)
- [Agent Workflow](docs/AGENT_WORKFLOW.md)
- [AI Agent Toolchain](docs/AI_AGENT_TOOLCHAIN.md)
- [Free-First Roadmap](docs/FREE_FIRST_AGENT_ROADMAP.md)
- [OpenAPI Contract](api/openapi.yaml)
- [OpenAPI Contract Review](docs/OPENAPI_CONTRACT_REVIEW.md)
- [Prototype Checks Workflow](.github/workflows/prototype-checks.yml)
- [Preflight Tool](tools/agent_preflight.py)
