---
name: code-review
description: Review changes for correctness and maintainability
---

# code-review

Compare diff against issue requirements and existing open PRs. Inspect edge cases, test evidence, API compatibility, error handling, and accessibility/Arabic RTL when relevant. Report actionable findings by file and line, distinguish blocking issues from suggestions.

Use a separate reviewer when one is available and authorized. Give the reviewer the diff, base revision and acceptance test. Ask them to reproduce one negative case from a clean copy and record the failing assertion. Label an automated check separately when an independent reviewer is unavailable.

To locate a literal together with its enclosing Python test, run `python -m tools.codex_context QUERY --limit 10` from the repository root. Use `--json` for structured results. Open the returned lines to verify the behavior.

## Completion evidence

Record changed files, tests actually run, security considerations, limitations, and next step. Follow the repository root AGENTS.md. This skill does not grant permissions or enable autonomous deployment.
