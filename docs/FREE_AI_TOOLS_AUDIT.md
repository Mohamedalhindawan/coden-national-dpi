# CODEN Free AI Tools Audit

**Date checked:** 2026-10-20  
**Status:** Initial shortlist; availability, free quotas, and account eligibility must be rechecked before depending on any service.  
**Constraint:** Start at $0. Do not add paid services without explicit approval.

## Existing repository foundation
- GitHub repository and Issues: source of truth for tasks and changes.
- GitHub Actions workflow `.github/workflows/prototype-checks.yml`: runs Python contract tests on push, pull request, and manual dispatch. Workflow configuration exists; a successful run has not yet been confirmed.
- Tamam prototype: static demo only, synthetic data, no server submission.

## Candidate tools

| Tool | Role for CODEN | Software/license vs actual running cost | Decision |
|---|---|---|---|
| GitHub Actions | Automatically run tests and checks | Public-repository usage is generally available subject to current platform limits and runner policy | Use now; verify runs |
| OpenAI Codex CLI | Coding agent to inspect/edit code and run commands | Open source; model access and execution environment may have limits or costs | Evaluate first if compatible with current ChatGPT access |
| OpenHands | Multi-step software engineering agent | Open source; requires a supported runtime and model/provider access, which may incur costs | Keep as alternative; not first setup |
| Aider | Git-aware coding assistant | Open source; requires a model endpoint or local model | Keep as lightweight alternative |
| Ollama | Runs supported models locally | Software is free; hardware/electricity are not; model performance depends on hardware | Defer until a suitable computer is available |
| n8n | Workflow automation and service integration | Self-hosted community edition is available; hosting and some features/integrations may cost | Later phase, after API exists |
| GitHub Copilot Free | Coding assistance in supported GitHub/IDE workflows | Free plan has usage limits and feature differences | Optional trial; check account limits |
| Replit | Browser-based development/prototyping | Free allowance and AI limits can change | Optional only; do not depend on unlimited free AI |

## Recommended no-budget order

1. Keep GitHub as the project source of truth.
2. Confirm GitHub Actions tests actually run and pass.
3. Use ChatGPT for requirements and review, and create small GitHub issues with acceptance criteria.
4. Evaluate one coding agent only; avoid installing multiple overlapping agents.
5. Add a separate security review and dependency scanning workflow before adding a backend.
6. Add orchestration (n8n) only when there are real workflows and APIs to connect.

## Important limits

- Open-source does not mean the AI model, hosted runtime, or compute is free.
- GitHub Actions is automation, not an AI coding agent by itself.
- No independent AI agents are currently confirmed to be running against this repository.
- Never commit API keys, credentials, real beneficiary/citizen data, or production secrets.
- Use synthetic data only. Human approval remains required for identity, payment, benefit eligibility, security, legal, spending, and production-release decisions.

## Next verification tasks

- Inspect recent workflow runs and record the actual test result.
- Check current free-plan quotas and access for candidate coding agents.
- Choose one agent based on whether it can work from the user's phone/browser and whether a genuinely free model/runtime is available.
- Do not enable write access or unattended merges until branch protections, tests, and review controls are established.
