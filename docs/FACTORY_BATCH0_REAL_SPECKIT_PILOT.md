# CODEN Factory Batch 0 — Real immutable Spec Kit source assets (review-only)

**Status:** Draft, UNAPPROVED, non-production. Implements an isolated first-stage source-use pilot for #159; stacked on Draft PR #158 (→ #153 → #152). No source becomes automatically authorized merely because its files are present in this branch.

## Actual upstream reused — not reconstructed

Upstream: https://github.com/github/spec-kit
Pinned exact commit: `fa7c88fb1c56034a10c4553c9d5527d1a62fc919`
Licensing: upstream `LICENSE` at that commit is MIT (GitHub, Inc.). The complete original LICENSE is stored and copied together with the three original Markdown templates. Follow-up independent legal/licensing decision still required before production or redistribution.

| Catalog ID | Original source file | Git blob SHA-1 | CODEN review output |
|---|---|---|---|
| source-011 | `templates/spec-template.md` | `ceb28776215a098e977650ac090c785dcbf53651` | `spec.md` |
| source-012 | `templates/plan-template.md` | `36f2eab16880bac670fe43cbe7ef2b9bc8c3aa2f` | `plan.md` |
| source-013 | `templates/tasks-template.md` | `7fff087cc5a3c51a889d865fd9126607a032d233` | `tasks.md` |
| Attribution | `LICENSE` | `28a50fa22639e32febe14e4ffc7a732b0ba8c90a` | `LICENSE` |

**Important:** Git blob IDs are Git SHA-1 object references; not SHA-256 package distribution seals. The pilot checks each original file against the immutable blob and records SHA-256 of the exact resulting bytes. It never runs template instructions or downloads remote content at runtime.

## How to run (on a checkout of this Draft PR, Python 3.12)

```bash
python -m unittest discover -s tests -p 'test_factory_spec_kit_pilot.py' -v
python -m ai_factory.spec_kit_pilot --output /tmp/coden-speckit-review
cat /tmp/coden-speckit-review/evidence.json
```

The destination **must be a fresh absolute directory** under an existing, non-symlink parent. The command fails closed if a source differs from its pinned blob, if the MIT attribution is missing, if an input is symlinked, or if the output already exists. It creates only original Markdown, `LICENSE` and JSON evidence, marks `release_authorized=false`, and makes no model, database, external network, paid provider or deployment calls.

The short-lived GitHub Actions `coden-speckit-immutable-source-review` artifact contains the five review-only files from the actual test run. This offers a reproducible, tangible Adopt-First use, not an autonomous engineering runtime.

## Remaining capability gates

- No source entry in the original 84-source read-only registry is marked approved/enabled/installed as a result of this pilot.
- The three templates are **unfilled** original upstream documents. User/business requirements, architecture, security, testing, citations and human approval must be supplied separately.
- License review, security approval, governance approval and dependency analysis for other components are still pending. Static, byte-identical markdown reuse does not prove an OpenHands agent works or a full-stack application can be generated.
- Next: a real, isolated **multi-file OpenHands SDK** trial, independently reviewing its pinned SDK/workspace, model and sandbox; then a zero-cost worker ↔ Supabase status bridge with separate controls. Do not bulk-install all 84.

**Success means:** original 3 upstream files verified, safely staged, complete MIT notice preserved, independent offline unit tests pass, immutable provenance and no-release receipt retained. Production adoption remains unapproved.
