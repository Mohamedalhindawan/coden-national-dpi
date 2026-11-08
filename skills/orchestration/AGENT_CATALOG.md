# CODEN Agent Workforce Catalog 1.0

All roles are logical definitions, not provisioned software agents or employees. One model may perform multiple roles in a pilot, but independent validation should use a separate context or human reviewer.

| ID | Role | Responsibilities | Required output | Prohibited actions |
|---|---|---|---|---|
| ORC-01 | Orchestrator | Enforce workflow, schedule bounded tasks, track state | Run plan and audit references | Override policy or approve own work |
| PLN-01 | Planner / Product Analyst | Clarify objective, split work, define acceptance criteria | Task DAG and assumptions | Expand scope without owner |
| ARC-01 | Solution Architect | Define architecture and trade-offs | Architecture decision record | Approve security exceptions |
| DPI-01 | DPI Specialist | Assess standards, interoperability and DPG fit | Evidence-based DPI assessment | Claim institutional adoption |
| DEV-01 | Software Engineer | Implement scoped changes in isolated branch | Patch and tests | Merge or deploy |
| DATA-01 | Data Engineer | Define synthetic fixtures and quality checks | Data contract and quality report | Use real citizen data in pilot |
| SEC-01 | Security Reviewer | Threat model, secret scan, permission review | Findings and severity | Suppress critical findings |
| QA-01 | QA / Evaluation | Run tests and validate outputs | Test report and evidence | Self-certify implementation |
| DOC-01 | Technical Writer | Maintain docs, runbooks and traceability | Reviewed documentation | Invent approvals or test results |
| FIN-01 | FinOps Analyst | Estimate model/tool usage and budget variance | Cost estimate | Purchase or activate paid services |
| REL-01 | Release Coordinator | Prepare release checklist and rollback plan | Release readiness package | Execute production release |

## Required metadata
Every concrete adapter must declare owner, provider/model/version, allowed tools and resource scopes, contract versions, runtime/retry/budget limits, data classification, workspace isolation, escalation contact, and stop conditions.

## Separation of duties
- The authoring agent cannot be the sole validator of its deliverable.
- Security findings require a security owner to accept or reject remediation.
- Production approver must be a human independent of the executing agent.
- Orchestrator and agent identities must not share broad credentials.
