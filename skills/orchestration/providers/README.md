# CODEN Agent Provider Integration 1.0

**Status:** Experimental contract layer. No live provider integration is enabled.

## Purpose

Provide a provider-neutral contract for registering provider metadata, capability allowlists, secret references, policy checks, and auditable simulation receipts. This layer is deliberately separate from routing: routing recommends a role/capability, while the catalog validates whether a configured provider profile advertises that capability.

## Current contract

- `ProviderProfile`: provider ID, display name, supported capabilities, secret reference, enabled flag, and simulated-only mode.
- `ProviderRequest`: request ID, provider ID, capability, task ID, data classification, and payload.
- `ProviderPolicy`: mode, network boundary, and mandatory human approval.
- `ProviderCatalog`: profile registration, adapter registration, safe profile listing, duplicate request rejection, and fail-closed dispatch.
- `SimulatedProviderAdapter`: deterministic receipt; never contacts a provider.

Capabilities are explicitly allowlisted. Only `synthetic` and `public` data classifications are accepted. Sensitive and personal data are rejected. The payload is represented in receipts by a SHA-256 digest; raw prompt/payload content is not copied into the receipt.

## Secret handling

Profiles store a reference such as `secret://codex/api-key`, never a credential value. This module does not resolve secret references, read environment variables, access a vault, or return credentials. A future secret manager integration must provide scoped retrieval, rotation, audit, and zeroization controls. Do not place API keys in repository files, task payloads, logs, or profile metadata.

## Provider onboarding status

Provider names are configuration identifiers, not claims of vendor integration. Factory AI, Manus, Codex, OpenHands, and OpenAI-compatible services may be evaluated as future adapters only after their official API, authentication, data-processing, contractual, and execution boundaries are reviewed. No provider is ranked or automatically selected here.

## Safety invariants

- `mode` must be `simulated`; `live` is rejected.
- `network` must be `disabled`.
- Human approval must remain true.
- Only enabled registered providers and explicitly allowed capabilities can be used.
- Adapter receipts must explicitly report `status=simulated`, `provider_invoked=false`, and `network_used=false`.
- Duplicate request IDs are rejected.
- No subprocess, network, provider SDK, or credential resolution is used.

## Tests

```bash
python -m unittest skills.tests.test_provider_integration -v
python -m unittest discover -s skills/tests -v
```

## Production gaps

This is not a production provider gateway. Missing capabilities include live adapters, vault integration, tenant isolation, per-provider quotas, rate limiting, spend enforcement, token accounting, retry/circuit-breaker policies, provider health checks, signed receipts, distributed idempotency, and formal data-processing/security reviews. Do not send real user or government data through this prototype.
