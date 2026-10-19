# Free / Open-Source AI Toolchain for CODEN

**Goal:** Accelerate delivery while keeping costs near zero during the prototype phase.
**Status:** Proposed toolchain; none of these tools is automatically connected to the repository just because it is documented here.

## Recommended roles

| Role | Candidate | Cost reality | Use in CODEN |
|---|---|---|---|
| Main coding agent | OpenAI Codex CLI — https://github.com/openai/codex | CLI software is open source; model access may require an eligible account or paid usage | Plan and implement bounded tasks, inspect repository, run tests; require review for risky changes |
| Alternative pair programmer | Aider — https://github.com/Aider-AI/aider | Open-source tool; model API or local compute may cost money | Smaller code edits, Git-aware changes, test/fix loops |
| Local model runner | Ollama — https://github.com/ollama/ollama | Runner is free; needs suitable RAM/CPU/GPU and model storage | Optional local assistance for lower-risk tasks; quality and speed depend on hardware/model |
| CI and regression tests | GitHub Actions + repository tests | Public-repository free usage may have limits/policies; verify current account and runner limits | Run tests and API-spec validation on pushes and pull requests |
| API contract | OpenAPI + pinned validator | Open standards/tooling; CI still consumes compute | Validate the interface before implementing backend endpoints |
| Security checks | Dependency audit and secret scanning tools | Tool availability and free limits vary | Detect known dependency issues and accidental secret commits |

Sources:
- Codex: https://github.com/openai/codex
- Aider: https://github.com/Aider-AI/aider
- Ollama: https://github.com/ollama/ollama
- OpenAPI validator: https://github.com/python-openapi/openapi-spec-validator

## Suggested operating loop

1. Create a small, explicit GitHub issue with acceptance criteria.
2. Agent reads `AGENTS.md` and the relevant project docs.
3. Agent works on a branch, not directly on production.
4. Agent implements one bounded change and adds/updates tests.
5. CI runs tests, OpenAPI validation, and available security checks.
6. Review the diff and CI output; merge only after passing checks.
7. For identity, payment, access-control, privacy, or social-benefit decisions, require human review and do not allow unattended deployment.

## Cost-saving principles

- Start with the tools already available; do not subscribe to multiple paid coding agents.
- Keep model/API spending disabled until a budget and usage limit are explicitly approved.
- Local models are not automatically faster or better; benchmark on the actual machine before choosing them.
- Free software does not imply free hosting, inference, CI minutes, or support.
- Never put API keys, secrets, or real beneficiary data in prompts, issues, public logs, or test fixtures.

## Device / workflow limitation

The current owner workflow is mobile-first, while most coding agents are designed for a terminal or desktop environment. Repository edits through GitHub are possible, but a fully autonomous coding agent is not installed or running in the background from this document alone. To enable a real agent, it must be installed/configured in a suitable environment and explicitly granted repository access.

## Rollout

### Stage 1 — Free baseline
- GitHub repository and issues
- GitHub Actions for deterministic tests
- Contract-first API specification
- ChatGPT-assisted bounded changes
- Human review of diffs

### Stage 2 — One coding agent
- Choose Codex CLI **or** Aider, not both initially
- Run it in a controlled development environment with least-privilege access
- Require branch-based changes and tests
- Measure task success, defects, and time saved

### Stage 3 — Optional local inference
- Trial Ollama only after checking laptop specifications
- Compare latency, output quality, and power/thermal impact
- Use it for documentation or simple tests first, not for unreviewed security-sensitive code

### Stage 4 — Production engineering
- Add reproducible environments, dependency pinning, vulnerability scans, backup/restore tests, monitoring, and release approvals
- Keep human approval mandatory for high-impact actions
