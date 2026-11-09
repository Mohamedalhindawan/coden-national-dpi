# CODEN V4.0 — Issue #55 reconciliation decision register

Status: **provisional / human review required**. Date: 2026-11-09.
Scope: coordination only. This file does **not** replace the approved full V4.0 text, assert implementation completeness, or authorize merges, releases, spending, or permission changes.

## Evidence and candidate source-of-truth decisions

| Area | Existing work to reconcile | Proposed contract boundary (not approved) | Human acceptance gate |
| --- | --- | --- | --- |
| Skills | [#26](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/26) `skills/` runtime/library; [#50](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/50) `ai-enterprise/skills/` | Prefer one canonical skill ID catalog, with compatibility aliases; preserve #26 runtime/tests until evaluated | Diff both trees, compare IDs/permissions/tests, choose path and migration plan |
| KPI | [#43](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/43), [#44](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/44) JSON schema/provenance; [#53](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/53) YAML template | JSON schema defines validation; YAML is a versioned instance only | Test sample YAML against schema and provenance requirements |
| Risk | [#46](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/46) risk contract; [#51](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/51) risk register | Contract and instance must be separate, validated artifacts | Add positive/negative compatibility tests before merge |
| Enterprise lifecycle | [#37–#47](https://github.com/Mohamedalhindawan/coden-national-dpi/pulls) stacked management work | Preserve dependency ordering; do not assume independent mergeability | Inspect each PR's base/head SHA, CI, conflicts and review status |
| Governance templates | [#29](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/29) | Reuse existing PR/ADR templates; avoid duplicates | Review actual diff before selecting |
| Visual QA | [#49](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/49) | Retain checks only if independently reproducible | Run actual workflow/tests and record run URL |
| DPI and TAMAM | [#52](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/52), [#54](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/54) | Registry records are not proof of deployable integrations | Verify license, data protection, test evidence and human approval |
| Progress | [#51](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/51), [#56](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/56), [#58–#65](https://github.com/Mohamedalhindawan/coden-national-dpi/pulls) | Require approved full V4 requirements matrix, eight stage weights and evidence before publishing percentages | Reject unsupported numeric progress |

## Review queue (no merge authorization)

1. Verify current `main` SHA and exact approved V4.0 master-document hash; do not replace it with this register.
2. Capture each PR number, state, base/head SHA, CI run URLs, reviewer decision and changed files for #26, #29, #37–#54 and #56–#69.
3. Inspect dependency chains using [#66–#69](https://github.com/Mohamedalhindawan/coden-national-dpi/pulls) tools only after their tests are independently verified.
4. Reconcile overlapping skill IDs, schema-versus-instance ownership, and duplicate governance templates.
5. Define a complete requirement-by-stage baseline and explicit weighting methodology before claiming percent complete.
6. Require human sign-off for canonical ownership, protected-branch changes, merges, release and any citizen-data processing.

## Evidence status and blockers

This register derives its **candidate overlaps** from [coordination issue #55](https://github.com/Mohamedalhindawan/coden-national-dpi/issues/55) and the repository's visible PR inventory on 2026-11-09. It does not independently certify the contents or CI outcomes of those PRs. All decisions remain **proposed** until diffs, CI, full V4 text, and reviewers are recorded.

**Next highest-value action:** produce a machine-checkable PR inventory with base/head SHAs and CI evidence, then implement schema/instance compatibility tests on an isolated branch. No protected branch should be changed as part of this work.
