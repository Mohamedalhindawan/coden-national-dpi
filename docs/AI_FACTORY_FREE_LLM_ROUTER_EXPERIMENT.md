# Optional FreeLLMAPI experiment for CODEN AI Factory

**Status:** opt-in developer experiment only. This is not deployed, not enabled by GitHub Actions, and not a bypass for Codex Cloud usage limits.

## Decision

Use **FreeLLMAPI** as the single optional, self-hosted model router for local **Codex CLI** experiments. Do **not** stack OmniRoute in front of it: both perform model routing, and a second hop adds complexity without a demonstrated benefit. Keep existing CODEN model gateway decisions unchanged until a measured comparison is reviewed.

Official upstream: https://github.com/tashfeenahmed/freellmapi (MIT; upstream states it is for personal experimentation, not production).

## Developer setup (separate from GitHub)

1. Review the upstream source, security and provider terms before installing. Run FreeLLMAPI on a **trusted local development machine** following its official installation instructions. Do not execute an unaudited remote install script.
2. Add only developer-owned API credentials in the local FreeLLMAPI dashboard. Never put keys in Git, PRs, issues, CI logs or the CODEN repository.
3. Confirm the local service is reachable at `http://127.0.0.1:3001/v1/models` using its documented authorization method.
4. Follow the **upstream Codex CLI client guide** to configure its Responses API endpoint (`/v1/responses`) and a compatible model. Prefer its documented `launch-codex` flow, which avoids storing credentials in configuration files. Check CLI and router version compatibility.
5. In an isolated synthetic-data test project, verify one read-only prompt, one tool-call round trip, and one intentional rate-limit/fallback. Inspect logs for secret exposure. Disable the integration if tool-call or response formats fail.
6. Record observed latency, errors, model identity and provider terms. Obtain explicit approval before using this integration for a shared CODEN environment.

## Boundaries

- **Codex Cloud** (ChatGPT browser) cannot be reconfigured by this repository file; its usage quota remains independent.
- FreeLLMAPI's free providers have variable quotas, availability, tool support and terms. Do not assume any published aggregate token estimate is a guaranteed entitlement.
- Keep the router bound to loopback for experiments. No public port, no production PII, no government or financial data.
- No CI job should call free external LLM providers by default. Tests must be deterministic and run offline.
- This guide adds **no live integration**, credentials, paid service, deployment, or permissions.

## Acceptance checklist before any future runtime integration

- [ ] Owner confirms which developer machine/environment runs Codex CLI
- [ ] Router and CLI versions pinned and reviewed
- [ ] Responses API streaming/tool-calling contract test passes
- [ ] Rate-limit fallback and timeout behavior tested
- [ ] Provider terms and data-handling reviewed
- [ ] Local secrets and log redaction verified
- [ ] Explicit human approval for any shared or production use
