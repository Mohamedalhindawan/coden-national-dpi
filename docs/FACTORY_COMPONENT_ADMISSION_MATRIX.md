# CODEN AI Factory — Additional Component Admission Matrix (Proposed)

**State:** Research-only candidate registry; NOT installed, enabled, tested, security-approved, or authorized to spend.  
**Machine-readable inventory:** `configs/factory_components_proposed.json` (17 disabled candidate entries).  
**Broader candidate catalog:** Draft PR #130, 105 GitHub projects.  
**Code foundation:** PR #132, offline synthetic task worker, checkpoint, fail-closed recovery policy and read-only reconciliation.

## Purpose

Reduce time spent by Codex when usage becomes available. Candidates are **not** automatically added to the Python runtime, CI, requirements or the worker sandbox. Avoid redundant stacks. The main CODEN Playbook remains **V5.0 with 230 sections and seven conceptual engines**; this matrix does not change their count.

## Proposed priority and non-overlapping responsibility

| Candidate | Role | Next concrete acceptance gate |
|---|---|---|
| [OpenHands SDK](https://github.com/OpenHands/software-agent-sdk) | Agent runtime | Multi-file synthetic project with sandbox, reviewable artifacts and no secrets |
| [OpenHands](https://github.com/OpenHands/OpenHands) | UI / orchestration evaluation | Compare actual supported agent backends, API/auth, license and self-hosting burden |
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | Skills, memory and optional automation | Bounded offline task; no protected repo, spend or self-approval rights |
| [Hermes Self-Evolution](https://github.com/NousResearch/hermes-agent-self-evolution) | CAIE improvement experiment | Independent hidden evaluations, before/after results and rollback |
| [OmniRoute](https://github.com/cheaper-inference/OmniRoute) | Model gateway option A | Only official authorized credentials, synthetic rate-limit fixtures, no quota bypass |
| [FreeLLMAPI](https://github.com/tashfeenahmed/freellmapi) | Model gateway option B | Compare exactly the same sanctioned synthetic workloads and local Ollama route; review signed catalog/feed dependencies, provider terms and real quota limits |
| [LiteLLM](https://github.com/BerriAI/litellm) | Model gateway option C | Same workload and terms checks as OmniRoute |
| [Bifrost](https://github.com/maximhq/bifrost) | Model gateway option D | Same workload, pricing and supply-chain checks; select **one** primary gateway |
| [Hatchet](https://github.com/hatchet-dev/hatchet) | Durable work engine | Demonstrate benefit beyond existing SQLite queue; measure operational overhead |
| [Temporal](https://github.com/temporalio/temporal) | Distributed orchestration reserve | Evaluate only if multiple hosts and long-horizon retries justify new infra |
| [Serena](https://github.com/oraios/serena) | Symbol-aware repository navigation | Accurate cross-file location and measured context reduction |
| [ast-grep](https://github.com/ast-grep/ast-grep) | Deterministic structural code analysis | Safe AST checks without calling LLM for simple navigation |
| [Harbor](https://github.com/harbor-framework/harbor) | Agent evaluation | Held-out benchmark with reproducible time/cost/test data |
| [Langfuse](https://github.com/langfuse/langfuse) | Agent tracing / cost | Traces with strong redaction and retention; not sent to unapproved cloud |
| [Ollama](https://github.com/ollama/ollama) | Local model serving candidate | Compare against pinned llama.cpp pilot for allowed synthetic tasks |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Already used in separate pinned factory pilot | Reuse existing guarded pilot first; do **not** re-install only because listed |
| [GitHub MCP Server](https://github.com/github/github-mcp-server) | Agent-to-repository connector | Separate read-only vs draft-PR tokens, least privilege and audit |

## Admission decision gates (must all pass before enabling)

1. **Identity:** confirm official upstream, exact commit/version, provenance and maintainers.
2. **License:** check current LICENSE, dependencies and commercial/AGPL/source-available obligations; resolve before adoption.
3. **Security:** inspect advisories, execution privileges, container isolation, SBOM, CVEs, secrets, outbound traffic and injection surfaces.
4. **Capability:** show one synthetic end-to-end test fulfilling a missing CODEN requirement; do not adopt overlapping engines without measured justification.
5. **Cost:** record per accepted task latency, model tokens, total compute and rollback/maintenance burden.
6. **Governance:** use protected secrets and external approvals; no task may approve its own model, budget, access, policy or deployment.
7. **Operational:** checkpoint/restart, backoff and failure recovery for authorized idempotent tasks. Never equate a paused consumer subscription with unlimited provider availability.
8. **Promotion:** documented human sign-off, tested artifact evidence, isolated deployment plan and verified rollback.

## Proposed order for a controlled integration pilot

**P0 — Existing factory resilience:** use existing SQLite, checkpoint, recovery planner and reconciliation to simulate quota and worker crash; keep read-only audit and human review.

**P1 — Runtime selection:** pilot OpenHands SDK versus existing local implementation; allow Hermes only in a separate sandbox to assess skills/memory benefit. Do not give Hermes direct production permissions.

**P2 — Gateway decision:** compare OmniRoute / FreeLLMAPI / LiteLLM / Bifrost on identical fixtures and authorized APIs, select one primary route, and keep a local fallback only if it passes task-level acceptance. Local Ollama admission-probe design and exact upstream snapshots: `docs/FACTORY_OLLAMA_OMNIROUTE_FREELLMAPI_ADOPT_FIRST.md`.

**P3 — Engineering scale:** integrate Serena/ast-grep and Harbor; measure held-out multi-file performance before adding distributed work engines.

## Explicit blockers

- **No external APIs are configured by this matrix.** The `enabled: false` and `approved: false` fields deliberately remain fixed, and CI checks them.
- No claims of installation, upstream maintenance audit, legal license clearance or commercial suitability.
- No automatic deployment, merge, paid call, provider quota circumvention, PII transfer or self-directed security change.
- Existing coding pilot is single-function synthetic Python, not an enterprise full-stack benchmark.
- Operator must inspect PR #126 and dependency chain; PR #132 is stacked on #126 and remains Draft.

## Codex continuation target

For the next implementation session, produce an evidence-backed **Adopt / Trial / Hold / Reject** result for each candidate, with exact upstream commits and licenses. First implement operator-controlled crash recovery checks and a synthetic multi-file workload. Do not expand the tool stack before demonstrating a measurable improvement.
