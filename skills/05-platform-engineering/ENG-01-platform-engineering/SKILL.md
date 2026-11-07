---
name: platform-engineering
description: Build paved roads and reusable internal developer platform capabilities for teams and AI agents.
---

# ENG-01 — Platform Engineering

> Status: Draft | Version: 1.0.0 | Owner: Platform Lead

## Purpose
Provide secure, repeatable, self-service engineering workflows that reduce cognitive load without hiding important controls.

## Scope
Golden paths, repository templates, CI/CD, development environments, infrastructure automation, artifact management, observability integration, and developer experience.

## Required inputs
Team workflows; supported technology stack; security baseline; deployment targets; service criticality; budget; operational capacity.

## Workflow
1. Identify repeated delivery friction and platform users.
2. Define a small paved-road capability and its supported use cases.
3. Create versioned templates, reusable pipelines, and documented interfaces.
4. Embed identity, secret management, dependency scanning, tests, and policy checks.
5. Provide isolated development/test environments and ephemeral credentials.
6. Instrument adoption, pipeline reliability, lead time, and failure rates.
7. Gather developer feedback and evolve platform capabilities incrementally.

## Deliverables
Golden-path templates; CI/CD workflows; environment definitions; platform service catalog; runbooks; versioning and deprecation policy.

## Quality gates
Templates are tested; secrets are not embedded; builds are reproducible; artifacts are traceable; rollback is documented; platform ownership and support are defined.

## Controls
Kubernetes is optional and must be justified by scale, isolation, resilience, or operational requirements. Do not assume cloud credits or services are free. Do not give agents standing production credentials.

## Evaluation
Measure onboarding time, deployment lead time, change failure rate, platform adoption, pipeline availability, and cost per workload.
