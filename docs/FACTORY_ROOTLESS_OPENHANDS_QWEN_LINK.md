# CODEN AI Factory v1.0 — signed OpenHands server ↔ real Qwen on a rootless internal Podman network

**Status:** Draft PR #181, unmerged / human review required / *not* agent acceptance or production approval.  
**Previous verified checkpoints:** OpenHands source-built server, signed binary, cgroup and health proof #180; real SHA-pinned Qwen CPU private Docker HTTP inference #175; prior synthetic internal network #174.  
**Security issue:** #162 remains open until the full real SDK Conversation and independent three-file acceptance gates pass.

## Objective and exact meaning

Join two capabilities **without rebuilding either**. Reuse the actual repaired, CI-signed OpenHands 1.63.1 agent-server binary from build run 45431783950 (upstream commit `077f3fad6d31cd852be5c87176e0a93c3b446126`, SHA256 `5ad5fa2bb86256b510df3bfbbd9653fbc60a243ea744a579d3ca4c6fd9e91cf3`). Reverify signature, archived high/critical vulnerability scans, and exact binary hash before creating its container.

Reuse real Qwen2.5-Coder-0.5B-Instruct GGUF SHA256 `1d9614638d18024d0fbb36575a15f1302a3adf044df10345688ec4f6e1c4ff32`, original llama.cpp b12600 SHA256 `da524c71f9dd09913df29264bb7229b99a2de82d8a26e6902e6921d413560d6d`, and three Ubuntu dependency archives whose hashes were previously verified in #175. Build both images **offline** from already verified inputs, inside rootless Podman on a trusted first-party PR-only GitHub Actions runner.

The actual OpenHands server and local model run in **separate resource-capped rootless containers** on one uniquely named `podman network create --internal` bridge. The OpenHands source-built server listens at `127.0.0.1:8002` inside its own container, and the real model uses its isolated `ollama:11434` network alias. **The alias `ollama` is only a DNS label: the actual implementation is llama.cpp, not an Ollama daemon.**

### Mandatory runtime checks

- Rootless Podman v2 cgroup host and CPU/RAM/PIDs controllers; actual private namespace CPU/RAM/PID quotas (OpenHands 1 CPU/1536MiB/96 PIDs, Qwen 2 CPU/1536MiB/64 PIDs).
- No root inside either container; all Linux capabilities dropped; `no-new-privileges`, read-only root filesystems and no host-published port or Docker/Podman socket.
- OpenHands writable `/tmp` is a capped 768MiB tmpfs with 32,768 inodes; `/workspace` is capped to 32MiB/2,048 inodes. Model temporary storage also bounded. Both temporary containers and volumes are explicitly cleaned up, including failures.
- Agent binary starts and responds with HTTP 200 at its own loopback `/health` endpoint; the true OpenHands container independently connects to the real Qwen model `/health`, invokes **one actual** HTTP `/completion`, checks a nonempty bounded model response and verifiable token counters, and retains only a SHA256 digest of the generated words.
- Attempts by the actual OpenHands container to make HTTP connections to a public IP and an external DNS hostname must fail. **A negative pair of network tests is not a mathematical proof against every exfiltration route**; external and host/metadata paths and future network joiners still require more rigorous operator controls.
- All observed server process replicas must reside in the same cgroup and show no capabilities or unexpected credential environment variables; model server has the same resource enforcement. **Do not submit a coding/tool-call prompt or allow any SDK Conversation.**
- Fail-closed code `ai_factory/factory_rootless_openhands_qwen_link.py` accepts a strict JSON evidence schema, requiring all runtime checks to be marked true **only after real commands pass**, SHA identities unchanged and production/merge/session authorization false. `tests/test_factory_rootless_openhands_qwen_link.py` includes positive/negative tests and rejects mock authorization or unknown fields.

## What this stage does NOT prove

This is **real server-to-real-model networking**, not OpenHands operating an autonomous coding agent. The OpenHands server and Qwen are exercised by explicitly scripted operator-owned shell and HTTP commands; there is no official OpenHands SDK `Conversation`, no OpenHands model/tool-calling workflow, no three-file change and no independent withheld coding tests. No customer/beneficiary information or GitHub production tokens enter either container.

The signed binary and two archived scans passed zero HIGH/CRITICAL thresholds in their bounded scan scopes, **but incomplete license notices and the transitive SBOM review are still not Approved**. Podman `--internal` is not a substitute for a stronger service allowlist and identity-based network policy, and this pilot does not prove a general multi-tenant sandbox. Local Qwen service authentication is not yet enabled; there is no host port and the network is ephemeral, and this configuration must not be reused in production.

The definition of done in #162 still requires independently reviewed service authentication, package/license/rights analysis, host egress policy, external reviewer signoff, process recovery, a real official SDK session generating three interdependent synthetic files, held-out tests, and review-only Draft PR. **No automatic merge, paid calls, release or production authorization.**

## Human review and reproduction

Evidence workflow: `.github/workflows/factory-rootless-openhands-qwen-link.yml`. Verify the uploaded sanitized JSON and runner tests before accepting any technical PASS. Use:

```bash
python -m unittest discover -s tests -p 'test_factory_rootless_openhands_qwen_link.py' -v
```

If any OCI, provenance, network or model test fails, the workflow must be recorded **FAIL/BLOCKED** and no artifact may claim successful linkage. Follow-up after this milestone should be the true SDK Conversation pilot, strictly behind the remaining #162 security gate and human review.
