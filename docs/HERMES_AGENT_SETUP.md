# Hermes Agent Setup for CODEN

**Status:** Setup guide only. Hermes is not installed or running in GitHub by this document.
**Repository:** `Mohamedalhindawan/coden-national-dpi`
**Default branch:** `main`

## Goal

Run Hermes Agent in a controlled development environment so it can inspect CODEN, work on a dedicated branch, run tests, and propose changes for human review. This does not authorize production deployment or high-impact decisions.

## Recommended path for a mobile-first owner

Use a GitHub Codespace from the repository in a mobile browser if Codespaces is available to the account. This avoids trying to run the full development toolchain directly on Android.

1. Open the repository on GitHub and select **Code → Codespaces**.
2. Create a Codespace from `main`.
3. Open the Codespaces terminal and confirm the working directory is the repository:
   ```bash
   pwd
   git status
   git branch --show-current
   ```
4. Confirm GitHub CLI authentication if `gh` is installed:
   ```bash
   gh auth status
   ```
   In a Codespace, GitHub authentication is commonly provided by the environment. If authentication is missing, use the official GitHub sign-in flow; do not paste a token into chat or commit it to a file.
5. Install Hermes using the current official instructions:  
   https://hermes-agent.nousresearch.com/docs/getting-started/quickstart
6. Run `hermes setup` and follow the interactive prompts for a model provider. Model access may require a separate account, quota, or paid usage. Do not configure paid API usage unless the project owner has approved it.
7. Run `hermes doctor` if available in the installed version and resolve reported setup issues before giving the agent repository tasks.
8. Start Hermes from the repository root using the command in the current official documentation.

## First task: read-only audit

Give Hermes this prompt before permitting edits:

> Read `AGENTS.md`, `README.md`, `CODEN_MASTER_ENGINEERING_PLAYBOOK.md`, relevant files in `docs/`, `app/index.html`, `api/openapi.yaml`, and `tests/`. Report the current architecture, implemented versus planned features, how tests are run, and the safest next small task. Do not edit files, install dependencies, create commits, push branches, access external production systems, or use real personal data. Do not claim tests passed unless you ran them and observed the result.

## Safe write workflow

After reviewing the read-only report:

1. Create a dedicated branch; never start by editing `main`:
   ```bash
   git switch -c feat/hermes-small-task
   ```
2. Give Hermes one bounded task with acceptance criteria and the exact files it may change.
3. Require tests for behavior changes and ask it to run the repository's documented checks:
   ```bash
   python -m unittest discover -s tests -v
   python -m openapi_spec_validator api/openapi.yaml
   git diff --check
   git status --short
   git diff
   ```
   The OpenAPI validator may need installation as documented in `.github/workflows/prototype-checks.yml`. Report any command that could not run; do not infer success.
4. Review every changed file and the test output. Check for secrets, unexpected dependencies, unrelated edits, and changes to privacy/security controls.
5. Only then commit and push the feature branch. Open a Pull Request to `main` and wait for CI and human review.

## GitHub permissions and secrets

- Prefer the least privilege needed for the task. Avoid repository administration and deployment permissions for the agent.
- Do not create a Personal Access Token just for convenience if the existing Codespaces/GitHub CLI authentication is sufficient.
- Never put tokens, API keys, passwords, private keys, or other secrets in prompts, source files, shell history, logs, issues, or commits.
- Do not expose the Codespace or agent terminal to untrusted users.
- Review any tool permissions that allow shell commands, browser actions, or delegated subagents before enabling them.

## CODEN-specific guardrails

Follow `AGENTS.md` and the master engineering playbook:

- Synthetic/demo data only; no real citizen, beneficiary, identity, financial, or health data.
- Tamam remains a prototype. Do not claim a backend, database, real authentication, payments, or official government integration exists unless implemented and verified.
- No autonomous benefit eligibility decisions, payment decisions, production deployment, spending, or changes to identity/security rules.
- Human review is required for high-impact changes and for merging.
- Do not claim that Hermes is connected, installed, or running until the environment has been configured and tested.

## Troubleshooting

- **`hermes` command not found:** restart the terminal or follow the installer's PATH instructions in the official docs.
- **Git push denied:** check `gh auth status` and the repository permissions; do not paste credentials into chat.
- **Model/provider error:** verify the selected provider's sign-in, availability, quota, and billing settings. Installing Hermes does not provide free inference automatically.
- **Android/Termux problems:** prefer Codespaces or a supported Linux/macOS environment; consult the official platform-specific documentation before trying unofficial workarounds.

## Official links

- Hermes Agent docs: https://hermes-agent.nousresearch.com/docs
- Quickstart: https://hermes-agent.nousresearch.com/docs/getting-started/quickstart
- Hermes repository: https://github.com/NousResearch/hermes-agent
- CODEN repository: https://github.com/Mohamedalhindawan/coden-national-dpi
