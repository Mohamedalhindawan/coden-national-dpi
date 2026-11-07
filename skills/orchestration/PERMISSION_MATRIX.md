# CODEN Agent Permission Matrix 1.0

This is a proposed default-deny policy. Enforcement must occur in the execution platform, not prompt text alone.

| Role | Read approved workspace | Write task branch | Run tests | External network | Secrets | Merge PR | Deploy | Spend |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Orchestrator | Scoped | No | No | No by default | No | No | No | No |
| Planner | Scoped | No | No | Approved sources only | No | No | No | No |
| Architect / DPI | Scoped | No | No | Approved sources only | No | No | No | No |
| Developer | Scoped | Yes | Yes | Deny by default | No direct access | No | No | No |
| Data | Synthetic fixtures only | Scoped | Yes | Deny by default | No | No | No | No |
| Security reviewer | Scoped | Findings only | Approved scanners | Approved sources only | No secret values | No | No | No |
| QA / Evaluation | Scoped | Test artifacts only | Yes | Deny by default | No | No | No | No |
| Documentation | Scoped | Docs branch only | Documentation checks | Approved sources only | No | No | No | No |
| FinOps | Cost metadata only | Report branch only | No | Approved pricing sources | No | No | No | No |
| Release coordinator | Release artifacts only | No | Read CI results | No by default | No | No | No | No |

## Human-only actions
Human approval and human credentials are required for merging PRs, production deployment/rollback, protected branch or security policy changes, real sensitive-data access, purchases/subscriptions/budget increases, legal/policy/eligibility/identity/health/financial decisions, and official external commitments.

## Enforcement requirements
- Default deny; grants are per-task and expire automatically.
- Use short-lived scoped tokens; never expose token values to model context.
- Separate read, write, approval, and deployment identities.
- Enforce network egress allowlists and workspace boundaries.
- Log authorization decisions without secret values.
- Revoke grants on completion, timeout, cancellation, or policy failure.
- A prompt instruction is not a security boundary; platform controls must enforce this matrix.
