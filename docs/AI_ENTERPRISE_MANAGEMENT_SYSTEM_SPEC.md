# CODEN AI Enterprise Management System — Stage 3 Specification

**Status:** Draft requirements only | **Version:** 0.1.0 | **Date:** 2026-11-07  
**Boundary:** Synthetic data, read-only design, no live agents or external side effects.

## Purpose
Define the management and governance layer for CODEN's AI-native engineering organization. It coordinates portfolios, projects, human owners, teams, agent roles, skills, work items, approvals, evidence, quality, risk, and cost.

GitHub remains the source of truth for source code, issues, pull requests, commits, and CI evidence. This system provides a governed management view; it is not a replacement for GitHub, ERP, HR, or an autonomous decision-maker.

## Outcomes
1. Traceable records for initiatives and work items.
2. A named human owner for every initiative and workflow.
3. Agent work bounded by role, skill, task contract, tool allowlist, data class, budget, and deadline.
4. Progress measured from linked evidence, not model-generated claims.
5. Human approval for high-impact decisions and external side effects.
6. Management visibility into delivery, quality, risk, workload, and cost with data minimization.

## Non-goals
- No autonomous hiring, firing, employee scoring, or surveillance.
- No automated citizen eligibility, identity, health, or payment decisions.
- No production deployment, cloud provisioning, procurement, or paid model calls.
- No real government, donor, banking, identity, HR, or citizen-system connections.
- No live Factory AI, Manus, Codex, OpenHands, or other provider integration.
- No assumption that PR #26 orchestration modules are production-ready.

## Logical modules
| Module | Responsibility | Records |
|---|---|---|
| Enterprise Directory | Organizational units, human owners, teams, roles | OrgUnit, Principal, Team, Role |
| Portfolio & Strategy | Objectives, portfolios, programs, initiatives | Objective, Portfolio, Program, Initiative |
| Project Management | Scope, milestones, dependencies, risks, decisions | Project, Milestone, Dependency, Risk |
| Workforce Registry | Human and agent identities/capabilities | WorkforceMember, AgentProfile, Capability |
| Skills & Standards | Versioned skills and evaluations | Skill, SkillVersion, SkillEvaluation |
| Work Orchestration | Work requests, task graphs, contracts | WorkItem, Task, Assignment |
| Approval & Controls | Approvals, policies, separation of duties | Approval, Policy, Control |
| Quality & Assurance | Tests, findings, acceptance evidence | QualityGate, TestRun, Finding |
| Knowledge & Records | Decisions, architecture records, artifacts | KnowledgeRecord, ADR, Artifact |
| Performance & FinOps | Delivery metrics, usage, budgets, costs | Metric, Budget, CostRecord |
| Audit & Compliance | Append-only events and evidence | AuditEvent, EvidenceReference |

These are logical domains, not a mandate for eleven microservices. Start with a modular monolith or a few bounded modules until scale and ownership justify distribution.

## Core relationships
- Objectives contain portfolios; portfolios contain programs; programs contain initiatives.
- Initiatives own projects; projects contain milestones, risks, decisions, and work items.
- Work items decompose into tasks with an acyclic dependency graph.
- Tasks may be assigned only when role, skill, policy, data class, and tool constraints match.
- Agent profiles reference versioned skills and provider capabilities; a profile does not grant permissions.
- Approvals bind to one exact artifact digest, action, and target environment.
- Every privileged action and state transition creates an audit event.
- Metrics and cost records link to run, task, project, and team identifiers where available.

## Minimum entities
- **HumanPrincipal:** principal_id, display_name, relationship_type, status, organization_unit_id, role_ids, manager_id, created_at. Exclude national IDs, payroll data, personal secrets, and unnecessary personal information from the pilot.
- **AgentProfile:** agent_id, provider/model references, profile_version, status, capability_ids, skill_version_ids, risk_tier. Credentials are references to a future secrets broker; never store secret values.
- **Project:** project_id, name, objective_id, owner_principal_id, status, risk_tier, data_class, budget_id, dates.
- **WorkItem:** work_item_id, project_id, title, owner_principal_id, priority, status, acceptance_criteria, data_class, allowed_tools, budget_limit, deadline, evidence_refs.
- **Approval:** approval_id, subject, artifact_digest, action, environment, requester, approver, decision, reason, timestamps. Approval expires if artifact, action, or environment changes.
- **AuditEvent:** event_id, actor, action, subject, timestamp, correlation_id, outcome, evidence_ref, redacted_metadata. Append-only; secrets and raw sensitive payloads prohibited.

