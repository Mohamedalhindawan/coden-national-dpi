# Figure 07 — TAMAM National Super-App Architecture

**Status:** Target-state conceptual architecture. TAMAM's current prototype remains a limited social-support demonstration using synthetic data; this diagram describes a possible future platform, not deployed production capability.

## Purpose
Describe TAMAM as a unified citizen/business experience and modular service platform that consumes national DPI capabilities. TAMAM is not itself the whole national DPI and should not become a monolithic replacement for authoritative government systems.

## Architecture layers
1. **Access channels:** Android/iOS, web/PWA, assisted service desks, business/partner portal and low-bandwidth/offline workflows.
2. **TAMAM app shell:** account/profile, service discovery, service catalog, mini-app container, notifications/inbox, Arabic RTL, accessibility, shared navigation and offline cache.
3. **Product domains:**
   - **TAMAM Takafol:** applications, eligibility workflows, case status, appeals and social-support service journeys.
   - **TAMAM for Business:** merchant/business services, requests, payments and partner APIs.
   - **TAMAM Marketplace:** catalog, sellers, orders, fulfillment integrations and dispute workflows.
   - **Future mini-apps:** public services in government and sectors, onboarded only after governance, security and service-owner approval.
4. **Platform services:** API gateway/BFF, workflow and case engine, domain services, event integration, data/content services, search, documents and audit.
5. **National DPI integration:** identity, payments, authoritative registries, interoperability APIs, notifications and private partners.
6. **Cross-cutting foundations:** security/privacy, consent, observability, DevSecOps, localization, accessibility, offline synchronization, backup/DR, FinOps and product analytics.

## Core design principles
- Keep the app shell separate from domain services and mini-app business logic.
- Use documented, versioned APIs and event contracts; avoid direct database coupling between organizations.
- Keep authoritative government records in their responsible systems; TAMAM stores only what it needs for service delivery.
- Design for Arabic RTL, low bandwidth, intermittent connectivity, shared devices and assisted access.
- Offline mode must define which actions are safe to queue, how conflicts resolve and when server confirmation is required.
- Use a governed mini-app onboarding process: service owner, security review, privacy assessment, API contract, UX/accessibility review, support owner and lifecycle plan.
- Separate marketplace commercial operations from public-service eligibility and government decision-making.
- Do not expose sensitive eligibility or identity data to marketplace sellers or unrelated mini-apps.

## Security and trust
Apply strong authentication appropriate to service risk, authorization per action, consent and purpose limitation where applicable, encryption, rate limiting, fraud monitoring, audit logs, secure document handling and incident response. High-impact decisions and payments require explicit controls and accountable service owners.

## Suggested delivery sequence
1. Stabilize the current synthetic-data social-support prototype and define its scope.
2. Pilot TAMAM Takafol with a real accountable service owner only after legal, privacy, security and data-sharing approvals.
3. Establish app shell, API gateway, identity integration and notification foundations.
4. Add business services and payments only with regulated/payment-partner readiness.
5. Introduce marketplace and additional mini-apps after operating controls and support processes are proven.

## Open decisions
App-shell technology; API gateway and workflow engine; identity assurance levels; payment partners; offline synchronization policy; marketplace operating model; mini-app sandbox and review rules; hosting/residency; service-level objectives and support ownership.
