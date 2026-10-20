# CODEN Free-First AI Agent Roadmap

**Status:** Proposed implementation plan — agents are not yet deployed or running autonomously.

> **Current operational guide (2026-10-20):** The verified phone-first workflow, including confirmed and unverified capabilities, is documented in [CODEN Free-First AI Agent Workflow](AGENT_WORKFLOW.md). This roadmap remains a planning document.
**Cost policy:** $0 initial spend. Paid services may be introduced later only after explicit approval.
**Scope:** CODEN national DPI and the Tamam prototype. This roadmap does not authorize production use or processing real citizen data.

## Operating principles
- Start with free tiers and open-source software; record quotas and limits before depending on a service.
- Keep model providers, agent orchestration, application code, and hosting replaceable.
- Never store API keys, passwords, access tokens, or personal data in GitHub files or issues.
- Use synthetic data only in the prototype.
- Require human approval for changes affecting identity, payments, benefit eligibility, security, legal obligations, production deployment, or spending.
- Agents may draft code and tests, but changes must pass automated checks and review before merging.

## Initial toolchain
1. GitHub Issues and repository — backlog, decisions, version history.
2. ChatGPT — requirements, design, code review, and task preparation within available access.
3. GitHub Actions — automated checks for a public repository, subject to current platform limits.
4. A browser-based development environment such as Replit only if its free allowance is sufficient; do not assume unlimited free compute or AI.
5. Open-source test and security tools added when application code exists.

## Agent roles
- **Coordinator:** selects the next approved task and tracks dependencies.
- **Product/Requirements:** converts the goal into user stories and acceptance criteria.
- **Architecture:** proposes modules, APIs, data boundaries, and replaceable interfaces.
- **Implementation:** changes only the files needed for an approved issue.
- **QA:** adds tests before behavior changes and reports test results honestly.
- **Security/Privacy:** checks permissions, secrets, data minimization, and threat scenarios.
- **Documentation/Release:** updates setup instructions and prepares release notes; cannot independently authorize production release.

These are role definitions, not evidence that independent agents are already executing. Real autonomous execution requires a connected model, an execution environment, repository permissions, and verified safeguards.

## Rollout stages
### Stage 0 — Prepare
- Define the first Tamam workflow using synthetic data.
- Add acceptance criteria, contribution rules, security rules, and a clear definition of done.
- Keep the repository public only if all contents are safe to disclose.

### Stage 1 — Testable prototype
- Build one small social-assistance request workflow.
- Start with a responsive Arabic RTL web prototype before expanding to mobile.
- Include role-based access concepts, audit events, and a human-review state.
- Add unit and integration tests before implementing business logic.

### Stage 2 — Automated checks
- Run formatting, tests, dependency/security checks, and build validation on pull requests.
- Fail closed when checks fail; do not auto-merge sensitive changes.
- Publish a concise report of passed/failed checks.

### Stage 3 — Controlled agent execution
- Connect one agent at a time to an isolated branch or workspace.
- Limit permissions to the minimum required; no unrestricted production credentials.
- Have the coordinator create small tasks, require tests, and request human review.
- Measure cost, reliability, rework, and time saved before adding more agents.

### Stage 4 — Expand and reassess costs
- Evaluate orchestration, deployment, monitoring, backups, and provider options.
- Introduce paid tools only after explicit approval and a cost/benefit review.
- Preserve portability so the model or platform can be changed without rewriting core business logic.

## Definition of done for each task
- Acceptance criteria are explicit.
- Tests are added for new behavior and run using the project's documented commands.
- Security and privacy implications are reviewed.
- No secrets or real citizen data are committed.
- Results and known limitations are documented.
- Human review is completed where required.
