# AI Factory — reviewed draft PR handoff (pilot)

## Evidence
The read-only synthetic preview workflow succeeded in GitHub Actions run 43112693406 and uploaded artifact `coden-synthetic-preview`. This is not an AI model run and not a security certification.

## Manual first, automation later
1. Open the successful run and download the artifact before its one-day retention expires.
2. Inspect `review-report.json`, `review-manifest.json`, `proposed-change.diff`, and `demo-task.txt`. Confirm the contents are synthetic, expected, and do not contain secrets.
3. A human reviewer decides whether to authorize a *separate* development task. The preview itself is not authorization.
4. On an isolated development branch, a human or separately approved coding agent may implement a scoped change and run tests.
5. Create a **draft** pull request against the reviewed base branch. Include task ID, scope, tests, changed paths, risk notes, and link to evidence.
6. Require independent review before marking ready, merging, deploying, or enabling any paid API.

## Security boundaries
- The preview job retains `contents: read` and **cannot push or create PRs**.
- Never grant `pull_request_target` write access to untrusted PR code.
- Do not reuse a production credential or `GITHUB_TOKEN` with write permission inside untrusted model-generated code.
- A future PR creation service should use a separate trusted workflow with narrow permissions, protected environments, and explicit reviewer approval.
- GitHub Actions job timeout is not a dollar-denominated API budget. Track actual LLM spend separately and fail closed.
- Use synthetic data only. Never merge or deploy automatically.

## Gate to next stage
Review and approve a threat model for the write-capable workflow, prove isolation and least privilege, then implement on a new branch with tests and a draft PR. Until then, do not auto-create PRs from generated patches.
