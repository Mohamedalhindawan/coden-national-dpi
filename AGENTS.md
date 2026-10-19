# Instructions for AI coding agents working in CODEN

## Project context
CODEN is a proposed Yemeni GovTech / Digital Public Infrastructure project. Tamam is a prototype citizen-facing super-app. This repository is a prototype and planning workspace, not an approved government production system.

## Rules
- Start by reading `README.md`, relevant files under `docs/`, the target code, and tests.
- Work on one small, clearly scoped task at a time.
- Follow test-driven development: add or update tests first for behavior changes, run them to confirm the expected failure when feasible, implement the smallest change, then run the full relevant test suite.
- Never claim tests passed unless they were actually executed and the result was observed. If execution is unavailable, say so clearly and provide the exact command to run.
- Use synthetic/demo data only. Never add real citizen, beneficiary, identity, financial, or health data.
- Never add API keys, passwords, access tokens, private keys, or production secrets to source files, issues, logs, or commits.
- Do not make automated eligibility decisions or represent a demo request as an official benefit application.
- Keep the prototype's Arabic language and right-to-left layout intact unless a task explicitly changes this requirement.
- Prefer accessible, responsive, minimal dependencies and secure defaults.
- Explain changes and limitations in plain Arabic where practical.

## Human approval required
Do not independently deploy to production, change identity or payment rules, decide benefit eligibility, modify security controls, spend money, add paid services, or merge high-impact changes. Prepare a reviewable patch or pull request instead.

## Current prototype constraints
- The Tamam demo is a static client-side prototype.
- Submissions remain in browser memory and disappear on refresh.
- No backend, database, authentication, or server submission is currently provided.
- Existing contract checks are under `tests/`; the GitHub Actions workflow is `.github/workflows/prototype-checks.yml`.

## Completion report
For each task, report:
1. What changed (file paths).
2. Tests actually run and exact outcomes.
3. Security/privacy considerations.
4. Known limitations and next step.
