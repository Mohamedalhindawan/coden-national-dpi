# CODEN V4.0 — PR Integration and Dependency Plan

**Status:** Preliminary read-only filename inventory, not code review or CI certification. **Source:** Open PR filenames observed on 2026-11-09. [Tracking issue #55](https://github.com/Mohamedalhindawan/coden-national-dpi/issues/55).

## Proposed review order

| Wave | PRs | Scope | Required verification before merge |
|---|---|---|---|
| 0 | #29, #31, #49 | Governance templates, preflight, visual QA | Review diff and run CI on current base; avoid workflow collisions |
| 1 | #36, #37, #38, #39, #40, #41 | Enterprise specification, canonical records, lifecycle, approvals and audit | Confirm explicit dependency order, schema compatibility, test runs and security boundaries |
| 2 | #42, #43, #44, #45, #46, #47 | Portfolio, KPIs, resource, risk and dependency contracts | Rebase sequentially as needed; test complete enterprise suite |
| 3 | #26, #50 | Enterprise skills and orchestration | Compare canonical skills directory; review runtime permissions and actual tests before accepting duplicates |
| 4 | #51, #52, #53, #54, #56 | V4 tracking, DPI, enterprise registers, product engineering, progress baseline | Align register instances with schema contracts; avoid overwriting source-of-truth |

This is **review order**, not automatic merge authorization. PRs may be independent, superseded, or require splitting after detailed inspection.

## Conflict and duplication map

| Area | Existing PR | New PR | Decision required |
|---|---|---|---|
| Skills catalog and runtime | #26: `skills/`, registry, orchestration runtime and tests | #50: `ai-enterprise/skills/` guidance | Select canonical catalog, keep runtime separate from skill docs, deduplicate names and preserve security tests |
| Risk | #46: `schemas/enterprise/risk.schema.json` and tests | #51: `enterprise/risk/risk-register.yaml` | Make YAML instance conform to canonical JSON schema; add validation |
| KPIs | #43–#44: KPI and measurement schemas and tests | #53: `enterprise/performance/kpi-registry.yaml` | Treat schemas as contracts, register as instance; map fields and validate |
| Enterprise management | #36–#47: models, workflows, approval and audit | #51, #53: roadmap, evidence, governance | Establish owner and system of record, avoid parallel authoritative contracts |
| GitHub governance | #29: issue and PR templates | #51, #53: policies | Reuse templates, don't create duplicates |
| Visual quality | #49: SVG QA workflow and script | Other PRs: architectural documents | Ensure visual QA actually runs for board changes |
| DPI | #52: unpopulated 80-domain and DPG registers | Existing reference documentation | Source actual catalogs; do not fabricate asset counts or deployment |
| Progress | #51: 90-section tracking rows | #56: evidence-gated progress standard | Link exact requirements to phase IDs and evidence before publishing completion % |

## Safe merge protocol
1. Verify branch base SHA, changed files, CI status, reviews and dependencies.
2. Compare full diffs, not filenames only; perform secrets and data-sensitivity review.
3. For schema changes, add fixtures, negative tests and backward-compatibility checks.
4. Validate PRs against the **full approved V4.0 text**; currently not established as main source of truth.
5. Require authorized human approval before merge or policy changes.
6. Record merge SHA, test run URL and reviewer in evidence register.

## Current blockers
- Full authoritative V4.0 text is not on `main` as verified during repository inspection.
- Branch protection and required review checks need authorized configuration and evidence.
- Open PR inventory alone cannot establish which tests pass or which PR is safe to merge.

## Progress measurement linkage
Until the requirements and phase weights in [PR #56](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/56) are reviewed and approved, overall completion and remaining percentages are **not measurable yet**. The 90 rows in [PR #51](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/51) are tracking coverage, not verified implementation.
