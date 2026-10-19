# CODEN Reuse Register and Integration Boundaries

**Last reviewed:** 2026-10-20  
**Status:** Initial repository-discovery pass. This is not a security audit or production approval.

## Purpose

Track existing projects that may save development time for CODEN / Tamam. Prefer upstream releases and supported APIs over copying source code into this repository. Do not integrate a dependency merely because its repository is public.

## Candidate register

| Capability | Upstream candidate | Initial repository signal | Next verification |
|---|---|---|---|
| Social registry | https://github.com/OpenG2P/national-social-registry | Repository found; default branch reported as `develop`; not archived in search result | Check release/version compatibility, license, docs, APIs, test coverage, deployment and Arabic/RTL gaps |
| Registry platform | https://github.com/OpenG2P/registry-platform | Repository found; default branch `develop`; not archived in search result | Determine whether it is the correct current component and how it relates to the social registry |
| Program/benefit management | https://github.com/OpenG2P/pbms | Repository found; default branch `develop`; not archived in search result | Confirm current scope, version, dependencies, licensing, and fit to SFD workflow |
| Payment integration bridge | https://github.com/OpenG2P/g2p-bridge | Repository found; default branch `develop`; not archived in search result | Confirm supported rails and whether Yemen providers could integrate safely |
| Deployment reference | https://github.com/OpenG2P/openg2p-deployment | Repository found; default branch `main`; not archived in search result | Read current sandbox/production instructions and resource requirements |
| Authentication / access control | https://github.com/keycloak/keycloak | Repository found; default branch `main`; not archived in search result | Check current stable release, configuration hardening, MFA and role mapping |
| Secure institutional exchange | https://github.com/nordic-institute/X-Road | Repository found; default branch `develop`; not archived in search result | Review official architecture, security server requirements, governance and certificates |
| Citizen mobile app | https://github.com/flutter/flutter | Framework, not a finished Tamam application | Choose a maintained UI template only after API and accessibility requirements are defined |

**Important:** Repository existence and branch names are discovery signals only. They do not establish active maintenance, production quality, current licensing, compatibility, or security. Check each upstream repository's actual license file and tagged release before reuse.

## Proposed boundaries

- **Tamam UI:** mobile/web presentation, Arabic RTL, accessibility, citizen-friendly forms.
- **CODEN service layer:** integration adapters, API contracts, configuration and local workflow extensions.
- **OpenG2P:** candidate for social-protection registry and program-management functions, subject to fit-gap review.
- **Keycloak:** candidate for authentication and access management; not a national identity register by itself.
- **X-Road:** candidate for governed exchange between connected institutions; not a universal database or permission to access all records.
- **Human operators:** remain accountable for eligibility, appeal, correction and payment decisions.

Do not create tight source-code coupling between all these systems. Prefer documented APIs and explicit adapters. Keep local customization small and maintain an upstream update path.

## Integration gates

### Gate A — Before adopting a component
- [ ] Record exact upstream URL, release/tag or commit.
- [ ] Read the license and confirm obligations for modification, distribution, attribution and network use.
- [ ] Check latest release, issue activity, security advisories and known vulnerabilities.
- [ ] Map the required feature to a supported module/API.
- [ ] Estimate Arabic/RTL, accessibility, offline operation, support and localization work.
- [ ] List transitive dependencies and data flows.

### Gate B — Before running a sandbox
- [ ] Use synthetic data only.
- [ ] Isolate the sandbox from production and public beneficiary systems.
- [ ] Store secrets outside source control.
- [ ] Use least-privilege accounts and secure transport.
- [ ] Document resource requirements and expected cost.
- [ ] Define how to remove the sandbox and its data.

### Gate C — Before any real pilot
- [ ] Written authorization from the relevant data owner and institutional stakeholders.
- [ ] Privacy impact assessment, data minimization, retention/deletion and correction processes.
- [ ] Threat model and independent security review.
- [ ] Tested backup restoration, incident response and audit trails.
- [ ] Clear human appeal and review path for benefits.
- [ ] Legal, operational, accessibility and field-readiness review.
- [ ] Measured pilot results and a rollback plan.

## First vertical slice

Keep the first workflow narrow: **a staff member records a synthetic assistance application, a second authorized staff member reviews it, and the system records an auditable status change.**

Acceptance criteria:
1. No real personal data.
2. Arabic RTL interface and usable on a mobile viewport.
3. Role separation is explicit (applicant intake vs. reviewer).
4. The prototype never calculates or automatically decides entitlement.
5. Every status change records who performed it and when in the future backend design.
6. Invalid input is rejected with accessible Arabic feedback.
7. Automated tests run in CI.
8. The prototype clearly states that it is not an official application or payment decision.

The current static prototype does not yet provide real authentication, a database, server-side audit logs, or secure multi-user role enforcement. Do not simulate these as if they were production security controls.

## Immediate next actions

1. Read official OpenG2P documentation and deployment instructions.
2. Build a fit-gap matrix against the first SFD assistance workflow.
3. Identify the smallest sandbox configuration that is actually supported.
4. Run only after infrastructure requirements and cost are understood.
5. Keep CI status claims tied to a verified workflow run for the latest commit.
