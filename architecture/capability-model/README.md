# CODEN Enterprise Capability Model

**Edition:** 1.0  
**Status:** Proposed enterprise capability baseline  
**Companion:** [Capability Register](capability-register.yaml)

## 1. Purpose

The Enterprise Capability Model describes **what CODEN must be able to do** to deliver its mission, independently of its current organizational chart, chosen tools or individual projects. It provides a stable structure for strategy, operating-model design, portfolio planning, investment decisions, workforce planning and architecture traceability.

A capability is an enduring ability combining people, process, information, governance and technology to achieve an outcome. It is not the same as a team, application, project or job title.

This is a proposed capability model for CODEN. It does not assert that all capabilities currently exist or are staffed.

## 2. Capability hierarchy

- **Level 1 — Domain:** A broad area of enterprise responsibility.
- **Level 2 — Capability:** An enduring ability that can be assessed, funded, owned and improved.
- **Level 3 — Sub-capability:** A more specific ability used for planning and measurement.

Capability IDs are stable identifiers. Names and descriptions may evolve, but IDs should not be reused.

## 3. Enterprise capability map

| ID | Level 1 domain | Level 2 capability groups | Primary outcome |
|---|---|---|---|
| STR | Strategy & Enterprise Direction | Strategy management; enterprise architecture; portfolio and investment; partnerships and ecosystem; public-value measurement | CODEN invests in the right outcomes and maintains a coherent enterprise direction |
| GOV | Governance, Risk & Assurance | Decision rights; policy and standards; legal and compliance coordination; risk management; audit and assurance | Work is authorized, accountable, controlled and reviewable |
| PRD | Product & Service Management | Discovery; product strategy; service design; product delivery; service lifecycle; user experience and accessibility | Useful, inclusive services are designed and improved around real needs |
| ENG | AI-Native Engineering | Requirements and specification; architecture and design; software engineering; integration engineering; quality engineering; release engineering | Reliable digital products are delivered through repeatable, evidence-based workflows |
| AIP | AI Platform & Agent Operations | Model and provider management; agent registry; agent orchestration; tool and identity permissions; evaluation and observability; human approval | AI capabilities are useful, bounded, measurable and accountable |
| DPI | Digital Public Infrastructure | DPI reference architecture; shared platform services; identity and trust patterns; interoperability; payments and messaging patterns; DPG assessment and reuse | Reusable digital foundations can support services across institutions |
| DAT | Data & Intelligence | Data governance; data architecture; data engineering; data quality; analytics and intelligence; AI data governance | Data is governed, reliable, useful and handled according to authority and purpose |
| SEC | Security, Privacy & Trust | Security architecture; identity and access; application and cloud security; privacy engineering; supply-chain security; incident coordination | Risks are reduced and trust boundaries are explicit |
| OPS | Platform, SRE & Service Operations | Platform engineering; infrastructure automation; observability; SRE; incident management; continuity and disaster recovery | Services can be operated, supported and recovered responsibly |
| FIN | FinOps & Commercial Management | Cost visibility; unit economics; budget controls; vendor and license management; procurement support; financial sustainability | Technology investment is transparent and economically sustainable |
| KNO | Knowledge & Organizational Learning | Knowledge management; decision records; documentation; lessons learned; capability development; continuous improvement | Institutional knowledge is retained and used to improve performance |
| ECO | Partnerships & Ecosystem Enablement | Institutional engagement; donor and development partner coordination; supplier ecosystem; open-source communities; standards bodies | CODEN can collaborate effectively while maintaining clear accountability |

## 4. Capability ownership model

Assign one accountable capability owner for each Level 2 capability. The owner is responsible for its definition, performance, maturity, risks and improvement roadmap—not necessarily for directly managing every person or system involved.

Each capability record should identify:

- Accountable owner role (named person only after authorization).
- Business outcome and service consumers.
- Current and target maturity.
- People, process, information, technology and governance components.
- Supporting applications, data and integrations.
- Dependencies and risks.
- Performance measures and evidence.
- Improvement initiatives and funding needs.

## 5. Capability maturity scale

| Level | Name | Description |
|---:|---|---|
| 0 | Absent | No repeatable capability or accountable ownership is evidenced. |
| 1 | Ad hoc | Work occurs inconsistently and depends on individuals. |
| 2 | Repeatable | Basic roles, practices and records exist and are used. |
| 3 | Defined | Standardized, documented and governed across relevant teams. |
| 4 | Measured | Performance, quality, risk and outcomes are measured and reviewed. |
| 5 | Adaptive | Evidence and feedback drive continuous optimization and responsible innovation. |

Maturity is assessed from evidence, not from the presence of a diagram, tool license or written policy alone.

## 6. Capability assessment dimensions

Assess each capability across six dimensions:

1. **People:** skills, capacity, role clarity and succession.
2. **Process:** defined workflows, controls, handoffs and repeatability.
3. **Information:** data, knowledge, records, quality and access.
4. **Technology:** applications, platforms, infrastructure and integration.
5. **Governance:** authority, standards, risk, compliance and assurance.
6. **Performance:** service outcomes, cost, quality, reliability and user value.

Record a maturity level and evidence for each dimension. A single average can hide critical weaknesses; retain dimension-level scores and any hard blockers.

## 7. Relationship to other CODEN architecture assets

| Asset | How the capability model uses it |
|---|---|
| Enterprise Architecture Atlas | Establishes the enterprise context and board relationships |
| Architecture Traceability Matrix | Connects capability IDs to architecture scope, evidence and owners |
| ADR Framework | Records material decisions that shape capabilities |
| Technology Radar | Tracks candidate technologies supporting capabilities |
| AI Workforce Architecture | Maps human and agent roles to bounded work within capabilities |
| Product and DPI architectures | Show how capabilities are applied to platforms and services |

## 8. From capability map to execution

1. Validate the Level 1 and Level 2 capability scope with the authorized CODEN leadership.
2. Assign accountable owners and service consumers.
3. Assess current maturity with evidence; mark unknowns explicitly.
4. Define target maturity based on mission, risk and delivery priorities.
5. Identify capability gaps and dependencies.
6. Create initiatives with outcomes, cost, milestones and owners.
7. Link each initiative to ADRs, architecture boards, technology entries and acceptance evidence.
8. Review capability performance and maturity on a defined cadence.

## 9. Initial baseline

All capabilities in the accompanying register begin with status **Proposed** and maturity **Not assessed**. Do not infer current maturity from the existence of repository documentation or prototypes. Validate the model with actual organizational mandate, staffing, operating evidence and stakeholder needs before using it as a formal performance baseline.

---

**CODEN Enterprise Capability Model — Edition 1.0**
