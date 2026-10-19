# CODEN AI Coding Agent — Quick Start

This guide prepares a controlled first trial. It does not install or start an agent by itself.

## Recommended first trial

Use **one** coding agent at a time. Start with Codex CLI if its model access is already included in the account you intend to use; otherwise compare Aider with a local model. Do not assume that an open-source CLI means free model inference.

Official project: https://github.com/openai/codex

## Safe setup checklist

1. Use a trusted development environment with Git installed.
2. Clone `https://github.com/Mohamedalhindawan/coden-national-dpi`.
3. Read `AGENTS.md`, `README.md`, and the task-specific documents.
4. Check the provider's current installation instructions and account pricing before signing in or enabling model usage.
5. Keep credentials in the provider's approved credential store or environment; never commit them.
6. Create a dedicated working branch for each task.
7. Ask the agent to explain its plan before editing files.
8. Require tests and a concise diff summary.
9. Review changes and CI results before merging.
10. Revoke repository access and remove local credentials when the trial is over.

## First task prompt

Copy this prompt into the coding agent after it has opened the repository:

> You are working in CODEN, a proposed prototype, not an approved production government system. Read AGENTS.md, README.md, the relevant docs, the API contract, and the existing tests before changing anything. Use synthetic/demo data only. Do not add secrets, real citizen data, authentication bypasses, automatic benefit eligibility decisions, payment execution, or production deployment. Work on a separate branch. Follow test-driven development: write or update tests first, run them, implement the smallest safe change, and run the relevant suite again. If you cannot execute tests, state that plainly and provide exact commands. Do not merge your own changes. First inspect the current repository and propose one small next task; wait for approval before implementing any high-impact change.

## Current project checks

Run from the repository root:

```bash
python -m unittest discover -s tests -v
python -m pip install openapi-spec-validator==0.7.2
python -m openapi_spec_validator api/openapi.yaml
```

The commands above are the checks declared in GitHub Actions. Running them locally requires Python and internet access for installing the validator unless it is already installed.

## Mobile-first note

If working only from a phone, GitHub's web editor can change files but is not a reliable substitute for running a coding agent and test suite. Use a trusted terminal/cloud development environment, review its access permissions, and avoid granting broad account access.

## Explicitly not enabled

- No background agent has been started by this document.
- No paid plan, API usage, hosting, or spend has been authorized.
- No production deployment or access to real beneficiary data is allowed.