## Role and permission model
Use RBAC for broad functions and attribute checks for project, team, data class, environment, and action. Effective permission is the intersection.

Initial roles: Executive Sponsor, Portfolio Manager, Project Manager, Human Engineer, Agent Operator, Agent, QA/Security Reviewer, Finance Operator, Finance Approver, Auditor.

Separation of duties:
- Requesters cannot approve their own high-impact requests.
- Agents cannot approve their own output.
- Finance operators cannot approve their own reconciliations.
- Client-supplied project/team identifiers are not proof of authorization.
- Scope comes from trusted authenticated principal claims and is checked server-side.

## Workflow lifecycle
DRAFT → SUBMITTED → POLICY_REVIEW → APPROVED → READY → IN_PROGRESS → VALIDATING → HUMAN_REVIEW → ACCEPTED.  
Alternative states: REJECTED, BLOCKED, CANCELLED, FAILED.

Deterministic code enforces transitions. Agents cannot change their own role, permissions, budget, policy, or approval state. Mandatory quality/security failures block acceptance. Completion requires linked artifacts and evidence. Retries and cancellation are bounded and audited.

## Dashboards
Initial synthetic dashboards: executive portfolio overview; project delivery; workforce assignment/capability coverage (no employee scoring); agent operations; quality/security findings; and FinOps reservations, estimates, reconciliations, and variances.

Every metric states source, period, scope, freshness, and whether it is measured, estimated, or simulated.

## Security and data governance
- Synthetic data and data minimization by default.
- Least privilege, deny by default, server-side project/team authorization.
- Authentication/token verification remains in a trusted host identity layer.
- Separate read, propose, execute, approve, and release permissions.
- Append-only audit evidence for privileged actions; redact secrets.
- Retention requires legal and records-management review.
- Threat-model cross-project access, privilege escalation, prompt injection, tool misuse, replay, approval substitution, and supply-chain compromise.

## Integration boundaries
Initial integrations are read-only or link-only: GitHub repository/issue/PR/commit/check metadata, CI runs/artifacts, CODEN skill metadata, and simulated orchestration records. HR, finance, procurement, identity, donor, government, production infrastructure, and provider APIs require separate approval and security review.

## Delivery sequence and acceptance criteria
### 3A — Domain model
- [ ] JSON Schemas for Project, AgentProfile, WorkItem, Approval, AuditEvent.
- [ ] Stable IDs, lifecycle enums, versioning, data classification.
- [ ] Reference validation, unknown-field rejection, synthetic fixtures, contract tests.

### 3B — Authorization and audit
- [ ] Principal claims and project/team scope format.
- [ ] Server-side scope enforcement and cross-scope denial tests.
- [ ] Separation-of-duties, append-only audit, and redaction tests.

### 3C — Read-only management view
- [ ] Static synthetic dashboard.
- [ ] Provenance, freshness, measured/estimated/simulated labels.
- [ ] No write actions or external integrations.

### 3D — Human-controlled workflow pilot
- [ ] One synthetic project work item and bounded task plan.
- [ ] Simulated assignment to a draft agent profile.
- [ ] Evidence validation and human acceptance decision.
- [ ] Cancellation and blocked-state demonstrations.

Stage 3 exits only when schemas validate, authorization and separation-of-duties tests pass, audit evidence is complete and redacted, dashboard metrics are clearly labeled, no external side effects exist, and a human reviewer accepts the pilot.

## Open decisions
Confirm the organizational chart and human-only roles; select service boundaries only after deployment context exists; choose identity provider after trust boundaries are defined; define retention with legal/records owners; define project/team delegation; decide whether orchestration code should be refactored or replaced after independent review.

## Dependencies and status
This is a proposed specification, not an implemented system. Stage 3 implementation is gated on human review of Stage 1–2 pull requests:
- PR #26 is a broad Draft prototype, not production-ready.
- PR #28 addresses workflow role restrictions.
- PR #35 adds principal-bound project/team authorization for observability and is stacked on #26.
- No PR in this sequence has been merged by this work.
- Main branch protection remains unverified and requires an authorized administrator.

## Recommended decision
**GO:** domain modeling, schemas, synthetic fixtures, read-only prototypes.  
**NO-GO:** live agents, real employee/citizen data, external provider calls, finance/HR integrations, or production deployment.
