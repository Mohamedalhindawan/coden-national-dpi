# Open-Source Reuse Assessment — CODEN / Tamam

**Status:** Research and evaluation plan; no external system has been integrated or approved for production.
**Decision:** Prefer proven open-source building blocks over recreating mature systems, while keeping the first prototype small and synthetic-data-only.

## 1. First candidate: OpenG2P

Official organization: https://github.com/OpenG2P  
Official documentation: https://docs.openg2p.org/  
Deployment repository: https://github.com/OpenG2P/openg2p-deployment

OpenG2P is the strongest first candidate for the SFD social-protection use case because it provides modular building blocks for registries, program/beneficiary management, social-payment account mapping, and disbursement integration. It is a candidate for evaluation, not a claim that every module fits Yemen unchanged.

Repositories to inspect first:
- https://github.com/OpenG2P/registry-platform
- https://github.com/OpenG2P/national-social-registry
- https://github.com/OpenG2P/pbms
- https://github.com/OpenG2P/g2p-bridge
- https://github.com/OpenG2P/openg2p-deployment

### Deployment caution

OpenG2P is not a one-click phone installation. Its current deployment documentation describes a single-node sandbox for evaluation and a multi-machine production architecture. The published production prerequisites can be substantial (for example, the documentation lists a 16-vCPU/64-GB-RAM/256-GB-storage OpenG2P cluster in one architecture). Therefore:
1. Do not promise production hosting for free.
2. Do not deploy real beneficiary data to a public demo or an unreviewed host.
3. Start with source review, architecture mapping, and a synthetic-data proof of concept.
4. Confirm current version-specific requirements before provisioning infrastructure.

## 2. Candidate building blocks

| Capability | Candidate | Proposed role | Gate before adoption |
|---|---|---|---|
| Social registry and beneficiary/program management | OpenG2P | First system to evaluate for SFD assistance workflows | Functional fit, licensing, Arabic/RTL effort, accessibility, security review, local operations |
| Login and role-based access | Keycloak — https://github.com/keycloak/keycloak | Authentication and access management where appropriate | Threat model, MFA/admin controls, integration and configuration review |
| Government data exchange | X-Road — https://github.com/nordic-institute/X-Road | Securely connect authorized institutions, not a shared unrestricted database | Governance, institution onboarding, certificates, network/security design |
| Mobile citizen experience | Flutter and a reviewed RTL-capable template | Tamam app UI | License, maintenance, accessibility, Arabic rendering, API compatibility |
| Existing demo | `app/index.html` | Small offline prototype with synthetic records only | Keep explicitly labelled as a demo; never treat as a production beneficiary system |

## 3. Integration strategy

Do not copy entire repositories into one codebase indiscriminately. Prefer supported releases and documented deployment methods; record upstream URL, exact release/tag or commit, license, local changes, and upgrade owner. Use adapters/APIs between components where practical.

Proposed sequence:
1. Review OpenG2P modules and choose one narrowly scoped SFD assistance workflow.
2. Write acceptance criteria and a data-protection threat model.
3. Run automated checks against the current CODEN prototype.
4. Create a sandbox only when suitable compute is available; use synthetic data.
5. Test Arabic/RTL usability, accessibility, audit trails, permissions, and offline field workflows.
6. Add Keycloak/X-Road only when the chosen workflow actually requires them.
7. Obtain security, legal, SFD stakeholder, and operational approval before any real data or pilot.

## 4. Non-negotiable safeguards

- Use synthetic test data until formal approval and secure infrastructure exist.
- Minimize personal data and document purpose, access roles, retention, correction, and deletion.
- Log privileged access and sensitive changes without putting secrets or unnecessary personal details in logs.
- Encrypt traffic and storage; manage secrets outside source control; test backup restoration.
- Do not let AI automatically approve, deny, or rank people for financial/social benefits. AI may assist staff, with accountable human review.
- Review dependency health, known vulnerabilities, license obligations, and upstream release activity.
- Never claim an external system is integrated, secure, or production-ready until that state has been verified.

## 5. First deliverable

Produce a short OpenG2P fit-gap report for the proposed SFD use case:
- required workflow and user roles;
- modules/APIs that already exist;
- gaps requiring configuration or customization;
- Arabic/RTL and offline constraints;
- infrastructure and recurring cost estimate;
- security/privacy/licensing risks;
- go/no-go recommendation for a synthetic-data sandbox.

## Research references

- OpenG2P overview: https://docs.openg2p.org/
- OpenG2P GitHub organization and repositories: https://github.com/openg2p
- OpenG2P deployment repository: https://github.com/OpenG2P/openg2p-deployment
- Keycloak: https://github.com/keycloak/keycloak
- X-Road: https://github.com/nordic-institute/X-Road


---

## 6. OpenG2P source review — dated snapshot (2026-11-07)

This section records a preliminary review of the official OpenG2P documentation and repositories. It is not a deployment test, security certification, legal opinion, or proof of Yemen-specific fit.

### 6.1 Product boundaries confirmed in official sources

OpenG2P describes four modular building blocks:
- **Registry:** configurable registry capabilities and registry-specific implementations.
- **PBMS:** program and beneficiary management for cash, goods, staples, and services, with rule-driven processing and review/approval workflows.
- **SPAR:** maps beneficiary identifiers to financial addresses such as bank accounts or mobile-wallet addresses.
- **G2P Bridge:** dispatches disbursement instructions to downstream service providers and supports reconciliation.

The official documentation says modules can be deployed standalone; the combined architecture connects registry, program management, payment-account mapping, and disbursement. This supports a modular fit-gap assessment rather than assuming CODEN must adopt the entire stack.

### 6.2 Repository snapshot and license evidence

