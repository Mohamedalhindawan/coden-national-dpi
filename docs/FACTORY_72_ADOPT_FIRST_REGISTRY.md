# CODEN AI Factory — 72 Adopt-First GitHub source candidates (v1)

**State: indexed in a Draft PR, unapproved, not installed.**
**Baseline:** CODEN Adopt-First File & Integration Manifest v2.0, 2026-11-23.
**Source of truth:** `configs/factory_72_adopt_first.json` (72 candidate entries).
**Read-only indexer:** `ai_factory/adopt_first_registry.py`.
**TDD evidence:** `tests/test_factory_72_registry.py`.

## What 'added to the factory' means

The 72 entries are machine-readable **component/source references**. They cover both complete projects and individual example files; they are **not necessarily 72 unique upstream repositories or 72 independently runnable services**. The index can be searched from the same Python environment as the existing CODEN factory. It does **not** download source, install dependencies, call providers, submit GitHub changes, provision Supabase resources, run untrusted agents or grant merge/production credentials.

The registry is separate from the existing `configs/factory_components_proposed.json` (16 earlier research-only entries), which remains unchanged. Some of those 16 overlap with the 72: overlapping records are cross-catalog research references, **not additional installations**. The existing running proof-of-concept in `ai_factory` and Draft PRs #140, #147–#151 remain separate; this metadata index changes none of their execution behavior.

## Registry counts

| Priority | Sources | Admission |
|---|---:|---|
| P0 | 23 | Review first; not automatically installed |
| P1 | 33 | Advanced candidate trials |
| P2 | 16 | Hold until justified; includes paid-risk Hermes Self-Evolution |
| **Total** | **72** | **All disabled / unapproved / source revisions unpinned** |

The URL stored for each candidate is a GitHub repository or example file. `blob/HEAD` is an **unpinned moving reference** and must never be executed or installed as a verified dependency. Prior to importing a candidate, record an exact commit SHA or signed release and the transitively required dependencies, then independently verify provenance, license, model rights, advisories, review boundaries, security controls and permitted use.

## Query the index (no external services)

From the repository root:

```bash
python -m ai_factory.adopt_first_registry
python -m ai_factory.adopt_first_registry --priority P0
python -m ai_factory.adopt_first_registry --contains hermes
python -m ai_factory.adopt_first_registry --contains freellmapi --json
python -m ai_factory.adopt_first_registry --contains omniroute
python -m unittest discover -s tests -v
```

The indexer validates that all 72 are present, ordered, URL-scoped to GitHub, and cannot be marked installed/approved/enabled without a separately designed admission process. It rejects untrusted source domains, duplicate candidate IDs, unsupported priorities and any change to the no-auto-install / no-spend gates. The only data it reads is a repository-tracked local JSON file.

## Explicit user-requested candidates and decisions

| Candidate | Source | Trial boundary |
|---|---|---|
| Hermes Agent | https://github.com/NousResearch/hermes-agent | Secondary skills/memory agent only, synthetic tasks, no secrets or self-approval |
| Hermes Self-Evolution | https://github.com/NousResearch/hermes-agent-self-evolution | P2 HOLD — README states API costs, optimization and self-change need separated benchmarks and operator approval |
| OmniRoute | https://github.com/cheaper-inference/OmniRoute | P1 compare one authorized provider, provider terms and quota; does not grant free credits |
| FreeLLMAPI | https://github.com/tashfeenahmed/freellmapi | P1 personal experiment **not production**; original upstream, not older fork `valorisa/FreeLLMAPI` |

**Overlap decision:** Only one of OmniRoute, FreeLLMAPI or LiteLLM may be promoted to active primary gateway for an environment after an independent measured trial; none is enabled by this registry. Existing direct pinned `llama.cpp` remains a valid zero-fee route for an isolated small workload.

## Promotion / admission checklist for EACH component

