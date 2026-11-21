# CODEN Factory PR #126 — Focused Security & Release-Gate Review

**Date:** 2026-11-21  
**Status:** automated technical review of an **offline, synthetic-only, optional** factory prototype. **Not** independent professional penetration testing, production approval, authorized model installation or a software-supply-chain attestation.  
**Pull request:** #126, based on `main`. The follow-on **Draft PR #132** contains separate checkpoint, queue, worker and evidence components.

## What was actually reviewed

- The implementation of `ai_factory/project.py` and `ai_factory/local_coder.py`.
- `tests/test_factory_project.py` and `.github/workflows/prototype-checks.yml`.
- Repository branch dependencies; all prerequisite PRs #116, #118 and #124 are in `main`.
- `docs/FACTORY_PROJECT_RUNBOOK.md`, identifying model weights, pinned hashes and limits.
- CI execution for the pull request. No external or paid inference requests were made during this review.

## Security improvements in this PR

**AST complexity and unsafe assignment hardening:**

1. Bound generated `transform(value)` source code to a maximum of **512 AST nodes** and **40 AST nesting levels**, in addition to existing source-size limits.
2. Restrict allowed `.get` attribute references to **read/access context only**; reject `value.get = ...` writes.
3. Add 3 regression tests:
   - `test_security_rejects_attribute_assignment_to_method`
   - `test_security_rejects_excessive_ast_nodes`
   - `test_security_rejects_deeply_nested_ast_expression`

**TDD evidence:** [failing CI run #44851202259](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44851202259) demonstrated **exactly these three failing security tests** before code changes (test phase: 80 tests, 3 failures, one conditional skip). Following the code change, [CI run #44851251676](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44851251676) passed **80 tests** (one conditional skip) and OpenAPI validation. The separate [intake workflow #44851251636](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44851251636) passed 6 intake tests.

## Relevant existing protections (code/tests, not security certification)

- Synthetic-only task classification and zero paid inference budget; `status-counts` and `python-transform` recipes; bounded visible and withheld review fixtures.
- AST allowlist, restricted builtins, static source lint, then source/package acceptance verification.
- Linux bubblewrap with network namespace separation, cleared environment, read-only mounts and resource/time limits. No unsafe host fallback if the required sandbox is unavailable. The CI suite includes an isolated sandbox probe.
- Hash-pinned local llama.cpp CPU archive and model inputs. Real GGUF inference is opt-in and not executed by the ordinary CI tests.
- Human-review-only result: `release_authorized = false`. The prototype does not merge PRs, deploy or trigger a cloud-model call.

## Open findings / production blockers

| ID | Concern | Current disposition |
|---|---|---|
| SEC-126-01 | Node/depth limits and attribute-write policy in source validator | **Addressed in code and CI regression tests** |
| SEC-126-02 | Only Linux x86_64 with pinned bwrap, namespaces, distro layouts and prlimit supported | **Restricted platform; unsupported hosts must fail closed** |
| SEC-126-03 | Operator-provided local tarball/model assets depend on trusted provenance, pinning and a stable operator-owned filesystem | **Production supply-chain provenance/security review pending** |
| SEC-126-04 | A single synthetic Python transformation and deterministic roles do not demonstrate arbitrary full-stack engineering | **Prototype scope; broader claims blocked** |
| SEC-126-05 | Code quality, OSS licenses, dependencies, image provenance, SBOM and independent threat-model review have not been fully validated for production | **Independent security/legal review pending** |
| SEC-126-06 | No approvals/authenticated identity, persistent worker or supervised real-world production workflow is present | **No production enablement authorized** |
| SEC-126-07 | GitHub workflows include pinned third-party action SHAs, but upstream runner changes/toolchains must be maintained | **Routine maintenance/security verification required** |

## Merge-versus-deploy distinction

A merge to `main` is acceptable *only as an explicitly labeled prototype* if the owner accepts the code-review scope and CI results; it **must not** be interpreted as security certification, operational readiness, permission to deploy, or approval to expose private data. Production enablement, real provider credentials, and unrestricted execution require a **separate independent human security review and approval**.

The next dependent Draft PR #132 must be reviewed independently after this base is merged; its SQLite queue and checkpoint journal are separate stores without an atomic transaction, and its operator-invoked worker is not 24/7.
