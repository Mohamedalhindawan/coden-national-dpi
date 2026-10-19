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
