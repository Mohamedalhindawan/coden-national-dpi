# CODEN Enterprise Technology Radar

**Edition:** 1.0  
**Status:** Proposed evaluation baseline — not an approved procurement or adoption list  
**Scope:** Enterprise architecture, AI engineering, national DPI, TAMAM, data, security, delivery and operations

## 1. Purpose

The Technology Radar gives CODEN a consistent way to evaluate technologies and standards, communicate recommendations, reduce duplicate tooling and manage technical risk. It is a decision-support instrument, not a shopping list or a claim that any product is deployed.

All placements in this initial edition are **provisional recommendations for evaluation**. A technology becomes an approved standard only after an accountable owner, fit assessment, security review, cost analysis and (where appropriate) an ADR are completed.

## 2. Radar rings

| Ring | Meaning | Permitted interpretation |
|---|---|---|
| **Adopt** | Preferred default for a defined use case after validation | Use for new work within documented guardrails; exceptions require rationale |
| **Trial** | Limited, time-boxed pilot with success criteria | Use only in an approved pilot or sandbox |
| **Assess** | Worth investigating; evidence is incomplete | Research and compare; do not treat as a production standard |
| **Hold** | Avoid new commitments for the stated use case pending review | Maintain only where necessary; document migration or exception plans |

A ring is always scoped to a use case. “Adopt” for source control does not mean “Adopt” for every engineering workflow.

## 3. Initial radar

### Adopt — candidate defaults, subject to validation

| Domain | Candidate | Intended use | Guardrail |
|---|---|---|---|
| Source control and change review | GitHub | Version control, pull requests, review history | Enforce protected branches, least privilege and secret scanning |
| API contracts | OpenAPI | Documented HTTP API contracts | Version contracts and run compatibility tests |
| Automated testing | pytest; Playwright | Backend and browser-level tests | Tests must be meaningful, deterministic and maintained |
| Containers | Docker / OCI images | Repeatable packaging and local/CI execution | Pin base images, scan dependencies and produce provenance |
| Infrastructure as code | Terraform | Reproducible infrastructure definitions | Require plan review, state protection and change approvals |
| Observability | OpenTelemetry | Vendor-neutral telemetry instrumentation | Minimize sensitive data in telemetry and define retention |
| Software composition evidence | CycloneDX or SPDX SBOM | Dependency inventory and supply-chain transparency | Generate from actual build artifacts and retain provenance |

### Trial — controlled pilots

| Domain | Candidate | Pilot question | Exit criteria |
|---|---|---|---|
| AI coding execution | Factory AI | Does repository-native execution improve throughput without reducing quality or control? | Reproducible tasks, reviewable diffs, security checks and measured cost |
| AI discovery and specification | Manus AI | Does assisted research/specification improve clarity and reduce rework? | Traceable sources, validated requirements and human review |
| AI coding assistants | Codex; OpenHands; Aider; Cline | Which assistant fits specific task classes and control boundaries? | Task benchmark, permission model, quality and cost comparison |
| Workflow automation | n8n | Is it suitable for bounded integrations and human-in-the-loop workflows? | Credential isolation, retries, auditability and operational ownership |
| Workflow orchestration | Temporal | Are durable workflows and recovery needs sufficient to justify its operational footprint? | Failure/replay tests, operational skills and TCO assessment |
| Identity and access management | Keycloak | Does it meet the target identity federation and application access requirements? | Threat review, lifecycle integration, resilience and usability tests |
| Policy as code | Open Policy Agent (OPA) | Can policies be expressed, tested and enforced consistently? | Policy test coverage, ownership and exception handling |
| Monitoring stack | Prometheus and Grafana | Are metrics, alerting and dashboards supportable in the target environment? | SLO dashboards, alert quality, capacity and support runbooks |

### Assess — research and fit evaluation

