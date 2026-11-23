# CODEN AI Factory — Real local Qwen CPU server within private Docker network

**Stage:** Draft PR #175; founder-approved Plan v1.0 retained unchanged, not a production release.
**P0 issue:** #162 OpenHands security admission remains **BLOCKED**.
**Prior work:** #151 genuine offline Qwen model, #173 real Docker cgroups, #174 network to synthetic **mock** HTTP model.

## Scope: genuine Qwen model call, NOT OpenHands agent

This trial packages **actual Qwen2.5-Coder-0.5B-Instruct-Q4_K_M** weights and previously tested **llama.cpp b12600** `llama-server`, builds a local Docker image without build-stage Internet access, then runs it alongside a resource-limited BusyBox client on a Docker `--internal` bridge. Both container filesystems are read-only at runtime, all capabilities dropped, `no-new-privileges`, non-root UID 65534, limits on CPUs, RAM/swap, PIDs and ephemeral tmpfs. No user data, production secrets or paid inference providers are used.

### Hard-locked identity

- Official model revision: `ebb2015119c907b064c512bf053e945850b5875f` from `Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF`; **GGUF SHA256** `1d9614638d18024d0fbb36575a15f1302a3adf044df10345688ec4f6e1c4ff32`.
- Official ggml-org llama.cpp release `b12600` Ubuntu x64 release archive; **SHA256** `da524c71f9dd09913df29264bb7229b99a2de82d8a26e6902e6921d413560d6d`. These original exact checks have already run successfully in #151/#155/#169.
- Docker build base: Docker Official `ubuntu:22.04` **OCI index** `docker.io/library/ubuntu@sha256:f64b2ffc2f10ab8f8505aa56b2664bd846cbb9df87c7e2532e30f7667021c0e6`. Before building, CI pulls/verifies exact digest and Linux amd64, and builds **without network**.
- Client: Docker Official BusyBox indexed digest `73aaf090f3d85aa34ee199857f03fa3a95c8ede2ffd4cc2cdb5b94e566b11662`. A locally constructed model image is **not** an approved independently attested product image; it remains ephemeral, self-contained and SHA-labelled for this experiment only.

Official source references: https://github.com/ggml-org/llama.cpp and https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF .

### Evidence gates

1. Require `sha256sum --check` on both source assets **before** they enter an image; require immutable Docker base image digests and no floating runtime tags.
2. Independently inspect the model and client containers, requiring exactly two members on an `--internal` bridge, no published host ports, no bind mounts/Docker socket/privileges/secret environment, and fixed resource budgets.
3. Check true in-container cgroups and privilege state. Real server gets 2 CPU, 1536 MiB RAM, PID limit 64; client 1 CPU, 256 MiB RAM, PID limit 64.
4. Confirm the real model server responds on the internal alias `http://ollama:11434/health`; submit an **actual** POST at `http://ollama:11434/completion`, not a mock HTTP result. Verify bounded nonempty response, `tokens_predicted` and matching timing tokens and retain SHA256 of generated text, not raw generated text.
5. Independently test failure to connect to `http://1.1.1.1/` and `http://example.com/` from inside the client. Network denies tested outside egress, but **does not** provide a universal per-service ACL against a compromised Docker host or extra attached containers.
6. Write sanitized, time-bounded `coden-real-qwen-private-review.json` as the sole artifact; cleanup the two containers, private network and locally constructed image using `trap cleanup EXIT` even on failed checks.
7. Any failed verification = **BLOCKED**; no fallback from genuine Qwen to canned mock responses or public model APIs.

### Limitations: what remains NOT done

- **This server is `llama.cpp`, not actual Ollama.** The alias `ollama` is a compatibility label for network topology only, not a claim that the Ollama application is running.
- No actual OpenHands SDK `Conversation`, agent-server image, three-file code generation, tool calling, persistent Worker, automatic model routing or production release. Issue #162 remains open.
- Rootless Docker **HOST** has not been verified. Running as UID 65534 inside a rootful engine is not equivalent to rootless isolation.
- Model licenses, complete transitive **SBOM**, build attestation and vulnerability reviews have not reached human `APPROVED`. No model/source catalog auto-promotion.
- One successful real CPU completion is a **connectivity and inference test**, not a demonstration of high-quality coding, robust prompt-injection defense, multi-agent behavior or world-class benchmarks. Actual model quality must be independently measured.
- Disk/inode controls, tenant separation, full network egress/metadata interception, child process controls for the official SDK runtime and secrets governance remain independent checks.

**Human review:** required for every Draft PR, source approval, actual OpenHands execution and any subsequent deployment. No automatic merge, no paid provider calls, no change to founder-approved plan v1.0.
