# CODEN AI Agent & Toolchain Plan

## Goal
Use AI agents to accelerate design, implementation, testing, documentation, and maintenance of the proposed CODEN / Tamam platform. AI-generated work must be reviewed; this plan does not imply that agents are already running autonomously.

## Start-now setup (mobile-friendly, free-first)
1. **GitHub** — source control, issues, pull requests, project history.
2. **ChatGPT** — requirements, architecture, task breakdown, code review, troubleshooting, and documentation.
3. **Replit** — optional browser-based prototype environment; check current free limits before relying on it.
4. **GitHub Issues** — one issue per small, testable task; acceptance criteria required.
5. **GitHub Actions** — later, run automated checks when repository workflows are added.

## Agent roles
- **Product / Requirements Agent:** turns goals into user stories, scope, acceptance criteria, and edge cases.
- **Architecture Agent:** proposes component boundaries, APIs, data flows, threat models, and technology decisions.
- **Implementation Agent:** implements one approved issue at a time and opens a reviewable change.
- **QA / Test Agent:** proposes unit, integration, accessibility, and end-to-end tests; checks acceptance criteria.
- **Security / Privacy Agent:** reviews authentication, authorization, secrets, data minimization, dependency risks, and audit logging.
- **Documentation Agent:** maintains setup guides, decisions, API contracts, and release notes.
- **Release / Operations Agent:** prepares release checklists and monitoring plans; does not deploy to production without explicit approval.

## Proposed toolchain by phase
### Phase 0 — planning on a phone
- GitHub repository and Issues.
- ChatGPT for planning and code review.
- Markdown documentation.
- Synthetic data only; no citizen or beneficiary records.

### Phase 1 — prototype
- Replit or another browser IDE, if available.
- A small web prototype before committing to a full mobile app.
- OpenAPI for API contracts.
- Automated tests and formatting checks.
- GitHub pull requests for review.

### Phase 2 — engineering foundation
- Flutter only when mobile-app scope is validated.
- PostgreSQL for relational data.
- Docker for reproducible local environments.
- Playwright for end-to-end browser tests.
- GitHub Actions for continuous integration.
- Trivy or equivalent dependency/container scanning.

### Phase 3 — integration and operations
- Evaluate X-Road for secure data exchange only after interoperability requirements and governance are defined.
- Evaluate n8n for low-risk workflow automation; use stronger workflow orchestration only when justified.
- Add observability, backups, incident response, access reviews, and security testing before any production pilot.

## Required workflow for every change
1. Product agent defines the problem and acceptance criteria.
2. Architecture/security review identifies data and safety risks.
3. Implementation agent works on a narrow task in a branch.
4. QA agent adds or runs tests.
5. Human reviewer checks the diff, tests, dependencies, and privacy impact.
6. Merge only after checks pass and a human approves.
7. Release to a test environment first; production requires explicit authorization.

## Mandatory guardrails
- Never paste API keys, passwords, private certificates, or personal data into prompts or repository files.
- Use synthetic test data until lawful authority, agreements, access controls, and privacy safeguards are established.
- Human approval is required for identity, payments, eligibility, security, legal, and production changes.
- AI must not autonomously determine real benefit eligibility or issue payments.
- Do not enable unrestricted agents or production deployment permissions.
- Keep dependencies maintained and pin versions where practical.
- Record architecture decisions and important changes.

## First backlog
1. Define the first use case and measurable success criteria.
2. Write product requirements and user roles.
3. Create a system context diagram and threat model.
4. Define data minimization and authorization rules.
5. Build a synthetic-data prototype.
6. Add automated tests and CI.
7. Review with relevant institutional and technical stakeholders.

## Cost principle
Start with tools already accessible and free tiers where available. Free limits and product capabilities can change. Do not commit to paid API usage or always-on hosting until there is an approved budget.
