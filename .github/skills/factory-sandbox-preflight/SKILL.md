---
name: factory-sandbox-preflight
description: Diagnose and block unsafe CODEN Factory agent execution; verify local model, Docker rootless/network and CPU-memory-PID isolation before an OpenHands or generated-code trial.
---
# CODEN Factory — Runtime isolation and budget preflight

## Trigger
Use before running untrusted agent-generated code, opening a DockerWorkspace, enabling a new local model or changing worker/sandbox configuration. Status: **DRAFT** instructions.

## Steps
1. Verify the exact trusted host/runner, immutable upstream image digest and dependency lock; no floating `latest`, unknown registries or raw install scripts.
2. Confirm actual CPU, RAM/memory, PID, disk, wall-time, file descriptor and process-group caps for both the agent server and child commands. Check cgroup limits independently: a Python timeout alone is insufficient.
3. Verify rootless/nonprivileged container; deny Docker socket mounts, inherited cloud credentials, host network, SSH/TCP remote Docker contexts, privileged caps, extra ports and uncontrolled shared volumes.
4. Isolate approved model traffic; prefer local `Ollama` or the proven `llama.cpp` / `bubblewrap 0.12.0` CPU pilot. Prove no egress or paid API fallback. Do not leak token/keys in evidence.
5. Test negative cases: bad image digest, hostile environment, symlink/parent traversal, no network, excessive memory, long-running process and unexpected startup side effects. Verify forced termination and cleanup.
6. Only then perform one limited synthetic agent session with explicit operator approval and independent multi-file review. If any control is unproven, return `BLOCKED_FOR_REAL_SESSION`.

## Evidence
Read `ai_factory/openhands_upstream_preflight.py`, issue #162 and the existing authentic Qwen workflow. Source-code static analysis is not runtime isolation proof. Do not claim safe OpenHands deployment while issue #162 remains unverified. Human review, **no automatic merge**, no production access, release_authorized=false.
