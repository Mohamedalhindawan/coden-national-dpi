# CODEN AI Factory — Provider-Neutral Runtime Evidence Contract

**State:** a tested, offline, synthetic-only, **metadata contract**. It is not an inference API, gateway adapter, SDK connection, model execution service or approval authority.

**Code:** `ai_factory/runtime_contract.py`. **Tests:** `tests/test_runtime_contract.py`.  
**Existing security policy:** `ai_factory/recovery_policy.py`, plus checkpoint, SQLite queue and operator-invoked worker in PR #132.

## Motivation

Future CODEN coding runtimes (OpenHands, Hermes, Codex, local llama.cpp) and gateways (OmniRoute, LiteLLM or Bifrost) should submit comparable **sanitized metadata** without requiring the core factory to trust model-specific responses.

The contract deliberately carries **SHA-256 task and artifact references**, not prompts, source-code content, model credentials, OAuth cookies, API keys, or personally identifying data.

## Request schema (illustrative; never grants execution)

```json
{
  "schema": "coden.runtime.request.v1",
  "task_id": "demo_1",
  "task_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "classification": "synthetic",
  "required_capabilities": ["coding", "tool_calls"],
  "allowed_providers": ["local_qwen"],
  "allow_external_api": false,
  "max_tokens_total": 2048,
  "max_duration_seconds": 90,
  "max_cost_usd": "0"
}
```

## Report schema (illustrative, from an *untrusted* adapter)

```json
{
  "schema": "coden.runtime.report.v1",
  "task_id": "demo_1",
  "provider_id": "local_qwen",
  "model_id": "qwen_local",
  "transport": "local",
  "status": "completed",
  "error_code": null,
  "artifact_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "input_tokens": 300,
  "output_tokens": 400,
  "duration_ms": 2500,
  "cost_usd": "0"
}
```

## Offline check

```bash
python - <<'PY'
from ai_factory.runtime_contract import assess
request = {
  "schema": "coden.runtime.request.v1", "task_id": "demo_1",
  "task_sha256": "a"*64, "classification": "synthetic",
  "required_capabilities": ["coding"], "allowed_providers": ["local_qwen"],
  "allow_external_api": False, "max_tokens_total": 1000,
  "max_duration_seconds": 90, "max_cost_usd": "0"
}
report = {
  "schema": "coden.runtime.report.v1", "task_id": "demo_1",
  "provider_id": "local_qwen", "model_id": "qwen_local",
  "transport": "local", "status": "completed", "error_code": None,
  "artifact_sha256": "b"*64, "input_tokens": 100,
  "output_tokens": 200, "duration_ms": 100, "cost_usd": "0"
}
print(assess(request, report))
PY
```

Expected: contract_valid=true but **artifact_verified=false, provider_approved=false and execution_authorized=false**. A hash claim must be independently checked against actual files before approval or release.

## Hard validation rules

- Unknown fields fail closed; raw prompts, output text, secrets, passwords, cookies and self-granted approval flags cannot be inserted as metadata.
- `classification` must be synthetic in this version; no citizen, identity, health, financial, government or production customer data.
- Only `local` and `official_api_key` transport identifiers are accepted. External transport is disallowed unless the request separately allows it; allowing a transport is **not an approval to call it**.
- Task IDs, provider IDs and model IDs must have safe syntax and match a task-level allowlist. The task SHA and result SHA are lower-case 64-character hex values.
- Token, elapsed-time and cost metadata must remain within the request's declared maximum. This is **post-hoc contract validation**, not real-time budget enforcement; a future runtime must actively stop calls before exceeding limits.
- Completed reports require a result digest and no error. Failed, paused or blocked reports need sanitized canonical error codes and cannot claim a completed artifact.
- No adapter may use this contract to perform external actions, approve deployment, merge to GitHub, or bypass subscription restrictions.

## Which integration should Codex add first?

1. Run the existing local Qwen/llama.cpp pilot through a **strict metadata-producing wrapper** and validate it against this contract.
2. Add fake official-provider adapter fixtures for quota/timeout/401/429 with no live API keys, and connect them to recovery_policy.
3. Evaluate ONE official gateway candidate (OmniRoute, LiteLLM or Bifrost) with legally authorized credentials in a separate sandbox only after owner approval; measure latency, cost and tool-call correctness.
4. Pilot OpenHands SDK on a preapproved synthetic multi-file task. Treat Hermes as a separate skill/memory/CAIE experiment with no self-approval rights.
5. Verify artifact file digests and independently held-out tests. Add real-time kill switches and operator-owned approval before any paid or non-synthetic use.

## Tests

```bash
python -m unittest discover -s tests -p 'test_runtime_contract.py' -v
python -m unittest discover -s tests -v
```

**Note:** A passing contract test proves the shape of metadata and budget checks, not that a model is correct, a gateway is safe, or a provider license is valid.
