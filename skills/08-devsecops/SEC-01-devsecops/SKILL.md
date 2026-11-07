---
name: devsecops
description: Integrate security checks and software supply-chain controls throughout the software delivery lifecycle.
---

# SEC-01 — DevSecOps

> Status: Draft | Version: 1.0.0 | Owner: Security Engineering Lead

## Purpose
Make secure delivery repeatable by embedding automated and human security controls into engineering workflows.

## Scope
Source control, CI/CD, dependency management, secrets, code scanning, container/IaC scanning, artifact integrity, release controls, and vulnerability remediation.

## Required inputs
Repository; architecture; data classification; deployment environment; threat model; supported languages; risk and release criticality.

## Workflow
1. Establish branch protection, peer review, and protected release paths.
2. Run unit, integration, and contract tests in CI.
3. Scan secrets, dependencies, source code, containers, and infrastructure definitions.
4. Generate and retain SBOMs and artifact provenance where supported.
5. Enforce policy-as-code for required checks and deployment conditions.
6. Triage findings by exploitability, exposure, impact, and compensating controls.
7. Require authorized approval for production release.
8. Monitor deployed services and feed incidents back into engineering.

## Deliverables
Pipeline definitions; security baseline; scan reports; SBOM; remediation records; release evidence; exception register.

## Quality gates
No known exposed secret is accepted. Critical findings block release unless an authorized, documented exception and mitigation exist. Tests and scans must be evidenced, not merely listed.

## Controls
Protect CI tokens; use short-lived credentials; pin and verify dependencies where practical; restrict workflow permissions; never print secrets in logs.

## Evaluation
Measure vulnerability age, remediation time, escaped defects, pipeline control coverage, secret incidents, and release failure rate.
