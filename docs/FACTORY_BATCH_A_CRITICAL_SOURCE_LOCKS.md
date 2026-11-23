# CODEN AI Factory — Batch A: Critical Source Snapshot Locks (v0.1)

**Checkpoint date:** 2026-11-23  
**Status:** DRAFT / **NOT APPROVED FOR INSTALLATION** / PR #153 stacked on PR #152 (both remain Draft).  
**Parent evidence:** `docs/FACTORY_84_SOURCE_AUDIT_AND_DEVELOPMENT_GAPS_2026-11-23.md` (**84 available GitHub candidate/file links across 76 repositories, not 84 installed tools**).

## Execution completed — in this PR

- Captured **11 critical source/file references** from the existing 72-source baseline, covering **6 independent GitHub repositories**.
- Queried official GitHub repository commit metadata and the matching file at its exact immutable commit, and recorded the **Git blob object ID** for each.
- Created `configs/factory_critical_source_pins_v0_1.json` with the captured 40-hex commit SHA and blob SHA-1 IDs and exact `/blob/<40-hex-commit>/...` URLs.
- Implemented `ai_factory/factory_source_locks.py`, a **read-only, local-data** validator and CLI. It refuses an unknown source, changed source path, duplicate, mismatching commit for one repository, mutable ref, missing blob ID, or unauthorized activation.
- Added `tests/test_factory_source_locks.py` and the CI acceptance gate to reject source-lock corruption and check that every candidate remains pending review.
- **No download, execution, installation, model API, credentials, expense, merging or deployment.** The 72/84 primary proposed source records still say `approved=false` and `pinned_commit=null`; this is an independent *provenance snapshot* and does not silently promote them.

## Exact upstream commits (retrieved from GitHub API on the date above)

| Original source IDs | Upstream | Captured repository commit | Evidence paths |
|---|---|---|---|
| 001–004 | [OpenHands/software-agent-sdk](https://github.com/OpenHands/software-agent-sdk) | `077f3fad6d31cd852be5c87176e0a93c3b446126` | Hello World, isolated Docker workspace, GitHub workflow, workspace implementation |
| 005 | [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | `87f816e87f35f91c8a6f7e561b1f1a7899bee254` | `examples/simple/simple.cpp` |
| 009 | [containers/bubblewrap](https://github.com/containers/bubblewrap) | `1fb0aa26d3eb66254f7742e704add7f82f41a582` | `README.md` |
| 011–013 | [github/spec-kit](https://github.com/github/spec-kit) | `fa7c88fb1c56034a10c4553c9d5527d1a62fc919` | `spec-template.md`, `plan-template.md`, `tasks-template.md` |
| 015 | [astral-sh/ruff](https://github.com/astral-sh/ruff) | `24828519029bf702f1b776cade46e89e0ec23595` | `README.md` |
| 018 | [aquasecurity/trivy](https://github.com/aquasecurity/trivy) | `a7b0d649ea07bf957acdb7a742edc81d27358f2c` | `README.md` |

**Important distinction:** Git commit IDs and Git blob IDs use SHA-1 object identifiers; they are **not** download verification SHA-256 hashes. This locks which source revision and file content object were observed, **not** the integrity of a future downloaded image, binary or model. Those require signed/versioned distributions, artifact digest verification and runtime tests.

**Independent free CPU model evidence:** Separate Draft PR #151 ran a pinned released `llama.cpp b12600` **binary archive** with an independently SHA-256-verified Qwen GGUF. That actual executed binary is a different pinned artifact from the later `ggml-org/llama.cpp` HEAD source snapshot recorded above; **do not treat them as the same deployed version**.

## What remains open — these are mandatory before runtime admission

| Gate | Required evidence | Current |
|---|---|---|
| GitHub source identity | Exact owner, repo, file path and commit metadata | **11/84 captured and structurally verified** |
| Reproducible source build | Reproducible dependency locks, build setup and hashes | **NOT VERIFIED** |
| License compliance | Copyright notices, transitive licenses, obligations, use case, independent decision | **PENDING** |
| Security | Advisories, dependencies/SBOM, static analysis, isolation and malware-risk review | **PENDING** |
| Compatibility | Pinned SDK signatures, OS/runtime and actual CODEN worker integration | **NOT TESTED** |
| Capability and quality | Actual OpenHands multi-file run, secret denial, test evidence, human-reviewable PR | **BLOCKED / UNPROVEN** |
| Budget | Zero-fee trial plus explicit resource ceilings and no unintended paid provider calls | **POLICY PROPOSED; PROVIDER LIMITS REQUIRE CHECK** |
| Approval | Human reviewer signs admission decision and enables one component explicitly | **NONE GRANTED** |

**License warning:** `containers/bubblewrap` API currently reports `NOASSERTION`; its root LICENSE file contains LGPL-2.1 but actual file-by-file rights, linked libraries and distributions require independent review. A GitHub `license.spdx_id` entry is not itself sufficient to approve commercial redistribution.

## How to reproduce the offline checks (free)

```bash
python -m ai_factory.factory_source_locks
python -m ai_factory.factory_source_locks --source-id source-001 --json
python -m unittest discover -s tests -p 'test_factory_source_locks.py' -v
python -m unittest discover -s tests -v
```

CI does not fetch code from GitHub to install it. This is a **low-cost machine-checkable gate** for a recorded immutable source snapshot. No internet, credentials or model needed for this offline check.

## Next step — Batch B, real agent execution

Use the *pinned OpenHands SDK revision* only after verifying its actual SDK/API compatibility, its sandbox boundaries and real model integration. Then execute **one synthetic multi-file task** (three files minimum) with an independent hidden test set, keep `PR Draft`, and record runtime evidence. Integrate the already tested free CPU model and existing CODEN worker only if capability is verified; otherwise mark the trial BLOCKED rather than replacing it with mocks.

After a successful agent trial, implement a separately secured worker↔Supabase bridge without exposing `service_role` credentials to public PR workflows. **Do not automatically approve, install, or merge all 84 sources.**

## Additional safety gate — staged-file integrity (no execution)

`ai_factory.factory_source_locks.verify_staged_blob(path, expected_blob_sha)` now checks the bytes of a **local quarantined regular file** against the original pinned Git blob object ID with no symlink following. It enforces a 2MB default maximum input, rejects changed/missing/symlink files, and calculates an additional local SHA-256 digest for a future independent review. It **does not** download a GitHub source, follow links, execute commands, install packages or grant deployment rights.

Example after an operator separately stages a verified public sample:

```bash
python -m ai_factory.factory_source_locks \
  --source-id source-001 \
  --verify-file /path/to/quarantined/01_hello_world.py
```

The path must point to the **exact bytes** from the commit pinned in `configs/factory_critical_source_pins_v0_1.json`. The check will fail if these bytes differ; Git SHA-1 object identity is not a replacement for independently verified signed source releases or package/binary SHA-256 digests. A passing result is **integrity-matching only**, not an acceptance decision.

The new regression tests cover exact Git object format, byte tampering, symlinks, directories, and oversized staged files. No real upstream source file has been newly installed by this gate.

