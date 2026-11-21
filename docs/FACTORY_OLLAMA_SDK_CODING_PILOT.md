# CODEN AI Factory — Official Ollama SDK Coding Pilot (Adopt-First)

**Status:** experimental / operator-only / review pending. This branch is stacked on [PR #146](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/146) and proposed in [PR #147](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/147), not merged into `main`.

## What we actually reuse (not rebuild)

- **Ollama** provides the existing local model server; its official Python SDK **`ollama-python`** provides `Client.generate`. CODEN does not build an inference server, session manager or alternative model protocol.
- **Existing CODEN `ollama_probe.probe`** verifies a model name is listed at the explicitly approved loopback address.
- **Existing CODEN `project.run`** performs AST policy checks, Ruff linting, pinned Linux bubblewrap execution, visible and independent review cases, immutable-review-style package generation and `awaiting_human_review` status.
- This PR adds **only a small integration boundary**: `ai_factory/ollama_sdk_pilot.py`. A real Ollama model/server was **not** installed or exercised in GitHub CI.

This is not a general OpenHands agent runtime and does not yet build a real full-stack or multi-module application. The CODEN proof produces a synthetic `transform(value)` module, a runnable `candidate.pyz` and accompanying test/review files. The SDK is optional, not installed by CI.

## Test-first evidence

- RED: [CI #44857587377](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44857587377) failed because `ollama_sdk_pilot` did not yet exist.
- GREEN on implementation: [CI #44857663103](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44857663103) — 204 tests run (1 conditional skip), OpenAPI PASS. One real Linux sandbox test drives the complete `project.run` path using a **fake SDK client** with prewritten synthetic Python output; no hosted or local model requests occur in CI.
- Follow-up test addition verifies the tracked synthetic task fixture and CLI default no-inference behavior; use the latest branch CI for its result.

## Offline-by-default operator examples

**Readiness check; no network:**

```bash
python -m ai_factory.ollama_probe --model 'qwen2.5-coder:1.5b'
```

**Default SDK pilot; no model call:**

```bash
mkdir -p /tmp/coden-ollama-operator-output
python -m ai_factory.ollama_sdk_pilot \
  --task ai_factory/examples/ollama-python-transform.json \
  --output-root /tmp/coden-ollama-operator-output \
  --model 'qwen2.5-coder:1.5b'
```

Without the explicit inference flag, the result is `status=disabled` and no model is contacted, even if the SDK is installed.

**Only on a trusted operator Linux host with permission, already-installed/pinned Ollama server and an approved local model:**

```bash
# Operator must separately verify: official ollama-python release + dependency
# lock, model weight license/digest, local network isolation and CPU/RAM budgets.
# Do NOT pipe arbitrary upstream install scripts into a privileged shell.
python -m ai_factory.ollama_probe \
  --model 'qwen2.5-coder:1.5b' --probe-loopback

python -m ai_factory.ollama_sdk_pilot \
  --task ai_factory/examples/ollama-python-transform.json \
  --output-root /tmp/coden-ollama-operator-output \
  --model 'qwen2.5-coder:1.5b' \
  --allow-local-inference
```

The model name is an **example only**; availability and weight licensing have not been independently verified. This code does **not** install Ollama, pull weights, start a server, grant execution authority for any other task, or create a GitHub PR.

## Guardrails and limitations

1. **Synthetic-only task**: the task must pass `project.valid()`, have recipe `python-transform`, estimated API cost 0 and request only `run_tests`. The prompt includes only task description plus visible `cases`; `review_cases` remain withheld.
2. **Explicit per-run operator opt-in**: `--allow-local-inference` is required. The endpoint is a numeric IPv4 loopback URL, not remote HTTP, `localhost`, URL credentials or HTTPS. Model identifiers containing a `cloud` marker are rejected. Nonetheless, a malicious/misconfigured local server or model alias could contact an upstream system; enforce network egress controls and inspect actual local model metadata outside this pilot.
3. **SDK settings**: uses `Client(host=..., timeout=90, follow_redirects=False, trust_env=False)` and one nonstreaming `generate()`, temperature 0, max 192 predicted tokens, `keep_alive=0`; no tools or automatic retries. Rejects a populated `OLLAMA_API_KEY` environment because the official SDK may otherwise attach it to requests.
4. **Output**: rejects malformed/oversized model source (>8 KiB), demands the exact AST shape `def transform(value)`, then hands the source to the existing sandbox reviewer. Candidate source is written under a temporary restricted directory and deleted afterward. The independent review gate remains **not approved**.
5. **No real model tested in CI**: an injected synthetic client exercises the official SDK method contract, while a real pinned Linux sandbox checks the resulting `candidate.pyz` and `review.json`. The repository does not yet carry a vetted SDK installation lock or a pinned real model. Passing tests **does not** prove model coding quality or deployment readiness.
6. **Scope of resources**: a local inference call can still use meaningful CPU/GPU and time. The `timeout=90` applies to the SDK HTTP connection; an operator-owned cgroup/container or stronger worker cancellation remains required for production. No use of real citizen/government/customer data, autonomous process, paid API, auto-merge, self-modification or production deploy.

## Next required integration gates

1. Independent review of this exact PR and predecessor PR #146, including optional SDK supply chain.
2. On an authorized host, pin Ollama + Python SDK + model weights, block external networking and establish a resource budget before one permitted local synthetic generation.
3. Capture actual output and run the existing CODEN evidence verifier; compare generated files to hidden acceptance tests.
4. Trial **OpenHands SDK** for a genuine **multi-file** software task in a strong sandbox; measure it against this simple synthetic baseline.
5. Compare **OmniRoute vs FreeLLMAPI** individually as alternative gateways with official provider terms and no shared API credentials in source control. Do not layer both gateways by default.
6. Complete separate [worker/supervisor PR #140](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/140) security signoff before any persistent operation.

**Current readiness:** local SDK interface integration `TESTED WITH FAKES`; real Ollama model run `BLOCKED`; multi-file OpenHands agent `BLOCKED`; operator-reviewed worker `DRAFT`; production factory `NOT READY`.
