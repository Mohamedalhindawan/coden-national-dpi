# First Coding Agent: Practical Setup Decision

## Decision
Evaluate OpenAI Codex first because it is an official coding agent and the Codex CLI is open source. Do not assume Codex Cloud is available on the Free plan. Current OpenAI plan documentation says Codex is included across plans with usage limits, while Codex Cloud availability is limited to eligible paid/workspace plans. Confirm the current in-product entitlement before relying on it.

References:
- https://github.com/openai/codex
- https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan

## Important device constraint
Codex CLI runs in a terminal on a computer; it is not a normal Android app that can independently edit this repository from the phone. The user currently primarily uses an Android phone. Do not ask the user to paste API keys into chat or commit credentials.

## $0 path today
1. Keep using the GitHub repository and ChatGPT for planning, scoped changes, and review.
2. Use GitHub Actions to run tests after repository changes.
3. From GitHub mobile/web, open the repository's Actions tab and select `Prototype checks`. The workflow has `workflow_dispatch` enabled, so if repository permissions allow it, choose **Run workflow** on `main`. GitHub documents manual runs here: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow
4. Confirm the resulting run status and inspect logs before claiming tests pass.
5. When a computer or supported cloud execution environment is available, try Codex with ChatGPT sign-in first, verify actual quota, and let it work on a branch or small issue. Do not use a paid API key unless the user explicitly approves spending.

## Safe first task for Codex
Read `AGENTS.md` and `docs/PROJECT_OVERVIEW.md`. Review the Tamam static prototype and its contract tests. Report potential defects and propose tests first. Do not add backend, authentication, real data, payments, automated eligibility decisions, or production deployment in this initial task.

## Exit criteria before expanding agent autonomy
- A real test run is green and visible.
- Agent changes are reviewable in a branch/PR.
- Secret scanning and dependency/security checks are enabled.
- Branch protection and human review are in place.
- Costs and model usage limits are documented.
