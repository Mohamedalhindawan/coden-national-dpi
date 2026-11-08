# Figure 02 — CODEN AI Agent Control Plane

**Status:** Target-state conceptual architecture. It is not evidence that these services are already deployed.

## Purpose
Define the governance and runtime control layer that registers AI agents, grants narrowly scoped capabilities, routes work, enforces policy, pauses for human decisions, and records evidence.

## Components
1. **Human governance:** named business, system, security, data and service owners; approval gates; audit and appeal.
2. **Agent registry and identity:** catalogue, accountable owner, versioned capability manifest, workload identity, risk tier, trust status, tool permissions and lifecycle state.
3. **Policy-driven orchestration:** request intake, policy/risk evaluation, planning and routing, workflow runtime, approval service, evidence/audit ledger.
4. **Specialist execution squads:** discovery/product, engineering, security/assurance, operations/knowledge.
5. **Isolated tool execution:** sandboxed workspaces, scoped credentials, network controls and secret broker. No unrestricted shell, production writes or external actions by default.
6. **Evaluation and telemetry:** task success, quality tests, cost/latency, safety events, drift and trace coverage. Evidence informs promotion, pause, rollback or retirement.

## Mandatory control principles
- Default deny; grant the minimum permissions needed for one task.
- Separate agent identity from the human user's identity.
- Short-lived credentials; never expose raw secrets in prompts, logs or artifacts.
- Require explicit human approval for production changes, financial actions, public communications, sensitive data access and legally consequential decisions.
- Keep immutable or tamper-evident records of requests, policy decisions, tool calls, approvals and outputs.
- Use isolated execution and egress allowlists; treat retrieved content and tool output as untrusted data.
- Evaluate agents before promotion and continuously monitor them after release.
- Provide kill switch, revocation, timeout, retry limits and rollback paths.

## Open design decisions
- Select workflow runtime and policy engine after a threat model and proof of concept.
- Define risk tiers, approval matrix, retention policy and audit access model.
- Determine whether the control plane is centralized or federated across engineering environments.
- Define measurable agent SLOs and evaluation datasets.

## Publication checks
Validate the agent lifecycle, trust boundaries, data classifications, approval semantics and all connectors with the security and architecture owners. Replace provisional brand colors and add the approved logo before final publication.
