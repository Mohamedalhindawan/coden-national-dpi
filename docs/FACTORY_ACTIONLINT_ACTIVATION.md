# CODEN AI Factory — P0 actionlint actual execution pilot

**2026-11-23 — Draft PR #167 — UNAPPROVED — no merge/deployment.**

## Why this source and not another catalog entry?

The source is **already** in the CODEN 84-source Adopt-First catalog as **`source-061`** (`rhysd/actionlint`); it is NOT a 85th source or another agent engine. This activates one tiny, high-leverage **workflow static lint pilot** on GitHub's existing free CPU runner. It finds GitHub Actions YAML/schema/expression mistakes *before* running heavyweight models, thereby reducing rework and wasted CI executions.

The official source is https://github.com/rhysd/actionlint. Release version `v1.7.12` is pinned by tag and, **more importantly, exact Linux/amd64 archive SHA-256**:

`8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8`

Official archive URL: https://github.com/rhysd/actionlint/releases/download/v1.7.12/actionlint_1.7.12_linux_amd64.tar.gz

The source owner publishes a checksums file and GitHub release asset digest, which is what the workflow independently checks. **A checksum is artifact identity, not a security audit or legal approval**. No new broad `pip install`, no `curl | bash`, no GitHub App permissions, no API keys, no reusable write credentials, no dynamic `latest` download.

## What actually runs

The **branch-specific first-party Draft PR** `.github/workflows/factory-actionlint-p0.yml`:

1. Uses Github checkout without persistent credentials and only `contents: read`.
2. Runs TDD contract tests `tests/test_factory_actionlint_p0.py`.
3. Downloads the exact official release asset into the temp directory, verifies its SHA-256 before archive extraction, and runs `actionlint -version`.
4. Runs the **real actionlint executable** on two checked-in workflows: `.github/workflows/ai-factory-intake-dry-run.yml` and its own `.github/workflows/factory-actionlint-p0.yml`.
5. Writes an intentionally **invalid synthetic workflow** into `$RUNNER_TEMP`. Requires actionlint to reject it with a diagnostic naming `invalid_custom_key` (this proves a genuine checker, not a mock).
6. Retains a sanitized, review-only JSON evidence receipt that explicitly says all source approval and release states remain false. The linter does not mutate any repository file.

Workflow version/asset choice and targeted checks are deliberately narrow to avoid changing all existing CODEN workflows without review. Other workflow files, Docker runtime isolation, model agent security and production secret scanning are **outside this particular proof**.

## Status distinction

- **Executable invoked in CI**: a verified P0 *trial capability*, not a permanent installed 84-source component. Each on-demand job uses a temporary runner.
- **Source registry**: `source-061` remains `proposed_only`, `approved=false`, `enabled=false`, `installed=false`; the identity of the official archive does not override license/SBOM/security review.
- **Skills**: six Draft SKILL.md source procedures in parent PR #166 remain advisory only. This tool strengthens their workflow QA but does not magically load OpenHands skills at runtime.
- **Human review** is required before making the linter an unconditional required gate for `main`, widening the target set or adding new external tools.
- **No automatic merge**, no release authorization, no paid calls, no changes to Supabase, no OpenHands agent session.

## Reproduce

From this Draft PR branch:

```bash
python -m unittest discover -s tests -p 'test_factory_actionlint_p0.py' -v
```

To inspect actual CLI execution and negative test, open the `CODEN Factory P0 pinned actionlint proof` run for PR #167. The proof is **PASS only after the official binary download/checksum, real CLI on actual workflows and negative fixture complete in GitHub Actions**. The static unit tests alone do not prove activation.

## Next high-leverage steps

1. Review the real actionlint diagnostics and sanitize/fix existing workflows if any.
2. After approval, extend the binary-pinned syntax check to the other factory workflows, still no automatic merge.
3. Profile `uv` (existing source-063) with a reproducible hash-locked alternate dependency setup, and `Copier` (existing source-030) for one Golden Template, but only if independently verified to be faster than existing methods.
4. Complete runtime resource limits and independent network checks for OpenHands issue #162 before attempting live multi-file agent execution. Never equate improved CI linting with a ready autonomous factory.

**Licensing note:** repo/source and complete binary distribution license and transitive dependency review remain pending, even if actual lint execution is verified. This source-specific evaluation does not admit the remaining 83 entries.
