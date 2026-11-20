---
name: test-driven-development
description: Test-first implementation and reproducible verification
---

# test-driven-development

Read AGENTS.md and the relevant tests. Write a failing focused test before behavior changes; observe failure, implement minimum code, then run the focused and relevant full suite. Report exact commands, exit codes, and any unrun checks. Never claim green CI without a completed run.

For a defect, record the failing assertion against the original behavior before applying the fix. Rerun that same test, then the relevant suite. Preserve the failure alongside the successful verification in the PR.

To locate a literal together with its enclosing Python test, run `python -m tools.codex_context QUERY --limit 10` from the repository root. Use `--json` for structured results. Open the returned lines to verify the behavior.

## Completion evidence

Record changed files, tests actually run, security considerations, limitations, and next step. Follow the repository root AGENTS.md. This skill does not grant permissions or enable autonomous deployment.
