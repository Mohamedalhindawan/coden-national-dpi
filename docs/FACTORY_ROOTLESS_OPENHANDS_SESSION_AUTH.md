# CODEN AI Factory v1.0 — Rootless OpenHands authenticated session API proof

**Status:** Draft PR #182, stacked on verified rootless Qwen integration #181; human review required. **Issue #162 stays OPEN.** Founder-approved v1.0 remains frozen.

## Why this gate matters before a real SDK Conversation

The previous checkpoint #181 proved a **real, signed, repaired OpenHands agent-server** runs under Podman Rootless and reaches the **actual hash-pinned Qwen2.5-Coder 0.5B llama.cpp inference server** on an isolated private network, with CPU/RAM/PIDs, read-only roots and two tested external egress denials. It did **not** authenticate the API clients. Upstream OpenHands source commit `077f3fad6d31cd852be5c87176e0a93c3b446126` confirms `OH_SESSION_API_KEYS_0` and `OH_SECRET_KEY` are native configuration variables, while `/api/conversations/count` is protected by `X-Session-API-Key` header authentication.

This PR tests the official mechanism on the **real source-built server**:

1. CI verifies the existing CODEN-signed OpenHands executable SHA256 `5ad5fa2bb86256b510df3bfbbd9653fbc60a243ea744a579d3ca4c6fd9e91cf3` against the signed attestation and previous archived high/critical security scan. It verifies exact GGUF and llama.cpp runtime hashes again before offline image building.
2. An independent **Rootless Podman** runtime creates a unique `--internal` bridge with exactly two nonroot, capability-free, resource-limited containers. The OpenHands server listens on its internal interface `openhands:8002` rather than its previous loopback-only address, but there are **no published host ports**.
3. CI generates two unpredictable per-run synthetic secrets with `openssl rand -hex`, masks them from GitHub logs using `::add-mask::`, and passes them to the server as `OH_SESSION_API_KEYS_0` and `OH_SECRET_KEY`. These are never real user secrets and never appear in the review artifact. The correct key is delivered solely to an ephemeral controlled test subprocess in the second container; the Qwen model process itself does not inherit it. CI checks for any *other* secret-like keys in OpenHands and Qwen processes.
4. The test client makes three actual HTTP requests over the private bridge to `GET /api/conversations/count`, requiring: **no key → HTTP 401; incorrect key → HTTP 401; correct ephemeral key → HTTP 200**. Any mismatch is a hard failure, not a warning.
5. A separate real inference over the same bridge, Qwen output hash/token count, source-built agent server HTTP 200, both network egress negative tests, cgroup CPU/RAM/PID, transient work-volume byte/inode quotas and cleanup remain required. Do not remove those controls to make authentication pass.
6. `ai_factory/factory_rootless_session_auth.py` validates a restricted **metadata-only** receipt; no raw session keys, prompt bodies, bearer credentials, model weights or customer data are copied into artifact storage.

## Security scope and non-claims

The experiment is a brief synthetic operator-controlled HTTP test. **It is NOT an official SDK Conversation**, there are no model-generated tool commands or three-file coding artifacts, no public port forwarding, no production keys and no paid calls. The local model is `llama.cpp` through the `ollama` DNS alias, not an actual Ollama process.

A successful test proves that upstream OpenHands API session-key authentication rejects unauthorized requests in the tested environment. It does not prove the full OpenHands SDK agent runtime, end-to-end authorization for tool execution, model service authentication, formal license approval, full SBOM/legal obligations or universal egress isolation. A malicious process on the same private network could contact the **unauthenticated** llama.cpp model service; its separate service policy remains under review. The configured synthetic `OH_SECRET_KEY` is not a replacement for a managed production secret.

**Human review** is required before any real SDK Conversation, code-writing pilot, merger or deployment. The next stage should test the exact official SDK API against the authenticated private server, with a synthetic empty workspace and independently withheld three-file tests, no automation outside the P0 gate.

**Proof:** `.github/workflows/factory-rootless-session-auth.yml`; reviewer checks the CI outcome and sanitized 7-day artifact. Test:
`python -m unittest discover -s tests -p 'test_factory_rootless_session_auth.py' -v`.

All evidence records declare `actual_sdk_conversation_run=false`, `agent_tool_calls_authorized=false`, `release_authorized=false`, `production_authorized=false` and `automatic_merge=false`.
