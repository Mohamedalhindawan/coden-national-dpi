# CODEN AI Factory — Unified 84-source Adopt-First Registry

**Status:** Draft / proposed only / **not an installation or runtime activation**.  
**Scope:** Factory-only assets from CODEN Playbook V5 R29; the 72-source v2.0 Adopt-First manifest, 12 additive R29 candidates, and dated GitHub link audit.  
**Location inside the factory:** `ai_factory/factory_84_registry.py`.  
**Source of truth remains separate and unchanged:** `configs/factory_72_adopt_first.json` and `configs/factory_r29_only_requirements.json`; dated cross-check: `configs/factory_84_source_availability_audit_2026-11-23.json`.

## What is actually integrated

- A single, on-disk, machine-readable **read-only discovery interface** in the `ai_factory` package; no duplicate catalog, code import or installer.
- **84 source/file candidate entries = 72 baseline + 12 non-duplicated R29 additions**, from **76 distinct GitHub repositories**; some entries are different example files from the same repository, not standalone programs.
- **26 P0, 39 P1, 19 P2**. Existing 16-item earlier proposal registry overlaps with this inventory and is **not** added to these totals.
- Every candidate links to its recorded `ADD-xx` factory-only requirements and relevant `W0–W4` references; all 47 R29 requirements are available from the existing `ai_factory.r29_factory_scope` source.
- 84/84 entries are unapproved, disabled, not installed by this registry; 84/84 still need independent source-version/license/security review. A dated, reachable GitHub link is **not** an admitted executable.
- The separate Draft PR #153 identifies 11 immutable critical file snapshots from six repositories, but **source snapshot pinning alone does not authorize installing or running those sources**.

## Factory commands

From the checkout root (Python 3.12; no extra packages):

```bash
python -m ai_factory.factory_84_registry
python -m ai_factory.factory_84_registry --priority P0
python -m ai_factory.factory_84_registry --wave W0
python -m ai_factory.factory_84_registry --requires ADD-13
python -m ai_factory.factory_84_registry --contains hermes
python -m ai_factory.factory_84_registry --contains omniroute --json
python -m ai_factory.factory_84_registry --contains freellmapi
python -m ai_factory.factory_84_registry --id r29-03 --json
python -m unittest discover -s tests -p 'test_factory_84_unified_registry.py' -v
python -m unittest discover -s tests -v
```

The registry has no HTTP requests, remote downloads, dynamic imports of third-party code, model calls, write operations, secrets, database mutations or program execution paths. Queries return references, not capabilities. The CI intake workflow checks the complete inventory and guardrails.

## Why registration is NOT the same as activating 84 tools

The following steps still require separate engineering and explicit operator approval for **each selected component**:

1. Verify immutable Git commit, release digest, publisher, dependency provenance and subdirectory licensing; build a per-component SBOM and check security advisories.
2. Compare with current factory capabilities to avoid redundant agent engines, gateways, queues and services. Example: Hermes, OmniRoute, FreeLLMAPI and Ollama are **alternatives or supporting components**, not a mandate to run four models/gateways simultaneously.
3. Reproduce isolated synthetic smoke tests under least privilege; record resource and network limits, expected zero-spend budget, and measurable improvement over the current engine.
4. Require independent human review, explicit scoped runtime enablement, rollback and audit evidence. Keep prod, secrets, Supabase service-role, autonomous merging and deployment disabled until specifically authorized and verified.
5. Prove the live OpenHands multi-file pilot and authenticated worker↔Supabase loop independently; the existing single-function Qwen CPU success in PR #155 is not evidence that all 84 components run.

**Do not merge Draft PR #158 automatically.** It stacks on #153 → #152 and is limited to candidate metadata discovery. No 84-package installation, provider quota circumvention, enterprise readiness or production delivery is claimed.
