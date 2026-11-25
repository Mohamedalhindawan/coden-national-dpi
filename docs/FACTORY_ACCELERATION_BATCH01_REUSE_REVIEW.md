# CODEN AI Factory — Execution Acceleration Batch 01
2026-11-24 | Acceleration Plan v1.0 — proposed, unapproved | REVIEW ONLY
Owner-supplied 45-section addendum; frozen v1.0 unchanged; v3.0 roadmap retained.
No live Conversation, installation of new tools, automatic approval, main merge, paid API or deployment.

## Snapshot and branch map
main ca1eb4e728a8bd09552d8d4b8fdc9594ea5a862a. #191 9fd4de5cf8cd2b09a56c6d4ed356f645f02e7509 is 168 commits ahead/0 behind main, 121 changed files. #192 13fec6b1cfc8503d1dd6201b6d78783caded1b70 is separately stacked on earlier #191 c550482; 356 passed, one skipped at run 45472831820. All 13 reviewed PRs are open drafts/unmerged. Compare shows #158, #160, #166, #167, #172 diverged from #191 at main; do not merge whole branch histories.

| PR | Head (short) | Decision |
|---|---|---|
| #191 | 9fd4de5 | P0 base, preserve all evidence |
| #192 | 13fec6b | reuse later; current P1 worker path, no overwrite |
| #158 | 7d598ec | reuse exact registry and prerequisites |
| #166 | e007c3f | reuse exact six skills, catalog, tests and documentation |
| #167 | 4ab8e21 | extend existing actionlint pilot in its own branch; no duplicate workflow |
| #160 | 3928eb4 | reuse offline Spec Kit assets after P0; existing MIT notice |
| #140 | a05708c | worker/supervisor previously reused in #192 |
| #150 | f27e827 | Supabase metadata only, no service role in worker |
| #170 | 38431d8 | review existing recovery status vs #192 queue_health |
| #171 | 8fca9e4 | extend cancellation, reconcile durable_queue/offline_worker conflicts |
| #172 | d9f32a2 | extend supervised cancellation, reconcile four changed core modules |
| #152 | 9fe8904 | 72 baseline sources, preserve as prerequisite |
| #153 | b711427 | preserve critical source pin evidence, not new registry |
| #165 | 09ed684 | reuse admission backlog after review of dependencies |

## Adopt / Reuse / Extend / Hold
| Item | Decision | Reason / next acceptance |
|---|---|---|
| OpenHands SDK / Qwen3 / Podman / bubblewrap | REUSE P0 | earlier real server/link and synthetic isolation evidence, not new candidate runtime |
| uv | REUSE P0 | R2 locked resolution already verified, no alternative resolver |
| Syft / Trivy | REUSE P0 | prior real scan tooling; scan actual built image and native dependencies when allowed |
| OSV-Scanner | EXTEND P0 if specific coverage gap | first measure overlap with existing Trivy; pin and compare; no new install now |
| ScanCode Toolkit | ADOPT conditionally P0 | use if exact notice gap needs static source license detection; not legal approval |
| pip-audit | HOLD P1 | avoid duplicate Python vulnerability scan until measurable gap |
| actionlint | EXTEND P0 #167 | real pinned v1.7.12 pilot targets two workflows only; expand paths/negative tests in same PR |
| zizmor / Gitleaks | EXTEND P0 | inventory existing controls before adding; no unverified binaries |
| Ruff / existing unittest CI | REUSE P0 | full suite retained; pytest migration not required for first execution |
| GitHub MCP | REUSE P1 | current connector used for reading and bounded draft writes; no added server |
| Skills #166 | REUSE P1 | source-only six skills; current chooser recommends one task kind, no agent activation |
| Registry #158 | REUSE P1 | one read-only view of original 72 + 12, 84 proposed entries, 76 repos |
| Spec Kit #160 | REUSE P1 | immutable templates offline, retain attribution, no duplicate OpenSpec |
| Serena / ast-grep / Tree-sitter / Repomix / Copier / Testcontainers | HOLD until scoped P1 pilot | prove benefit and avoid sensitive context; no bulk install |
| Renovate / pgvector / Langfuse / Harbor | HOLD P2 | after stable nucleus; no auto-merge |
| Temporal / Hatchet / LangGraph / CrewAI / Hermes / vLLM / SGLang / Backstage / ERPNext / Qdrant / OpenBao / full Grafana / gVisor | HOLD | deferred per owner proposal; do not install |

