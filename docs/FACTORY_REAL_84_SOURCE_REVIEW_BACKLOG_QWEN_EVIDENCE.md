# CODEN Factory — real 84-source license and security review backlog

**Status:** DRAFT / UNAPPROVED / read-only snapshot of the checked-in Adopt-First catalog.  
**Execution:** GitHub Draft PR #165 (stacked on Draft #158 → #153 → #152).  
**Related real generated improvement:** Qwen CPU Draft PR #164, task #163.  
**Source provenance:** real model run https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45239038437; source artifact https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45239038437/artifacts/14850752775.

## What has actually been implemented

`ai_factory/factory_84_admission_report.py` reads all 84 independently validated factory candidate entries through `ai_factory.factory_84_registry.load()`. It never downloads code, installs sources, makes paid calls or changes source admission fields. It rejects an invalid source record, unauthorized approved/enabled/installed state or missing metadata. The report includes an audit row per source and priority summaries.

The existing dated **catalog** states every entry has `license_review=pending`, `security_review=pending`, `approved=false` and `enabled=false`. Consequently:

| Priority | Source/file candidate entries | Outstanding license/security checks |
|---|---:|---:|
| P0 | 26 | 52 |
| P1 | 39 | 78 |
| P2 | 19 | 38 |
| **Total** | **84** | **168** |

These are **84 catalog references from 76 distinct GitHub repositories**, not 84 installed applications. A single repository may supply more than one source entry. **168 = two review fields per catalog entry**, not 168 unique software projects or confirmed CVEs. The report does **not** override the independently pinned 11 source snapshots or the experimental 3 Spec Kit copies: those separate proofs do not automatically clear legal or security review for any catalog entry.

## How Qwen's real generated code is preserved

The GitHub artifact ZIP from the real Qwen task was actually downloaded and inspected. The outer archive SHA-256 was `74b7d9963f134ab530e18a55a671a96dc6591ac20a30e47ac13b4687b9248210`. Nested original `candidate.pyz` SHA-256: **`e011e317dc06efb6870978d40e4d17263a308c30655a565518006af23b564573`**.

The single generated function `transform(value)` was extracted as a **non-imported review candidate** under `ai_factory/review_candidates/qwen_oss_admission_transform.py` with exact source-bytes SHA-256: **`c410f3e98b7e01e9208954da558cd6b94ee22fc0fe5fa04fa3a1027db401f9cc`**. Independent static inspection found a loop and ordinary `if/elif` branches with simple comparisons/increments and no imports, function calls or network/filesystem behavior. These are syntactic observations, **not legal approval or authorization to run model-written code in production**.

The report **verifies the candidate's exact source SHA-256 but does not import, compile or execute it**. Instead, its own reviewed report logic counts the existing catalog's explicit pending fields, so the model cannot silently change admission status. The original candidate was separately executed in bubblewrap by the real-model workflow and passed 3 visible + 3 hidden cases and a synthetic stress test with 84 entries × 4 flags. The report draws from actual GitHub catalog data, not that synthetic stress fixture.

## Reproduce on this Draft branch

```bash
python -m unittest discover -s tests -p 'test_factory_84_admission_review_report.py' -v
python -m ai_factory.factory_84_admission_report
python -m ai_factory.factory_84_admission_report --json
```

GitHub Actions `AI Factory intake dry run` produces an **independent complete JSON review artifact** and asserts 84 sources, 76 repositories, 84 pending license reviews, 84 pending security reviews, 168 pending checks, `model_candidate_executed_by_report=false`, `release_authorized=false`, and `source_catalog_modified=false`.

## Remaining gates

- Independent human/code ownership review for the model's specific code artifact, license and security audits per repository, transitive dependencies/SBOM, reproducible immutably pinned builds, and explicit operator approval.
- The catalog's pending states are **the state of the checked-in snapshot**, not evidence of ongoing real-time upstream license/security checks; no CVE scan has been performed by this view.
- No production worker, live Supabase task queue or real OpenHands multi-file session is activated by this report. Source-004 OpenHands runtime still requires isolation/provenance controls from task #162.
- This branch has no automatic merge; source admission and model-result execution rights remain disabled until independently authorized.
