---
name: factory-adopt-first-gate
description: Safely select, pin and review an open-source component for CODEN Factory, using the existing 84-source catalog without bulk installs or changing approval state.
---
# CODEN Factory — Adopt-First component acceptance

## Trigger
Use when the factory needs a library, runtime, template, source repository, connector or dependency not yet approved. Status: **DRAFT** procedure.

## Steps
1. Ask what precise existing feature is missing and whether a known CODEN component already solves it. Read `ai_factory/factory_84_registry.py` and `configs/factory_72_adopt_first.json`; the 84 entries include examples and alternatives, **not** 84 services.
2. Choose one relevant P0 source by verified ID; link it to a specific R29 ADD-xx acceptance requirement. Never count duplicated repositories as independent components.
3. Pin the exact upstream commit/release, publisher, package distribution SHA-256 and source path. Do not use a moving `HEAD`, floating tags or implicit dependencies.
4. Inspect root AND nested licenses, special commercial directories, model terms, transitive SBOM, vulnerability advisories, provenance, maintenance and compatibility. A reachable GitHub URL or one pinned file is not approval.
5. Run isolated synthetic installation-free evidence tests first. If runtime code is needed, require `factory-sandbox-preflight`; do not import or execute arbitrary repository files in the catalog pipeline.
6. Record explicit PASS, FAIL or BLOCKED for each gate. Preserve the source as `proposed_only` until independent human approval and reviewed activation PR.

## Evidence
`python -m ai_factory.factory_84_registry` and `python -m ai_factory.factory_84_admission_report` summarize candidates/review gaps read-only. The current 84-entry snapshot has 168 pending license/security review checks; these do not mean 168 confirmed vulnerabilities. Human review, **no automatic merge**, zero paid usage and no changes to approved/enabled/installed flags. Do not claim bulk admission or production readiness.
