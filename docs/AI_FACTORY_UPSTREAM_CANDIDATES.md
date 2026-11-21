# CODEN AI Factory — upstream integration candidates

Status: **evaluation only**. This file does not install, vendor, execute, or authorize any third-party software.

## Candidates

| Project | Upstream | Intended role | Decision |
| --- | --- | --- | --- |
| OpenHands | https://github.com/All-Hands-AI/OpenHands | Coding agent/runtime | Pilot candidate, not installed |
| Gas Town | https://github.com/steveyegge/gastown | Multi-agent orchestration | Evaluate separately, not installed |
| MetaGPT | https://github.com/FoundationAgents/MetaGPT | Multi-role agent workflow | Compare only |
| CrewAI | https://github.com/crewAIInc/crewAI | Agent coordination | Compare only |

## Integration sequence

1. Record the exact upstream release/tag and commit, its license and dependency licenses, support status, and security advisories. Do not pin to a moving `latest` tag.
2. Review installation permissions, Docker socket exposure, network egress, telemetry, secret handling, cost, and host filesystem mounts.
3. Run a **single** candidate against a disposable synthetic repository with a dedicated low-privilege account and an isolated runner, never the CODEN production repository.
4. Capture command logs, actual tests, budget/latency, resource use, and any attempted disallowed actions.
5. Only after independent review, propose a pinned integration in a separate draft PR with a rollback plan. Do not auto-merge or deploy.

## Acceptance gates

- Explicit approval of provider and expected spend before any paid API calls.
- No real citizen data, production credentials, or write-capable GitHub token in an untrusted agent runtime.
- No Docker socket exposed to an untrusted container without a reviewed isolation architecture.
- Worktree/branch isolation, network controls, per-task budgets, audit logs, human-reviewed draft PR.
- Confirm licenses and distribution rights before copying upstream source. Link to upstream by default.

## First pilot

Prefer assessing **OpenHands** for a single bounded synthetic coding task; compare **Gas Town** only when parallel-agent coordination is a demonstrated requirement. Do not run both simultaneously for the initial experiment.

Existing CODEN synthetic intake, review gate, and GitHub Actions preview are preparatory controls, **not** evidence that these frameworks are installed or operational.
