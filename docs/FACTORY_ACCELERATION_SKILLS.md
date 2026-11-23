# CODEN AI Factory — execution acceleration skills (six reusable Agent Skills)

**Status:** DRAFT, UNAPPROVED, no automatic installation/invocation.  
**Source:** Original CODEN repository-authored instructions, not copied from unrelated third-party code.  
**Draft PR:** #166, stacked on #165 → #158 → #153 → #152. **No changes to `main`.**

## Why this improves throughput

The current bottleneck is not the count of available open-source repositories: CODEN has **84 indexed candidate references (76 GitHub repositories)** and successful real local Qwen single-function development pilots, but no independently proven full multi-file OpenHands session and many unmerged Draft PR dependencies. These skills reduce repetitive specification, review and incident-recovery work. They do **not** substitute for model execution, safety controls or worker orchestration.

## Actual files and when to use them

| Skill (Agent Skills standard) | Trigger | Shortest useful outcome |
|---|---|---|
| `factory-batch-intake` | `intake` | Small approved scope, visible/hidden acceptance and zero-cost task plan |
| `factory-tdd-multifile` | `multifile` | RED → GREEN, independent multi-file review, bounded artifact |
| `factory-sandbox-preflight` | `sandbox` | Verify hard CPU/memory/PID/network/credential isolation; otherwise BLOCKED |
| `factory-adopt-first-gate` | `admission` | One source's pin, nested license, SBOM, security and isolated evidence |
| `factory-independent-review` | `review` | SHA-256 provenance, hidden acceptance, independent review receipt |
| `factory-pr-stack-recovery` | `recovery` | Dependency-aware Draft PR integration order and blockers |

All six are individual `.github/skills/<name>/SKILL.md` instructions with standard YAML `name` and `description`. GitHub Copilot agents that discover repository skill files can use them when enabled by their host. Existing project `AGENTS.md` points to them. The **OpenHands SDK is not yet wired to load this folder**, so no running OpenHands agent is currently known to use these skills. These files add no executable behavior to the SDK.

## Find the right skill (read-only; no API calls)

```bash
python -m unittest discover -s tests -p 'test_factory_acceleration_skills.py' -v
python -m ai_factory.factory_skill_catalog
python -m ai_factory.factory_skill_catalog --task intake --json
python -m ai_factory.factory_skill_catalog --task sandbox
python -m ai_factory.factory_skill_catalog --task recovery
```

The catalog is **six locally checked-in files only**: strict names/paths, fail-closed YAML frontmatter checks, locked task→skill mapping, no dynamic remote downloads, no auto execution, no installs, no privileges, no paid calls and no approval status changes. The selector suggests one procedure; an operator or approved agent must read and follow it.

## Which additional components speed CODEN without expanding to 100 sources?

Prefer activating independently reviewed **existing** catalog candidates; do not add duplicate registrations.

| Priority | Existing candidate | Why useful | Prerequisite |
|---|---|---|---|
| P0 | `source-061` actionlint | Catch GitHub Actions workflow syntax/expression mistakes before runners start | Pinned standalone executable, isolated test, checksum and license review |
| P0 | `source-063` uv | Faster Python dependency resolution, reproducible lock and cached installs | Review compatibility with existing `pip --require-hashes` supply-chain policy; do not replace signed hash-locked test commands blindly |
| P1 | `source-030` Copier | Reuse a golden repository template when starting a new multi-file project | Pin template and Copier version; disallow unreviewed post-generation hooks |
| P1 | `source-062` Renovate | Automate **proposals** for dependency updates | PR-only proposals, immutable pins, no auto-merge, rate limits and approval |
| Existing | `source-015` Ruff | Keep fast Python style/security checks | Already used in verified CPU model workflow; do not duplicate tool setup |

Optional **later** candidates such as `pytest-xdist` can help independent tests run in parallel, but must first be tested for runner limits, hidden-test isolation, deterministic results, dependency approval and genuine wall-clock savings; **not added or installed by this PR**. The fastest initial option may be removing unnecessary repeated network setup or using runner caching, measured against baseline rather than assumed.

## Recommended critical execution path

1. Use `factory-pr-stack-recovery` to review stack #152 → #153 → #158 → #165 → #166 and the independent real-Qwen branch #151 → #155 → #164. Do not merge either unapproved stack automatically.
2. Use `factory-sandbox-preflight` for P0 issue #162. If cgroups/caps, image/dependency SBOM and model isolation are not proven, leave real OpenHands execution BLOCKED.
3. Use `factory-batch-intake` and `factory-tdd-multifile` to scope the first real multi-file synthetic pilot using the existing #148/#149 code plus independent hidden acceptance.
4. Use `factory-independent-review` to sign off only on **actual observed** results; preserve source and hash evidence. The Qwen #164 success and source #165 report are narrow, real evidence, **not** production authorization.
5. Use `factory-adopt-first-gate` to activate only tools required for that pilot, in order of proof/need. Do not attempt a bulk 84-tool installation.

**CI success criteria:** six portable skill definitions validate and the read-only CLI resolves all six task kinds, the full relevant project tests pass on the current commit, and the skill selector never executes code or grants release/installation permission.

**Human review** before any installation, live model session, merge or deployment. No secrets, no donor/citizen data, no paid provider fallback, and no unsafe bypass to accelerate timelines.