| Domain | Candidate | Assessment focus |
|---|---|---|
| National interoperability | X-Road | Institutional governance, trust model, deployment and local operating capacity |
| Digital public goods | GovStack building blocks | Fit to local mandates, standards, maturity, localization and integration cost |
| Public digital goods discovery | DPGA Registry | Correct classification, license, maintenance, maturity and implementation fit |
| Social protection | OpenSPP; OpenG2P | Eligibility, case management, payment rails, local policy and data governance |
| Health information | DHIS2; OpenMRS; OpenIMIS; Bahmni | Health authority ownership, workflows, data standards and support model |
| Payments interoperability | Mojaloop | Regulatory model, participants, settlement, fraud controls and operational readiness |
| Civil registration | OpenCRVS; MOSIP | Legal mandate, identity assurance, data protection and institutional readiness |
| Government service platform | DIGIT | Fit to service domains, configuration, localization and maintainability |
| Data platform and analytics | PostgreSQL; DuckDB; dbt | Workload fit, governance, skills, scale and operational complexity |
| AI model routing | LiteLLM | Provider abstraction, logging, privacy, fallback and cost controls |
| Local model serving | Ollama | Hardware fit, model quality, security and supportability |
| Agent orchestration | LangGraph | State management, observability, human approvals and failure handling |
| Secrets management | HashiCorp Vault | Threat model, key lifecycle, operational burden and recovery |
| Security scanning | Semgrep; Gitleaks; Trivy; SonarQube; OWASP ZAP | Coverage, false positives, integration effort and remediation ownership |
| Delivery platforms | Kubernetes | Operational maturity, scale requirement, resilience and total cost |
| Infrastructure automation | Ansible | Configuration management needs and operational fit |

### Hold — no blanket adoption

No technology is placed in Hold as a universal judgment in this initial edition. Use Hold only for a named technology and a defined use case when evidence supports avoiding new commitments. Record the rationale, affected systems and migration path; do not use the ring as a substitute for security review.

## 4. Evaluation scorecard

Score each candidate from 1 (weak) to 5 (strong). Record evidence and confidence; do not rely on a numerical total alone.

| Dimension | Evaluation question |
|---|---|
| Mission and user fit | Does it solve a validated problem and improve public or business value? |
| Functional fit | Does it meet required workflows and integration needs? |
| Security and privacy | Can risks, access, data handling and vulnerabilities be controlled? |
| Interoperability | Does it support open, documented and versioned interfaces? |
| Reliability | Can it meet the service's availability, recovery and support needs? |
| Maintainability | Can the team operate, upgrade and troubleshoot it over time? |
| Local capacity | Are skills, connectivity, hosting and support realistically available? |
| Cost and sustainability | What are lifecycle, hosting, licensing, training and exit costs? |
| Portability and exit | Can CODEN migrate data and workloads without unreasonable lock-in? |
| Ecosystem maturity | Are releases, documentation, security response and community credible? |

### Decision thresholds (guidance, not automatic approval)

- **Adopt candidate:** No critical security/legal gap; strong evidence across fit, operations and cost; owner and support model identified.
- **Trial:** A bounded pilot can answer material uncertainties with limited risk.
- **Assess:** More research or stakeholder input is required before a pilot.
- **Hold:** A documented risk, poor fit, unsustainable cost or strategic conflict argues against new use.

Any legal, safety, privacy or critical-security blocker overrides a favorable score.

## 5. Required technology record

Every evaluated technology should have a record containing:

- Name, category, version or release line, license and upstream source.
- Intended use case and explicit non-goals.
- Radar ring, review date, owner and confidence level.
- Alternatives considered and relevant ADR.
- Security posture, data handling and threat considerations.
- Integration, deployment, observability and recovery requirements.
- Lifecycle cost, skills and support capacity.
- Upgrade cadence, end-of-life monitoring and exit strategy.
- Pilot results, decision evidence and exceptions.

## 6. Governance and update cadence

- Review new entries before a material project commits to them.
- Review Trial entries at the end of each pilot; expire stale pilots.
- Review Adopt entries at least annually and after major security or licensing changes.
- Review Assess entries quarterly; close, promote or defer with reasons.
- Review Hold entries when a migration, replacement or risk changes.
- Link material placement changes to an ADR.
- Maintain a single accountable owner for each standard and an exception process.

## 7. CODEN-specific guardrails

1. Prefer open standards and portable interfaces, but do not equate “open source” with secure, free to operate or suitable.
2. Evaluate Digital Public Goods by category: software, data, AI systems and open content are not interchangeable.
3. Separate prototype, pilot, staging and production environments.
4. Avoid premature Kubernetes or microservices complexity when a simpler architecture meets the need.
5. Do not grant AI agents broad or persistent production credentials.
6. Keep human approval for sensitive data access, financial actions, public-service eligibility decisions and production changes.
7. Compare AI tools on real benchmark tasks, review burden, failure rates, privacy and total cost—not marketing claims.
8. Treat hosting location, connectivity, legal authority and institutional operating capacity as first-class constraints.

## 8. Initial status

This radar is an evaluation baseline only. No listed technology is asserted to be formally approved, procured, integrated or deployed by CODEN. The status of existing prototypes and repository tooling must be recorded separately with evidence.

---

**CODEN Enterprise Technology Radar — Edition 1.0**
