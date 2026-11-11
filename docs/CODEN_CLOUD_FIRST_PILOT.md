# CODEN AI Factory: browser-first cloud pilot

## Scope and status
This is the first **no-Termux, no-new-server** step. It uses the existing GitHub Actions workflow `Prototype checks` and does not run autonomous AI coding agents. No cloud VM, paid API, deployment, or persistent service is provisioned.

## Run from Android browser
1. Sign in to GitHub and open `Mohamedalhindawan/coden-national-dpi`.
2. Select **Actions** → **Prototype checks**.
3. Select **Run workflow**, choose the reviewed branch, and confirm.
4. Open the run to inspect `contract-tests` logs and conclusion.
5. Do not interpret a queued run as passed. If GitHub limits or disables Actions, stop and inspect account/repository settings before changing any billing.

## Current security and spending limits
- Workflow has `contents: read` only and no secrets or model API calls.
- Runs are limited to 15 minutes per job and redundant runs on the same ref are cancelled.
- Tests use repository demo/synthetic fixtures; do not upload citizen data.
- No automated merge, deployment, paid provisioning, or external model invocation.
- Runner availability and GitHub billing rules depend on repository visibility, account plan, and usage. Review GitHub Actions usage/billing settings before repeated execution.

## Next milestone (separate approval)
Demonstrate a reviewed, single-task AI coding workflow in an isolated runner with explicit model budget, no production credentials, and draft PR only. Do not add `workflow_dispatch` inputs that execute arbitrary shell commands or untrusted model-generated code with elevated GitHub tokens.

## Acceptance
A reviewer can trigger the existing workflow from a phone browser, inspect the logs, and verify that a run concluded successfully. This document and the workflow edits alone are **not** evidence that a run succeeded.
