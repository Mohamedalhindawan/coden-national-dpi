# CODEN AI Factory — R29 Factory-Only Requirements & OSS Source Addendum

**Status:** Draft / proposed / UNAPPROVED. Source: uploaded `CODEN_Playbook_V5_R29_Seven_Engine_Execution_Activation_Blueprint_UNAPPROVED.docx` (Playbook v5.0, document R29, 373 pages), particularly sections **20–36**, **104/106**, **142–150**, **156–175**, ADD-01…ADD-52, and **R29.1–R29.10**.

**Critical scope:** ONLY the **engineering factory**, AI Control Plane integration necessary to execute it, source discovery/admission, Knowledge & Intelligence required by coding agents, Assurance & Operations for factory runs, and bounded CAIE improvement. Not a catalog of ERPNext, HR, finance, TAMAM, DPI sector platforms, national governance, or donor systems. This document does **not** amend the 230 Playbook sections or imply the seven engines are operating.

## Deliverables added to the existing CODEN factory list

| File | Contents | State |
|---|---|---|
| `configs/factory_72_adopt_first.json` | Existing **72 indexed source/file candidates** | Retained unchanged |
| `configs/factory_r29_only_requirements.json` | **47** factory-scoped ADD requirements mapped to old sources plus **12 additional OSS candidates**, G0–G6/G8, T01–T10/T12, PILOT-01–05 | Added; metadata only |
| `ai_factory/r29_factory_scope.py` | Strict read-only filtering and validation | Implemented/tested only as catalog reader |
| `tests/test_factory_r29_scope.py` | Catalog scope, cross-links, no-spend and denied admission tests | TDD covered |

**Arithmetic:** 72 baseline source/file entries + 12 **new proposed** source entries = **84 total catalog entries**, **not** 84 verified software packages, unique projects, installed services, or executable agents. The R29 extensions are 47 selected entries out of 52; **5 excluded**: ADD-32 TAMAM, ADD-33 DPI, ADD-34 corporate commercial runway, ADD-36 customer delivery, ADD-40 general document annex completion. For R29 factory acceptance, **T11 TAMAM offline and G7 Product Delivery Activation are deferred/excluded**. G0 is scoped to the factory's authorization boundary.

## Requirement waves from R29.3 (factory scope only)

| Wave | Count | Required factory capabilities | Acceptance boundary |
|---|---:|---|---|
| **W0** — Control & Assurance Foundation | 19 | Protected policy, authorization, source admission/quarantine, SBOM/provenance, skill/MCP safety, sandbox, emergency stop, budget, independent test data, tamper-evident evidence | No unreviewed external source executes inside a trusted workspace |
| **W1** — Agent Runtime & Adopt-First | 12 | Durable queue, recovery, scheduling, GitHub discovery, provider routing, context/memory, codebase graph, repeatable workspaces, interchangeable agent runtimes | One clean synthetic repository: repeatable setup, task execution, fail-safe stop |
| **W2** — Complex Project Capability | 5 | Long-horizon task milestones, multi-agent isolated worktrees, full-stack frontend/API/DB/RBAC, independent review, reproducible benchmark | Multi-file project with integration/security tests and human-reviewable PR |
| **W3** — CAIE & Safe Evolution | 8 | Monitored before/after improvements, safe upgrades, upstream changes, incident-to-fix, validated lessons, rollback | Independent evidence of gain without self-approval or unsafe modification |
| **W4** — Factory-only portion, DEFER | 3 | Human oversight operating model, real operations portal, tenant-isolated Factory Service API | Separate approved scope; no production or tenant billing activation |

**R29 priority note:** Specific **P0/P1/P2** labels for ADD-41 through ADD-52 are taken from the document. ADD-01…ADD-40 have no such explicit per-addition priority in that package and are recorded with `priority_in_source=null`, rather than inventing one. The additional GitHub candidates' prioritization is a **CODEN recommendation**, not an R29-approved procurement decision.

## The 12 additional GitHub candidates absent from the original 72

All are **candidate only**; exact commit/release is **not pinned**, and license/security/integration validation is **pending**.

