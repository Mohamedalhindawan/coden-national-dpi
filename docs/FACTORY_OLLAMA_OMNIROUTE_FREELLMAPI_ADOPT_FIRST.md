# CODEN AI Factory — Adopt-First: Ollama + Gateway Evaluation (2026-11-21)

**State:** Unapproved evaluation / no deployed services. **Scope:** CODEN AI Factory only. This document and the accompanying code neither install upstream projects nor enable model execution, spend, automatic fallback, background agents or production deployment.

## Goal and reuse boundary

- **Use upstream Ollama** as a local model server. CODEN does **not** reimplement the model runtime. Readiness is checked using Ollama's existing `GET /api/tags`; the factory already has a separate pinned `llama.cpp` pilot.
- **Trial one coding-agent runtime** such as OpenHands Software Agent SDK in a sandbox later; do not write a second general-purpose coding harness. Keep existing `project.py` synthetic task baseline for comparison.
- **Compare OmniRoute, FreeLLMAPI, LiteLLM and Bifrost** as alternatives for one primary model gateway. Do not automatically layer multiple gateways or assume their marketing aggregate free-tier numbers are available to CODEN.
- **Reuse CODEN's own governance pieces**: `checkpoint.py`, `durable_queue.py`, `reconcile.py`, `recovery_policy.py`, `runtime_contract.py`, `artifact_evidence.py` and independent PR review. Existing `router_preflight.py` covers a distinct local Codex **Responses API** configuration; it is not proof that all Ollama routes support that API.

## Upstream evidence snapshot (not installation pins)

| Candidate | Verified public upstream ref (2026-11-21) | Top-level LICENSE | Evaluation role | Current CODEN state |
|---|---|---|---|---|
| [Ollama](https://github.com/ollama/ollama) | `cecac8bf1bd30ba928ee7cfe53b953f9b25642ae` | MIT | Local inference and model discovery | Loopback discovery contract tested; runtime **not installed** |
| [OmniRoute](https://github.com/cheaper-inference/OmniRoute) | branch `release/v3.8.55` at `b748429cf5b3aeb142a708fd3e8751b6918b9dc8` | MIT | Candidate gateway A | Research-only, disabled |
| [FreeLLMAPI](https://github.com/tashfeenahmed/freellmapi) | `7ad9097fd9d83bc3e1af0f925ea813a913b18dde` | MIT | Candidate gateway B | Research-only, disabled |
| [OpenHands SDK](https://github.com/OpenHands/software-agent-sdk) | `885242b563b1d2695d6c7b3d4bfe642f1c8838a3` | MIT | Candidate coding-agent SDK | Research-only, disabled |

These are **source revision snapshots**, not audited release tags or pinned container digests. Top-level licenses alone do not clear transitive dependencies, model weights, hosted provider terms or distribution obligations. Before installation: select release/tag + immutable artifact digest, review dependencies and vulnerabilities, configure network/secret/PII rules, and obtain owner approval.

## Existing native Ollama API: read-only opt-in check

`ai_factory/ollama_probe.py` is a minimal admission check for the upstream server, **not an adapter that generates code**. A GET to Ollama's native `/api/tags` reads only the installed model names. It never pulls a model or posts inference prompts.

```bash
# Static validation, no network:
python -m ai_factory.ollama_probe --model 'qwen2.5-coder:1.5b'

# ONLY if Ollama is already running locally, you explicitly want to check it,
# and you control the host + selected model:
python -m ai_factory.ollama_probe --model 'qwen2.5-coder:1.5b' --probe-loopback

# Any nondefault loopback port must use numeric 127.0.0.1:
python -m ai_factory.ollama_probe --endpoint 'http://127.0.0.1:11435' \
  --model 'qwen2.5-coder:1.5b' --probe-loopback
```

The model string is only illustrative; no installation or download is implied. The probe connects directly using `http.client`, with a 2-second timeout, 64 KiB response limit, strict JSON validation, no redirect or credential handling, and no remote host or DNS alias. It always returns `execution_authorized=false` and `provider_approved=false`. Even `probe_status=available` means **a model name appears in a local API listing**, not that coding quality, model licensing, isolation, provenance or tool-calling integration has passed.

Tests include one live **loopback fake-server fixture**, various invalid URLs, malformed JSON, duplicate fields, HTTP failures, oversized results and default no-network mode. CI **does not install or run Ollama** and sends no prompt.

## Gateway options, not a combined quota

| Capability | Ollama | OmniRoute | FreeLLMAPI |
|---|---|---|---|
| Primary role | Local inference server | OpenAI-style multiprovider gateway | OpenAI-compatible multiprovider free-tier gateway |
| Needs own upstream provider accounts for hosted models? | Not for local execution | Usually yes; eligible providers and terms control limits | Usually yes; eligible providers and terms control limits |
| Local model route | Native Ollama API; optional compatibility endpoints | Must verify actual local-route configuration | Describes custom OpenAI-compatible local providers; must verify |
| Operational risks | Hardware sizing, model weights, exposed port | Complex routing, dependency supply chain and provider ToS | External catalog feed/update policy, provider ToS and dynamic free-tier changes |
| CODEN proposed decision | **First local proof** | Trial A after local proof | Trial B on identical isolated fixture |
| CODEN current approval | Not installed/approved | Not installed/approved | Not installed/approved |

Upstream README claims about large aggregated monthly free token budgets are **not** guaranteed per CODEN account, may combine shared pools, change rapidly or require eligibility, and may include options that must not be used under provider terms. Neither gateway bypasses a provider's real limits or grants unlimited access. Do not use consumer cookies, session transfer or unapproved account rotation.

## Strict next acceptance gates

1. On an **operator-controlled** Linux host, obtain explicit permission to install a pinned Ollama version and model whose weight license and size are checked. Keep binding on localhost; do not publish model API endpoints.
2. Run the read-only model discovery probe and capture system/model capacity + pinned versions. No real data.
3. In a sandbox, use an upstream coding-agent SDK with a small synthetic **multi-file** project; verify hidden acceptance tests and actual artifacts, not only a model name.
4. Evaluate OmniRoute and FreeLLMAPI **individually**, on identical synthetic tasks and sanctioned provider keys. Record pass rate, latency, cost, rate-limit behavior, model capability coverage, trace redaction and failure recovery. Select one gateway only after license/security review and explicit approval.
5. Integrate the selected runtime into existing task policy / checkpoints / independent artifact verifier. Quarantine uncertain work; no unattended release, merge or replay of non-idempotent operations.
6. After independent code/security review, consider a service deployment under stronger container/cgroup cancellation, backup and authorized resource budgets. This PR alone is **not** 24/7 execution or a Codex session resumer.

**Status vocabulary:** discovery contract `TESTED`; local Ollama process `NOT VERIFIED`; OmniRoute/FreeLLMAPI `RESEARCH`; OpenHands executable agent integration `NOT IMPLEMENTED`; factory production `BLOCKED`.
