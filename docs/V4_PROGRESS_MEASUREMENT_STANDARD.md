# CODEN V4.0 — Progress Measurement Standard

**Status:** Proposed measurement policy; no percentage is authorized until baseline approval.

## Denominator
The approved full V4.0 master text is the normative source. Enumerate all independently verifiable requirements per section, identify evidence and assign a unique ID. Do not treat the 90 section headings as 90 equally sized deliverables. Scope exclusions require signed human approval.

## Eight phases
Use the V4.0 phases P1–P8. Proposed default **equal phase weight of 12.5% each** is for discussion only; human owner must approve weights and requirement decomposition before publication of percentages. Each requirement receives an effort/risk weight (default 1 unless reviewed) and phase ID. Every requirement must belong to exactly one phase for scoring, even when cross-cutting.

## Evidence-gated completion score
- 0.00: absent or unverified; planning document alone is not proof of implementation.
- 0.25: approved requirements/design and owner, with linked evidence.
- 0.50: implementation or procedure exists and was independently inspected; tests not yet complete.
- 0.75: relevant tests/review passed with reproducible evidence, but release/operational gate remains.
- 1.00: all applicable acceptance gates satisfied with approved evidence and owner.

A requirement with missing evidence cannot exceed 0.25. A runtime requirement documented but not implemented cannot exceed 0.25. A critical security or legal blocker caps its affected requirement at 0.25. An unapproved production capability cannot be scored as production-ready.

## Formula
For phase p, score_p = sum(requirement_weight × evidence_gated_score) / sum(requirement_weight).
Overall percent = 100 × sum(approved_phase_weight × score_p) / sum(approved_phase_weight).
Remaining percent = 100 − overall percent. Round to one decimal, then compute remaining from the rounded overall so they total 100.0.

## Publication gate
If approved phase weights, full requirements, owner, or evidence audit are missing, publish **Not measurable yet** instead of a numeric completion or remaining percent. A partial audited subset may be reported only as subset coverage, not as overall project completion.

## Reporting
Every run must report: overall complete %, overall remaining %, method/baseline revision, coverage of requirements audited, phase breakdown, evidence URLs, unresolved blockers, new PRs, tests actually run and next work. When unmeasurable, say so explicitly and name missing prerequisites.

## Separate activity metrics
Commits, PRs, files, test counts and sections with a tracking row are **activity/coverage metrics**, not proof of V4.0 implementation. Never equate 90/90 matrix rows with 100% completion.