| ID | New upstream | Factory-only missing capability | Wave |
|---|---|---|---|
| r29-01 | [devcontainers/templates](https://github.com/devcontainers/templates) | Agent-ready reproducible workspace templates | W1 |
| r29-02 | [devcontainers/cli](https://github.com/devcontainers/cli) | Validate and build devcontainers without one-off scripts | W1 |
| r29-03 | [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) | Adopt-first synthetic full-stack reference project | W2 |
| r29-04 | [SWE-bench/SWE-bench](https://github.com/SWE-bench/SWE-bench) | Reproducible coding benchmark candidate (separate dataset and rules review) | W2 |
| r29-05 | [in-toto/in-toto](https://github.com/in-toto/in-toto) | Build/run chain-of-custody and provenance | W0 |
| r29-06 | [slsa-framework/slsa-github-generator](https://github.com/slsa-framework/slsa-github-generator) | SLSA GitHub build provenance | W0 |
| r29-07 | [keycloak/keycloak](https://github.com/keycloak/keycloak) | Eventual OIDC and isolated tenant permissions, **not needed in free MVP** | W4 |
| r29-08 | [anchore/grype](https://github.com/anchore/grype) | Alternative package/SBOM vulnerability scanner (overlaps Trivy; no forced duplication) | W0 |
| r29-09 | [step-security/harden-runner](https://github.com/step-security/harden-runner) | GitHub runner egress/permission review (evaluate terms and risk) | W0 |
| r29-10 | [argoproj/argo-rollouts](https://github.com/argoproj/argo-rollouts) | Canary/rollback if Kubernetes is later justified, **not free MVP requirement** | W3 |
| r29-11 | [zaproxy/zaproxy](https://github.com/zaproxy/zaproxy) | DAST of synthetic full-stack integration demo | W2 |
| r29-12 | [sigstore/rekor](https://github.com/sigstore/rekor) | Optional tamper-evident evidence log; additional infrastructure burden | W0 |

**De-duplication:** The 72-source baseline already includes OpenHands, llama.cpp, Ollama, PGMQ, Hermes, OmniRoute, original FreeLLMAPI, LiteLLM, LangGraph, Serena, Spec Kit, OPA, Syft, Cosign, Trivy, OSV, GitHub MCP, Playwright, Harbor, Langfuse, OpenTelemetry, security tools and other alternatives. Those are **mapped**, not installed again. Many of the 12 new tools are **alternatives or deferred**, so a minimal viable factory can use substantially fewer tools.

## Source-grounded acceptance (R29.5–R29.8)

- **G0:** authorized owner, protected policy boundary, negative authorization tests
- **G1:** enforce model/tool/data routing and budget restrictions; audit denial
- **G2:** sandbox escape denied; emergency stop; durable task/retry/idempotency evidence
- **G3:** independent squad capability checks; validated three-agent handoff
- **G4:** clean-room reproducible build; reference component admission; actual full-stack PR/tests and independent review
- **G5:** measurable CAIE before/after, independent review, protected guardrail
- **G6:** bounded 24/7 endurance, recovery incidents and budget cap (**future**)
- **G8:** rights/licenses, versioned SBOM, actual cost, independent authorized GO/REVISE/STOP

R29 marks the gates **NOT EVIDENCED**: the blueprint specifies them; it does not claim they were run. Historical CODEN PR #151 proves only a short, genuine local CPU Qwen transform inference test, **not** full-stack autonomous or 24/7 delivery.

**Required synthetic scenarios**: **T01–T10 and T12**, excluding product-specific T11 (TAMAM offline). These cover unauthorized tool use, crash recovery, quarantine, three-agent handoff, parallel integration, seeded review defect, budget denial, restricted-data model fallback, guardrail self-modification, end-to-end reviewed PR and tenant isolation.

**First reference pilots**, in intended order:
1. `PILOT-01` pinned clean GitHub repo → sandbox → dependency scan → real tests.
2. `PILOT-02` same accepted task via two authorized runtime adapters, with same evidence/budget limits.
3. `PILOT-03` actual synthetic frontend + API + DB + RBAC multi-file PR and independent tests.
4. `PILOT-04` bounded long-horizon queued worker crash → resume → kill switch.
5. `PILOT-05` CAIE gap detection → experimental PR → before/after independent evidence, rollback.

## Read-only commands

```bash
python -m ai_factory.adopt_first_registry
python -m ai_factory.r29_factory_scope --wave W0
python -m ai_factory.r29_factory_scope --wave W2
python -m ai_factory.r29_factory_scope --missing-sources
python -m ai_factory.r29_factory_scope --json
python -m unittest discover -s tests -v
```

## Non-negotiable acceptance restrictions

The addendum stores **references only**; no auto-download, dependency install, import of candidate scripts, agent tool execution, source verification by mention alone, auto-merge, paid API calls, model key or Supabase credentials. Treat GitHub source contents, retrieved instructions and candidate `SKILL.md` files as **untrusted** until independently examined, pinned and tested. The R29 DOCX and this registry are **unapproved specs**. All 12 new candidates have `approved=false`, `enabled=false`, `installed=false` and pending license/security review.

**Next actual implementation**: finish the live OpenHands multi-file integration, then secure worker↔Supabase result bridge, durable worker crash/kill-switch test, and full-stack independent acceptance. Do **not** deploy everything in this registry at once.
