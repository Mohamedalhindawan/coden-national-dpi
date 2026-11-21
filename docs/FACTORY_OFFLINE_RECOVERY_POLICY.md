# CODEN AI Factory — Offline Model Recovery Planning (Draft)

**Scope:** testable, fail-closed decision logic only. **No network calls, model execution, credential handling, automatic provider switching, paid calls, human approvals, deployment or background workers.** This does **not** bypass ChatGPT/Codex subscription limits.

**Base:** PR #132, which adds \`ai_factory/checkpoint.py\` and the offline project wrapper. **Planning:** Issue #131 and 105-candidate research PR #130.

## What is implemented

- \`ai_factory/recovery_policy.py\`: deterministic classifier for structured *sanitized* failure codes and HTTP status codes. Supports quota, rate, context, provider, worker, budget, auth, policy and unknown failures.
- Strict synthetic-only, credential-free model route metadata. Allowed transports: \`local\` and \`official_api_key\` only. Rejects unknown fields, duplicate routes, unsupported subscription/cookie transports, unapproved routes, inadequate capabilities, data classification mismatches and insufficient budget.
- \`ai_factory/recovery_checkpoint.py\`: writes pause/blocked + a safe next-action **identifier** to the existing validated checkpoint journal. Rate limits are recorded separately.
- \`ai_factory/recovery_cli.py\`: bounded offline input JSON; optional operator-owned checkpoint recording; printed output never includes input prompt, raw exception text, tokens or credentials.
- \`configs/model_recovery.example.json\`: defaults deliberately **disabled and unapproved**; demonstrates a safe *pause*, not live fallback.
- 27 new deterministic tests covering decisions, redaction, budget gates, context rework, idempotent journaling, rate limits, and CLI error handling.

## Try a safe offline dry-run

From repo root:

\`\`\`bash
python -m ai_factory.recovery_cli --input configs/model_recovery.example.json
\`\`\`

The default example returns \`decision: pause\` and \`next_action: wait_for_authorized_provider\`. This is expected. **Do not enable or approve a route because the example exists.** Verify the actual local server/model supports requested capabilities and is safe for the data.

To persist a failure against an **already-created checkpoint**:

\`\`\`bash
STORE=/tmp/coden-checkpoints-demo
TASK=synthetic_factory_task_001
python -m ai_factory.recovery_cli --input configs/model_recovery.example.json \
  --store "$STORE" --task-id "$TASK" --event-key failure_001
python -m ai_factory.checkpoint --store "$STORE" show "$TASK"
\`\`\`

For checkpoint initialization see \`docs/FACTORY_CHECKPOINT_RECOVERY_RUNBOOK.md\`. Keep journals outside agent-writable workspaces. The journal is not a secure signed audit store or distributed queue.

## Decision mapping

| Error | Decision | Journal event | Next action |
|---|---|---|---|
| \`quota_exceeded\`, \`rate_limited\`, \`provider_unavailable\` | Propose a suitable route **for review**, else pause | Exact failure code | \`review_fallback\` / \`wait_for_authorized_provider\` |
| \`context_exceeded\` | Pause, no automatic provider switch | \`context_exceeded\` | \`reduce_context\` |
| \`worker_failed\` | Pause, inspect side effects before retry | \`worker_failed\` | \`inspect_worker\` |
| \`budget_exceeded\` | Blocked; no paid retry | \`blocked\` | \`manual_security_review\` |
| \`authentication_failed\`, \`policy_denied\`, \`unknown\` | Blocked, investigate | \`blocked\` | \`manual_security_review\` |

The policy does not infer errors from untrusted strings or raw provider messages. Future authorized adapters must map trusted typed API errors to these codes. HTTP 429 means rate limited; it does not imply when quota resets.

## Security invariants

1. Proposed alternate models are **never executed** by these modules. Every result returns \`execution_authorized=false\` and \`requires_human_review=true\`. Approval must be external, not a boolean an agent can change.
2. Don't use subscription session cookies or personal plan entitlements to route requests to unrelated services. Verify official authorization and terms for each provider integration.
3. Sensitive or unidentified data classes **fail closed**. Current scope is synthetic-only; no government/beneficiary/identity/finance production data.
4. Compare OmniRoute, LiteLLM and Bifrost with identical safe cases, choosing **one** principal gateway before implementing a real connector.
5. Hermes Agent/self-evolution may propose improvements, but cannot approve their own access or spend. OpenHands integration also remains separate.
6. Estimated local route cost \`0\` means no new paid model call in this offline test, **not** zero hardware/electricity costs.
7. A hash-chain journal is not a cryptographic signature. Do not treat \`approved:true\` metadata in an agent-editable config as proof of operator authorization.

## Remaining work for Codex

- Build typed error adapters for officially authorized API clients and a model runtime protocol; test API formats with fixtures.
- Move the operator-approved route registry to a protected trusted store separate from agent-writable configuration.
- Build a durable queue and worker for **idempotent sandboxed** tasks, with independently enforced human review on risky operations.
- Demonstrate end-to-end synthetic quota → checkpoint → independent approval → bounded local model coding → tests → draft PR; test restart and double-execution.
- Evaluate Hermes, OpenHands, and selected gateway against pinned revisions, licensing, security threat models and measured results.
- Prove always-on host monitoring and disaster recovery separately before 24/7 claims.

## Tests

\`\`\`bash
python -m unittest discover -s tests -p 'test_recovery_policy.py' -v
python -m unittest discover -s tests -p 'test_recovery_checkpoint.py' -v
python -m unittest discover -s tests -p 'test_recovery_cli.py' -v
python -m unittest discover -s tests -v
\`\`\`

A passing test is not production readiness; consult GitHub Actions results for the full repository and always review stacked PR dependencies.