Repository metadata and README/LICENSE files were inspected on 2026-11-07:

| Component | Official repository | Default branch / repository state | License evidence observed | CODEN implication |
|---|---|---|---|---|
| Registry Platform | https://github.com/OpenG2P/registry-platform | `develop`, active; updated 2026-11-06 | Repository metadata and LICENSE file identify MPL-2.0 | Review a tagged release and deployment package; do not pin production to moving develop |
| PBMS | https://github.com/OpenG2P/pbms | `develop`, active; updated 2026-11-02 | README describes mixed licensing by subdirectory: Odoo modules LGPL-3.0; core, APIs, Docker, deployment MPL-2.0. No root LICENSE file was found at the inspected path | Build a file/subcomponent license inventory; do not label the entire monorepo with one SPDX identifier |
| G2P Bridge | https://github.com/OpenG2P/g2p-bridge | `develop`, active; updated 2026-08-28 | Repository metadata and LICENSE file identify MPL-2.0 | Evaluate connectors separately; the README says connectors live in a separate repository |
| Helm charts | https://github.com/OpenG2P/openg2p-helm | `gh-pages`, active; updated 2026-11-07 | Repository metadata identifies MPL-2.0 | Pin chart versions and image digests; chart publication does not itself prove a CODEN deployment |

Important: these are repository-level observations, not a complete legal bill of materials. Transitive dependencies, Odoo modules, images, chart dependencies, fonts, and bundled assets require their own license/security review. A repository's moving `develop` branch is not a release recommendation.

### 6.3 Deployment and operational fit

The official deployment documentation distinguishes:
- **Single-node sandbox:** intended for evaluation, development, QA, and demos.
- **Production:** documented as a minimum multi-VM topology (reverse proxy, compute, storage, and backup), with additional nodes for high availability.

Therefore:
1. A synthetic sandbox is a reasonable next evaluation step only after resource sizing and isolation are agreed.
2. Do not assume the sandbox topology is production-ready.
3. Do not provision cloud resources or incur paid costs without explicit approval.
4. Record exact release/tag, image digests, Helm chart version, infrastructure prerequisites, backup/restore approach, and support ownership before a pilot.

### 6.4 Preliminary Yemen/SFD fit-gap

| Requirement | Evidence / current understanding | Status for CODEN |
|---|---|---|
| Social registry | OpenG2P Registry is designed for dynamic, configurable registries, audit trails, change approval, and consent-aware sharing | Candidate fit; local data model and governance still required |
| Program administration | PBMS documents program/beneficiary management, rule-driven workflows, entitlement calculation, and human review/approval | Candidate fit; validate exact workflow and role model |
| Human review | PBMS documentation describes review and approval workflows | Promising, but CODEN must test authorization and separation of duties |
| Digital disbursement | SPAR and G2P Bridge support financial-address mapping and downstream dispatch/reconciliation | Out of initial prototype scope; requires licensed providers, regulatory review, contracts, and security approval |
| Offline field operation | Official overview mentions offline beneficiary registration in remote areas | Scope and module/version must be verified in a sandbox; do not generalize this to full offline operation |
| Arabic and RTL | No sufficient evidence in this source review to confirm complete Arabic/RTL support across Registry, PBMS, SPAR, and Bridge | Unverified; mandatory proof-of-concept gate |
| Accessibility | No completed CODEN-side accessibility assessment of OpenG2P modules | Unverified; test against an agreed WCAG target |
| Yemen integrations | No CODEN integration exists | Not implemented |
| Security and privacy | Official material describes security, audit, consent and access controls; CODEN has not independently tested them | Requires threat model, configuration review, penetration/security testing, and legal review |

### 6.5 Recommendation

**Decision: GO for a source-level and synthetic-data sandbox evaluation; NO-GO for production adoption or real beneficiary data at this stage.**

The first sandbox should be limited to:
- one synthetic assistance-program workflow;
- registry intake and controlled update;
- program configuration;
- staff review/approval with role separation;
- audit evidence;
- Arabic/RTL and accessibility test cases;
- offline behavior test limited to documented capabilities.

Exclude real identity, payment rails, bank/mobile-wallet connections, automated eligibility decisions, and real citizen records. The CODEN/TAMAM prototype remains a separate browser-only demo; it is not an OpenG2P integration and should not be described as an offline-capable field system.

### 6.6 Required evidence before closing Issue #7

- [ ] Select exact supported release tags/commits for Registry, PBMS, Bridge, and charts.
- [ ] Complete component-level license and dependency inventory.
- [ ] Produce a reproducible sandbox deployment with synthetic fixtures.
- [ ] Test Arabic/RTL, accessibility, role separation, audit trails, and the precise offline workflow.
- [ ] Record compute sizing, backup/restore, upgrade, monitoring, and support model.
- [ ] Complete threat model and privacy/legal review.
- [ ] Record human go/no-go decision for any next-stage pilot.

### 6.7 Sources

- OpenG2P overview and modular architecture: https://docs.openg2p.org/
- Official module overview and offline-registration statement: https://docs.openg2p.org/
- Registry product description and MPL-2.0 statement: https://www.openg2p.org/registry
- PBMS product description and review workflows: https://www.openg2p.org/program-management
- SPAR and G2P Bridge functions: https://www.openg2p.org/disbursement
- Deployment topology (sandbox vs production): https://github.com/OpenG2P/openg2p-documentation/blob/latest/deployment/README.md
- Registry source and license: https://github.com/OpenG2P/registry-platform
- PBMS repository README and component license map: https://github.com/OpenG2P/pbms
- G2P Bridge repository and MPL-2.0 license: https://github.com/OpenG2P/g2p-bridge
- Helm charts repository: https://github.com/OpenG2P/openg2p-helm