## Actual bounded integration
Branch feat/factory-acceleration-batch01-20261124 based on exact #191 head.
Reused 10 byte-identical files from #166 (six SKILL.md, catalog, manifest, guide, tests), 8 byte-identical files from #158 (three modules, three existing JSON inputs, guide, tests). Verified all 18 Git blob SHA-1 values against source refs after writing. AGENTS.md additive paragraph matches #166 blob 1d5a9e76d4a0c83e5f67f174cc5e0825898a9c5b; other rules unchanged. No second registry or skill catalog. Did not copy divergent intake workflow; existing full prototype suite discovers tests. Existing source test runs #166 45252461697, #158 45234698835 passed; new combined CI required. No claim of new run PASS yet. Reuse unchanged tested code, not new behavior implementation. No actual external skill installation or approval.
Registry reachability snapshot dated 2026-11-23; 84 proposed, not 84 installed or currently reverified. Six draft skills remain non-executing. Catalog does not support risk-aware multi-skill selection yet.

## Issue #162 gate and finite next action
PASS evidence within scope: earlier rootless runtime and authenticated local Qwen link #188; synthetic bounded build envelope 45468601818; R2 lock, exact wheel selection 131, static native inventory 45473221215; Pillow embedded BOM and 138 hashed RECORD members 45474104833. 210 Python and 249 Rust source-lock identities scanned in upgraded review, not installed membership. Historical vulnerable Rust scan intentionally fails. See R2_PILLOW_SBOM_RECONCILIATION.md. Open: five Pillow SONAMEs missing producer BOMs (four families), two selected wheels missing embedded notices, full native/static/OS license/security closure, immutable actual build and runtime SBOM, actual isolation checks, explicit operator approval for isolated build and then separate live session. Do not close #162 before official Conversation plus actual independent #148 multi-file acceptance. No new build or install authorized by proposal.
Next: test combined reuse and fix only observed incompatibilities; extend #167 rather than repeat actionlint; prepare measured build envelope for separate explicit operator approval. Do not repeat heavy scans on unchanged input during fast iteration; retain mandatory full checks before approval. No new external tool added. Cost of paid API calls in this batch: zero; CI resource consumption not independently billed/verified.

## Integration checkpoint 02 — 2026-11-24
Combined skills/registry CI at 6772710: 311 total, 310 passed, one skipped, all eleven reused tests passed (45476070310); intake 45476070318 passed. #192 standalone 356 passed/one skipped is not a comparable total. Existing #167 actionlint full review RED 45476929075 (3 diagnostics), 45477264204 (2 diagnostics). Fixed unused loop variable and kept checksum verification strict; remaining SC2094 at unzip archive member/output name corrected by extracting into distinct runner temporary file and reading that file in Python, commit 8335e3d. No warning suppression, no change to envelope limits or exact archive hash. Runtime of changed branch-restricted workflows not reverified by #193; skipped jobs not pass.

Reused all fourteen #192 changed files from exact 13fec6b1cfc8503d1dd6201b6d78783caded1b70, byte-identical Git blob SHA-1 verified after copying. Four prerequisites durable_queue, checkpoint, project and reconcile were identical on both branches; comparison from common earlier #191 c550482 found zero overlap with the fourteen files. Includes worker, supervisor, scheduler, queue health/alerts, two runbooks, seven test modules. No new worker logic, no #192 mutation. No claim of combined PASS until final snapshot CI observed. Cancellation #171/#172 remains separate, live OpenHands #162 blocked, no daemon, no automatic retry/approval, no production or paid API. This update supersedes earlier deferral of #192 reuse, not earlier evidence or the frozen v1.0. 
