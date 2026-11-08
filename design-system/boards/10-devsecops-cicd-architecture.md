# Figure 10 — CODEN DevSecOps & CI/CD Architecture

**Status:** Conceptual target architecture. It describes the intended secure delivery lifecycle, not a claim that all stages or tools are currently deployed.

## Purpose
Provide a repeatable, auditable and secure path from an approved code change to a production release, with automated quality checks and risk-based human authorization.

## Pipeline stages
1. **Commit and change control:** protected branches, traceable commits, issue linkage, peer review and approved change scope.
2. **Build:** reproducible builds, pinned dependencies, isolated runners and artifact provenance.
3. **Test:** unit, integration, API, UI/end-to-end, accessibility and performance tests as appropriate to the service.
4. **Security verification:** SAST, software composition analysis, secret detection, container and infrastructure-as-code scanning, policy and license checks.
5. **Package:** immutable artifacts, software bill of materials (SBOM), signing and provenance attestations.
6. **Release candidate:** evidence bundle, change record, risk classification and required human approvals.
7. **Progressive deployment:** development, test, staging and production; canary, blue/green or feature-flag rollout where suitable.
8. **Operate and improve:** logs, metrics, traces, SLOs, alerting, incident response, rollback and post-incident learning.

## Mandatory controls
- Least-privilege identities and short-lived credentials for CI/CD jobs.
- Protected branches, mandatory review and separation of duties for sensitive production changes.
- Secrets stored outside source code and isolated by environment.
- No deployment when critical required checks fail, unless a documented emergency exception is approved.
- Build once and promote the same immutable artifact across environments.
- Verify artifact integrity, dependencies and provenance before deployment.
- Keep deployment logs, approvals, test evidence and security findings auditable.
- Maintain tested rollback and recovery procedures.

## Security and quality gates
Define thresholds by application criticality. Typical checks include test coverage trends, contract compatibility, dependency vulnerabilities, secret leaks, container/IaC misconfiguration, license compliance, accessibility and performance regression. Critical/high findings require remediation or a formally approved, time-bound exception with compensating controls.

## AI-assisted engineering
AI agents may propose code, tests, fixes and pull requests within isolated workspaces. They must not bypass repository protections, approve their own high-impact changes, access production secrets by default or deploy to production without the required human authorization. Preserve agent identity, tool logs, diffs, test evidence and reviewer decisions.

## Deployment strategies
Use rolling releases for routine low-risk changes; canary or blue/green for services requiring controlled exposure; feature flags for reversible product changes. Database migrations must be backward-compatible where possible and have explicit recovery plans.

## Core metrics
Deployment frequency; lead time for change; change failure rate; mean time to restore; pipeline success rate; escaped defect rate; vulnerability remediation time; artifact provenance coverage; rollback success rate; and percentage of production changes with complete evidence.

## Open decisions
Runner isolation model; environment topology; signing and key management; artifact registry; release approval matrix; severity thresholds and exception policy; deployment strategy per service; evidence retention; emergency change procedure; and recovery objectives.
