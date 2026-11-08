# Figure 06 — CODEN National DPI Reference Architecture

**Status:** Conceptual national reference architecture. It is a planning model, not a description of Yemen's currently deployed government systems or a commitment to procure particular products.

## Purpose
Provide a modular architecture for interoperable public digital services. National DPI should be treated as a coordinated ecosystem of reusable capabilities, standards, institutions and safeguards—not as one super-app or one monolithic database.

## Architecture layers
1. **Access channels:** web, mobile, PWA, assisted service centers, business APIs, USSD/messaging, call centers and offline/edge workflows.
2. **Service layer:** citizen and business journeys, workflow/case orchestration, identity journeys, payments and benefits, notifications/consent, and sector service platforms.
3. **Shared DPI building blocks:**
   - Digital identity: enrollment, proofing, authentication, credentials and federation.
   - Interoperability: API gateway, secure data exchange, common schemas and service discovery.
   - Payments: payment initiation, routing/rails, reconciliation and disbursement.
   - Registries and consent: authoritative records, consent, delegation and access decisions.
   - Messaging and workflow: notifications, event exchange, case management and scheduling.
4. **Data and exchange:** authoritative data sources, data contracts, APIs/events, analytics, metadata, lineage, quality and classification.
5. **Trust, security and resilience:** cybersecurity, privacy, IAM, PKI/certificates, audit, fraud controls, backup, disaster recovery and monitoring.
6. **Foundational infrastructure:** connectivity, compute, storage, cloud/data centers, DNS, power, edge capabilities and developer platforms.
7. **Cross-cutting national governance:** legal mandate, institutional ownership, standards, funding, inclusion, public accountability and architecture assurance.

## Reference principles
- Build once, reuse safely; avoid duplicating foundational functions in every sector application.
- Use open standards and documented APIs to reduce vendor lock-in.
- Federate data exchange where feasible; do not create a single unrestricted national data lake by default.
- Keep authoritative data ownership with designated institutions.
- Design for low bandwidth, intermittent power, assisted access and offline recovery.
- Apply privacy, security, accessibility and inclusion from the start.
- Separate identity proofing, authentication and authorization; they are related but distinct capabilities.
- Establish operational ownership, service levels, incident response and lifecycle funding for every shared building block.

## Illustrative open-source / public-good references
Potential reference implementations may include MOSIP or OpenCRVS for identity/civil registration contexts; X-Road patterns for secure interoperability; Mojaloop for interoperable payment ecosystems; Keycloak for identity and access management; OpenG2P/OpenSPP for social protection; DHIS2/OpenMRS for health information contexts; and GovStack building-block specifications. These are examples for evaluation, not automatic selections or endorsements. Suitability, licensing, localization, hosting, security and total cost must be assessed per use case.

## DPGA inventory discipline
Use the DPGA registry as an inventory and classification reference, while distinguishing software from open datasets, AI systems and open content. Registry inclusion does not by itself prove that an item is a deployable national DPI building block or suitable for a particular service.

## Adoption sequence
1. Establish governance, legal authority, institutional owners and baseline architecture.
2. Map existing systems, data owners, service journeys and connectivity constraints.
3. Prioritize a small set of high-value shared building blocks and pilot services.
4. Define standards, trust framework, interoperability agreements and operating model.
5. Integrate incrementally, measure outcomes and expand only after evidence of reliability and public value.

## Open decisions
National identity model and safeguards; authoritative registry ownership; interoperability governance; payment ecosystem participation; data-sharing legal basis; hosting/residency; service-level targets; financing and long-term operating responsibilities.
