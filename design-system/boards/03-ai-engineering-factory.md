# Figure 03 — CODEN AI Engineering Factory

**Status:** Target-state conceptual architecture; not a claim that the pipeline is currently deployed.

## Purpose
Describe a repeatable AI-assisted product delivery system that converts an approved problem into a secure, tested, deployable and supportable digital service.

## Lifecycle
1. **Product intake and discovery:** problem statement, user needs, accountable service owner, value, constraints and measurable outcomes.
2. **Specification and planning:** research and requirements; architecture and UX design; threat model and non-functional requirements; delivery plan; versioned build specification.
3. **Build and continuous verification:** repository setup from a golden template; AI-assisted implementation; unit/integration/E2E/contract/accessibility testing; security and quality gates; pull-request review; release candidate with signed artifact and provenance.
4. **Release and operations:** progressive promotion through Dev, Test, Staging and Production; SLOs, monitoring, incident response, backups and recovery; user feedback and operational learning.
5. **Improvement loop:** evidence from production and users becomes a prioritized backlog for the next discovery cycle.

## Quality gates
- Requirements are traceable to tests and acceptance criteria.
- Every change is reviewed and built in a controlled CI environment.
- Run automated tests, static analysis, secret scanning, dependency scanning, software composition analysis/SBOM, and applicable dynamic security tests.
- Block release on critical unresolved findings, failed required tests, missing approvals or untrusted artifacts.
- Preserve artifact provenance, versioning, deployment records and rollback capability.
- Measure reliability, security, usability, delivery performance and cost.

## Human accountability
AI agents may draft specifications, implement code, run tests and prepare release evidence. Named humans remain accountable for product scope, architecture decisions, security exceptions, production promotion and public-service outcomes.

## Operating rules
- Small, reviewable changes; no direct unreviewed production writes.
- Environment separation and least-privilege credentials.
- Reproducible builds and pinned dependencies where practical.
- Feature flags and progressive rollout for high-risk changes.
- Defined SLOs, incident ownership, backup and disaster-recovery exercises.
- Track DORA-style delivery measures alongside user and service outcomes.

## Open decisions
Choose the concrete CI/CD runner, artifact registry, deployment platform, policy engine and test stack based on the product's threat model, operating environment and budget. Tool names in other CODEN planning documents are candidate options, not automatic implementation commitments.