1. Verify the upstream URL, release/tag and **immutable commit**; verify checksums and authentic publisher.
2. Check the root and dependency **licenses**; for model weights, separately inspect usage restrictions and data terms. A public GitHub repo is not automatically cleared for commercial use.
3. Inspect the full transitive dependency chain, package lockfile and known advisories; run reproducible isolated tests and record versions.
4. Record why existing CODEN components are insufficient. Only adopt, integrate or customize with a demonstrated advantage; no duplicate agent engines, gateways or queues just to increase tool count.
5. Run synthetic test first; enforce budget=0 in the free phase, prohibit credentials in agent prompts, use protected/separate execution credentials and maintain audit logs.
6. Require independent human approval and staged, reversible deployment before any candidate's runtime state changes. Do **not** repurpose this read-only registry as a remote installer or executable plugin loader.

## Next actual engineering gaps

- Complete the real sandboxed **OpenHands multi-file** trial with official SDK; the mocked bridge in Draft PR #149 is not evidence of a real runtime.
- Implement a **credential-minimal, authenticated worker→Supabase status bridge** separate from the private metadata schema of Draft PR #150.
- Independently review the worker lifecycle/recovery implementation of Draft PR #140.
- Retain real CPU Qwen synthetic proof from Draft PR #151, but avoid claiming its 0.5B model can produce enterprise-quality applications.
- Add an independent **license/SBOM/advisory evidence registry** keyed to immutable upstream versions, separate from a candidate's mere mention in this catalog.

**Release status:** Draft / not merged into `main` / no claim of 72 installed tools / no automatic expense.


## R29 Factory-Only Requirements — Playbook V5/R29 Addendum

The uploaded original CODEN V5/R29 blueprint was inspected for **factory-only** scope: coding-agent runtime, AI Control Plane boundaries, codebase intelligence, reusable GitHub sources, developer workspaces, QA/review, recoverable workers, finite budget, independent evidence and the CAIE improvement loop.

The **base catalog stays exactly 72 source/file candidates**. A separate linked file `configs/factory_r29_only_requirements.json` contributes:
- **47** R29 source requirements, selected from 52 ADDs (five general TAMAM/DPI/commercial/document-completion ADDs explicitly omitted);
- **12** additional, non-duplicated GitHub candidate sources: devcontainer templates/CLI, FastAPI full-stack reference, SWE-bench, in-toto, SLSA generator, Keycloak (later), Grype (optional alternative), harden-runner, Argo Rollouts (later), ZAP and Rekor (optional);
- **84 combined proposed source/file entries** (72+12), **zero new component installations**, **zero activations/approvals**;
- R29 factory-only **W0–W4**, applicable gates **G0–G6/G8**, scenarios **T01–T10/T12**, and all five reference pilots.

Inspect `docs/FACTORY_R29_ONLY_SOURCE_GAP_ANALYSIS.md` for which of the existing 72 sources meet each requirement, what remains missing, and which tools are alternatives or deferred. CLI queries:

```bash
python -m ai_factory.r29_factory_scope --wave W0
python -m ai_factory.r29_factory_scope --wave W2
python -m ai_factory.r29_factory_scope --missing-sources
```

A component appearing in the new R29 list **does not demonstrate installation, licensing approval, a verified executable, a test result, operational readiness or permission to spend.** The source Playbook and both candidate lists remain UNAPPROVED/proposed until independent verification.


## 84-source availability and development gap audit — 2026-11-23

See `docs/FACTORY_84_SOURCE_AUDIT_AND_DEVELOPMENT_GAPS_2026-11-23.md` for actual GitHub metadata/path checks, corrected gVisor and Renovate links, license caveats and prioritized factory development blockers.

The per-entry, **dated reachability-only evidence** is in `configs/factory_84_source_availability_audit_2026-11-23.json` and is protected by `tests/test_factory_84_audit_snapshot.py`. Results: 84 source/file entries, 76 distinct GitHub repos, 48 checked case-sensitive file links, 36 repo-root links, **0 newly installed/approved/enabled tools**, **0 pinned commits**, and no independent safety/license certifications. Revalidate against immutable commits before actual adoption.
