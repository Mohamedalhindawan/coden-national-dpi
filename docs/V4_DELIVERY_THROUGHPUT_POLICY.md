# CODEN V4 — Delivery Throughput & Consolidation Policy (proposal)

**Status:** Proposed for human review; NOT a replacement for the authoritative full V4 playbook.  
**Scope:** Development process only; no production or government authority.  
**Evidence baseline:** `main` at `921b2b848366a2a7a368660d5460ca5e6d712ba3`; issue [#55](https://github.com/Mohamedalhindawan/coden-national-dpi/issues/55); [#114](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/114) has a successful CI run but remains open.

## Bottleneck and corrective action

Many small draft PRs and stacked PR bases delay integration and make progress look larger than verified functionality. Stop creating PRs whose only deliverable is another inventory, drift checker, or progress report, unless a concrete CI defect makes that unavoidable. Prioritize one independently testable vertical feature per delivery batch.

## Immediate priority order (no autonomous merge)

1. **P0 — Reconcile issue #55.** Compare #26 vs #50 skills, #43–44 vs #53 KPI contracts/registry, #46 vs #51 risk contracts/registry, and the #37–47 branch chain. Select canonical paths/contracts **only after human review**. Avoid rewriting tested implementations.
2. **P1 — Engineering factory vertical slice.** From a new branch based on current `main`, implement one end-to-end synthetic-only workflow: intake → validated task specification → sandboxed execution plan → independent verification → human approval gate. A plan is not autonomous execution; no tool or production privileges are implied.
3. **P2 — TAMAM vertical slice.** Deliver one user-facing Arabic RTL synthetic-data journey with acceptance tests, not an unconnected catalog of proposed services.
4. **P3 — DPI adapter spike.** Contract-test a mocked integration with no live identity, payment, or citizen data.

## Batch definition of done

Each implementation PR must contain: (a) a user-visible or operator-visible capability, (b) explicit acceptance criteria, (c) tests actually run with commands and results, (d) security/privacy boundary, (e) links to applicable V4 requirements **only when full authoritative text is verified**, and (f) rollback or revert instructions. Draft status and human review are mandatory until authorized.

## Anti-fragmentation rules

- Default to one PR per complete vertical slice, not one PR per test or documentation amendment.
- Prefer `main` as the PR base; if blocked by an unmerged dependency, document the exact dependency and do not represent the stacked PR as independently mergeable.
- Before writing new code, search open PRs and existing files for the same functionality.
- Failures must be reproduced with a failing test before fixes; rerun the relevant tests and full available suite afterward.
- No automatic merging, production deployment, paid services, privilege expansion, or real citizen data.

## Throughput metrics (weekly; never substitute for V4 completion %)

| Metric | Numerator / denominator | Evidence |
|---|---|---|
| Vertical-slice completion | Accepted, tested user workflows / planned workflows | PR diff, test logs, human acceptance |
| CI pass rate | Successful required CI runs / completed required CI runs | GitHub Actions |
| PR cycle time | Time from PR open to human decision | GitHub timestamps |
| Unresolved dependencies | Count of blocked PR dependency edges | GitHub PR base/head graph |
| Duplicate effort | Confirmed overlapping deliverables / reviewed deliverables | Issue #55 reconciliation |

## V4 full-plan percentage gate

Do not report an overall percentage until the exact approved V4 source, its eight phases, requirement IDs, weights, acceptance criteria, and independently verified evidence are available. Then: completion = 100 × sum(weights of accepted requirements) / sum(weights of all requirements); remaining = 100 − completion. Unverified and draft work receives zero accepted weight. Publish per-domain rates only from the same weighted matrix. Until then: **غير قابل للقياس بعد**.

## Next human decision

Review issue #55 and choose canonical skills/schema owners; authorize a single P1 vertical-slice scope. This policy does not approve any pending PR for merge.
