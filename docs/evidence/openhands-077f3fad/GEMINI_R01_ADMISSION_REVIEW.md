# Gemini R01 handoff — admission and integration review
Status: REVIEW ONLY / PARTIAL ADOPTION / Issue #162 OPEN.
Baseline 23ad8bd7ebc1b6165fb47e3d954cdd4895340470; #193 Draft.

## Input verification
User-supplied CODEN_GEMINI_ENGINEERING_HANDOFF_R01.zip, 40058 bytes, SHA256 82714cb27b6023f8e55b17fb1f23b98afb17b6bc7231c636346f269cf75341d6. 37 entries: 36 payloads and MANIFEST.sha256, all 36 hash matches, ZIP CRC clean. Six JSON and two YAML documents parsed, three shell scripts passed bash -n only. No supplied scripts executed. Internal manifest is not publisher attestation. Gemini reports repository/lock inaccessible; no build, code change or end-to-end tests performed by Gemini. Public-source claims not independently reverified by this review.

## Admission decisions
| Handoff group | Decision | Action |
|---|---|---|
| LICENSE_CLOSURE_MATRIX.csv / LICENSE_EVIDENCE.json / THIRD_PARTY_NOTICES.md / LICENSE_BLOCKERS.md | RESEARCH ONLY | Useful license search leads, no legal admission. Match exact locked binary and embedded component versions/notice bytes. |
| SUPPLY_CHAIN_EVIDENCE.json / PROVENANCE_VERIFICATION.md / verify_provenance.sh | REVISE | CPython source signature is not standalone binary provenance; do not accept hash of wrong wheel or warning-and-continue attestation. Missing manifest must fail, not self-generate trusted manifest. Bind identity, issuer and exact digest. |
| OPENHANDS_BUILD_SOLUTION.md / CODING_ONLY_PROFILE.md / BUILD_REQUIREMENTS.txt / build_openhands.sh / BUILD_VALIDATION_PLAN.md | REJECT AS EXECUTABLE | Existing patched source and 131 exact selected wheel inputs remain authoritative. Stock --no-deps does not fix metadata; server normal resolution may reintroduce excluded packages. func-timeout explicitly forbidden by existing import contract. No unpinned >= or pip bootstrap. Preserve full import/metadata/negative checks; actual server launch separately gated. |
| RESOURCE_OPTIMIZATION_PLAN.md / BUILD_CAPACITY_ESTIMATE.json / ISOLATION_PREFLIGHT.sh | ADOPT IDEAS ONLY | Binary dependencies, no caches and controlled bytecode generation, bounded staging. Estimates not measured. Writable persistent disk outside approved scratch is rejected. nproc/free/df/ulimit display is not rootless/cgroup/network/time enforcement. 2 GiB alternative not authorized. |
| LOCAL_LLM_INTEGRATION.md / MODEL_COMPATIBILITY_MATRIX.csv / MODEL_GATEWAY_CONFIG.example.yaml / LOCAL_MODEL_TEST_PLAN.md | DEFER P1 | Retain proved Qwen3-0.6B Q8_0 + llama.cpp local link; structured-output and negative routing tests are candidates. No 14B/32K context or fallback assumptions under current limits. No static demo keys, unapproved remote endpoints or silent parameter dropping. Network deny needs enforcement, not observation alone. |
| OSS_ADOPTION_DELTA.csv / INTEGRATION_PRIORITY_MATRIX.csv / REUSABLE_SKILLS_REGISTRY.json / ADOPT_FIRST_RECOMMENDATIONS.md | CANDIDATES ONLY | Deduplicate against existing 84 registry and six skills, then verify individual repo/version/license. No second queue or inference gateway now. |
| FACTORY_BENCHMARK_PLAN.md / ACCEPTANCE_CRITERIA.json / INDEPENDENT_TEST_CASES.json | ADOPT AS DESIGN BACKLOG | Ten evaluation dimensions accepted as proposed coverage, not runnable fixtures or passed benchmarks. Implement independent fixture/hidden tests, exact metrics and denominators, isolated evaluation and baseline comparisons. |
| CONTINUOUS_OPERATION_DESIGN.md / AGENT_RECOVERY_PLAN.md / SELF_IMPROVEMENT_GUARDRAILS.md / AUTONOMOUS_TASK_LIFECYCLE.yaml | PARTIAL DESIGN ONLY | Draft-only and human-controlled improvement retained. Reject automatic uncertain-result retries, direct agent GitHub write token, 1800s default and replacing current durable queue. Keep reconciler/quarantine/lease controls. |
| 00_READ_ME_FIRST.md through 05_INTEGRATION_ORDER.md / MANIFEST.sha256 | ARCHIVAL | Source context only; no executable authority. |

## Exact-version reconciliation
Current Python receipt includes pip 26.2.1 (Gemini reviews 26.3); current fastmcp-slim 4.2.0 (Gemini describes fastmcp 4.2.5); current tokenizers 0.23.2 (Gemini 0.23.3); current jiter 0.16.0 (Gemini 0.19.0). setuptools 84.2.1, Pillow 13.0.0 and PyInstaller 6.22.3 version matches do not establish identical artifacts or native closure. Retain exact SHA-bound R2 lock 93447ba7c43d7c8bffe1bb66d99abad1eaffcbd0d11fe1ef5bb776c7155998a3. All candidate upgrades require fresh resolution, metadata, exact artifact license/security and import checks.

## P0 follow-up
1. Verify exact standalone 20260814 artifact SHA256 45816a2653b47a6cc48d8ada4ea1185758a4c2db389d012b31e0205e5ccb548b; inspect release-attestation availability for that artifact, distinguish producer checksum from independent signature. Inventory CPython/pip vendors, actual native members and required OS libraries; collect notice bytes and match upstream exact release. No execute or install.
2. Resolve fastmcp-slim/tokenizers notices and compiled Rust/native membership gaps, Pillow BOM omissions, legal approval. Do not infer static absence of GPL components from missing SONAME.
3. Compare bounded non-PyInstaller package-based execution with original packaging plan; prove actual metadata closure, stage exact pinned artifacts read-only and enforce approved rootless scratch. Do not silently switch deliverable or increase limits.
4. Reuse synthetic isolation workflow at approved ceilings; prove CPU/RAM/no swap/PIDs/bytes/inodes/network/timeout and cleanup. Only after prerequisites reviewed proceed to one non-agent build.
5. Preserve previous operator conditional approval issue comment 7144392543. Attempt not consumed. Live SDK Conversation and releases remain unauthorized.

## P3 candidate coverage
TC-01 regression, TC-02 feature, TC-03 multi-file, TC-04 comprehension, TC-05 test generation, TC-06 security, TC-07 performance, TC-08 architecture, TC-09 resources, TC-10 docs. First prioritize TC-03 with existing independent three-file verifier and synthetic workspace. TC-09 measures cgroup peak/time/resource enforcement; do not conflate 3.5 GiB proposed metric with 4 GiB hard ceiling. TC-05 branch coverage vs coverage delta must be reconciled. Single-case per dimension is not a pass-rate benchmark. No automatic security gate or threshold change.
