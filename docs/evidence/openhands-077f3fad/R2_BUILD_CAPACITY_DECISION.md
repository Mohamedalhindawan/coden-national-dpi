# R2 isolated build capacity and decision receipt
2026-11-24 | REVIEW ONLY | Issue #162 OPEN
build_authorized=false; live_conversation_authorized=false; release_authorized=false.

## Verified current integration
Commit dfa8b68133f382cc88e62d7c07ae5e6c614af707, Prototype checks run 45483888421: 381 total, 380 passed, one skipped. All eleven #172 cancellation tests and two alert integration tests pass, including a real synthetic owned child group stop. Intake 45483888391 success. Branch-restricted OpenHands workflows skipped; not new runtime evidence. Prior #167 actionlint 39 workflow PASS at 45483067181 predates cancellation code. No proof of whole process tree disappearance or live agent.

## Exact R2 wheel capacity calculation (static, no install)
Reopened local CODEN_Coding_Profile_Prebuild_R2_REVIEW_ONLY.zip; SHA256 bfdab41496d033756517a2327463859c42b951fda4a48a988b2bce9173c7c2cf, CRC clean, every MANIFEST.sha256 entry rehashed. Parsed lock SHA256 93447ba7c43d7c8bffe1bb66d99abad1eaffcbd0d11fe1ef5bb776c7155998a3 and selected build-inputs.json. For each of 131 unique selected records, exact name/version/URL/SHA256 matched one lock wheel with size. No external downloads of wheels or execution in this calculation. Independently rechecked ZIP hashes of source artifacts 14953280210, 14952151177, 14953700367 against PREBUILD_R2_CHECKPOINT.md.

| Quantity | Bytes |
|---|---:|
| Runtime registry wheels (126) | 103216645 |
| Build tool registry wheels (6) | 2282407 |
| Shared wheel (one) | 129956 |
| Unique selected compressed wheel total | 105369096 |
| Source patch | 6522 |

Largest inputs: litellm 1.108.3 36341841 B, botocore 1.44.3 16368633 B, pillow 13.0.0 7142544 B. Unique compressed wheel total is about 100.49 MiB. These are lock-declared sizes bound to previously verified wheel hashes; not new actual extraction/installation measurements. Four editable source trees, interpreter, build outputs, caches, expanded file counts and installed size are additional. The prior 128 MiB scratch/8192 inode/60 s synthetic envelope cannot be assumed sufficient.

## Proposed bounded non-agent experiment — requires explicit operator decision
Reuse existing source build recipe and rootless envelope; do not launch an agent or run build in the old unrestricted runner. Proposed upper limits for one experiment: 2 CPU, 4 GiB RAM including tmpfs, no swap, 128 PIDs, 1 GiB private scratch with 65536 inodes, 600 s wall-clock (plus bounded cleanup), one attempt. No paid API, no GPU, no network in build, no privilege/socket/production mounts or inherited credentials. No claim these limits suffice; abort on preflight/resource failure, no automatic increase or retries. Exact prior runtime base Ubuntu digest 9a04f13b3f80ef056361e30868593b1cfd2279fe19e4081cb93a90bf56819d6a is evidence only; Python 3.13.15 executable/build environment immutable archive/digest and OS dependency evidence still needed, not established by version alone. Prior uv 0.13.7 / setup action pins are reuse candidates, not complete interpreter provenance. Stage only pinned source/patch, verified wheel files and approved interpreter as isolated read-only input; measure expanded archive bytes/member counts safely without installing first, ensure writable budgets, use offline/no dependency resolution install with exact verified inputs only, validate resulting environment before building. Preserve all notices and explicit legal decisions; outstanding native and static Rust attribution and source-to-wheel rights review remain. Do not silently approve source use/distribution. Use synthetic negative checks for network, credentials, resource limits and host access, independent process accounting and cleanup. Only sanitized artifacts; no execution of generated server during this build-only experiment. Evidence must distinguish build success, installed inventory, signed provenance and final runtime license/security closure. Separate explicit approval for a real official SDK Conversation after actual runtime checks and independent #148 acceptance. No main merge/deploy. 

Operator decision requested: approve one isolated, non-agent R2 build experiment subject to all prerequisite evidence and review, within these ceilings, or adjust scope. This document itself grants no authority. 


## 2026-11-26 — Retained inventory recomputation and source-tree size review
REVIEW ONLY / Issue #162 OPEN / no build or installation authorization.

Previous candidate 6ddb84e84134389c4d1b4929f45f2bf5baa31225: Prototype run 45890303106 job 140151039253 completed SUCCESS, 579 tests (578 passed, 1 optional SDK skip); OpenAPI OK; intake 45890302915 and packaging 45890302968 SUCCESS; six specialized workflows skipped. RED 243b89092eba059249dfd2c20531a2729fe85bc2, run 45890255305 job 140150888200: 579 tests, 3 failures, 1 skip. Reclaim-first staging ordering and explicit queue snapshot inconsistency alert tested; exhaustive oracle for 125 three-archive size combinations. No measured real-build improvement.

### Recomputed retained inventory (no candidate packages downloaded)
Reopened retained artifact 14981902769, ZIP SHA256 7545f36fd8a8e4a049fa980cf60a716787ab0f3db05eb923182bd6d084ffe6b6, and 14981519094, ZIP SHA256 091a251a8f10cd704b2a42520140c697cab31464541763da80d6bffe4fbf805e. Both locally rehashed and CRC clean. Wheel inventory 131 unique names, identity digest 65775d2185597245ae1f2e7aa98820a4c92040bd21b4bc8e8725495dd2e6922f and size-bound digest bebbaa4e714a76ff1a128ca98862fdb3e48cbf4775669af2e1d56b4d88f30e9a match existing workflow binder. Python candidate SHA256 45816a2653b47a6cc48d8ada4ea1185758a4c2db389d012b31e0205e5ccb548b remains unexecuted/unadmitted. Recomputed using retained inventory metadata, not freshly inspected target archive bytes.

| Quantity | Bytes |
|---|---:|
| 132 input compressed total | 223853378 |
| Expanded payload total | 687648604 |
| Initial page-rounded input allocation | 224100352 |
| Old modeled peak | 765633786 |
| Reclaim-first modeled peak | 765633786 |
| No-reclaim concurrent payload model | 989725946 |
| Scratch ceiling | 1006632960 |
| Proposed reserve | 134217728 |
| Remaining after modeled peak and reserve | 106781446 |
| No-reclaim plus reserve deficit | 117310714 |

19042 archive members. All 132 have modeled expanded allocation greater than rounded compressed allocation, so the new ordering provides NO improvement for this exact retained dataset. Prior 270-to-191-byte synthetic improvement is not a production estimate. Reclamation model assumes only verified disposable archives can be reclaimed; input retention must be explicitly reviewed, no deletion here.

### Exact upstream tracked source metadata (not checkout/build evidence)
GitHub recursive tree for OpenHands/software-agent-sdk commit 077f3fad6d31cd852be5c87176e0a93c3b446126 returned nontruncated tree and 2694 entries; four subtrees below. Sum Git blob sizes and round each tracked blob to 4096-byte pages. No symlinks or gitlinks reported for these roots or the whole tree. No package/source execution or checkout, no generated-file/installer size measurement.

| Root | Tree SHA | Files | Bytes | 4096-byte rounded |
|---|---|---:|---:|---:|
| openhands-sdk | 5a581a7caab58b726717435d387872b5e52799b6 | 340 | 3475517 | 4227072 |
| openhands-tools | efbe422a9a589955a2af6d0d5bcf273bcded6bb9 | 128 | 839946 | 1150976 |
| openhands-workspace | 6f71f57b8708c3bae22c3a9be064edbb98f3754f | 23 | 143338 | 196608 |
| openhands-agent-server | ffa31982fa7ff66ccce52a5a8b847894316f5dd1 | 127 | 1775331 | 2023424 |
| Four roots | — | 618 | 6234132 | 7598080 |
| Entire tracked tree | — | 2297 | 28593051 | 33579008 |

Illustrative additive sensitivity, assuming source allocations coexist with peak and are incremental to unchanged reserve: four roots leave 99183366 B, one whole tracked tree leaves 73202438 B, two copies leave 39623430 B. The full tree includes the four roots; do not sum both as separate copies. Tracked bytes do not bound checkout, .git, patched sources, generated files, build isolation/install duplication, filesystem directory metadata, outputs, cache or inode consumption; reserve adequacy remains unproven. No-reclaim with reserve exceeds ceiling even without sources. No increased scratch request or automatic reclaim policy. No independent review, source-to-binary proof or runtime admission; R2 REPAIR_NOT_ADOPTED, GNU EXPKEYSIG unresolved. Build/install/import/real Qwen/agent still blocked, release_authorized=false.


## 2026-11-27 — Split build/runtime staging refinement
REVIEW ONLY; #162 OPEN. Original root-wheel-build-manifest SHA256 f396d96fe5e8f3cf1f38c2c786f749929f4bc3cc40cd9470a590c43facb9d19b explicitly separates build environment from runtime. Reopened historical inventories 14974383159 (c13917dbb24822108ffd36981e4a0e624e50a61a60d8cc43e62fcf00bc3285e8) and 14974862025 (c0a12f46ed63508dc164f78d58429435fe56cffdf0efcfe485f551bb59eeda93), local hashes and CRC PASS. Exactly three declared build-tool identities match inventory and manifest name/version/wheel hash/size. Retained inventory counts below, not target bytes acquisition.
| Input | Compressed B | Expanded B | Members |
|---|---:|---:|---:|
| setuptools 84.2.1 | 876263 | 3002768 | 348 |
| wheel 0.46.3 | 30557 | 87810 | 19 |
| packaging 26.3 | 129956 | 499179 | 29 |
| Python 3.13.15 | 118484282 | 386276509 | 4525 |
| Build-only input set | 119521058 | 389866266 | 4921 |
Full upstream tree at pinned 077f3fad6d31cd852be5c87176e0a93c3b446126 is nontruncated; all four root pyproject files use setuptools.build_meta, static name/version/dependencies and package discovery; no setup.py/setup.cfg/MANIFEST.in at root of any of the four packages. This supports examining an offline no-dependency build; does not prove backend hooks, dynamic requirements or successful build. Separate installer pip remains subject to vendor/legal review.
No-reclaim page-rounded model (compressed round up; expanded payload plus 4095*members), with 128MiB reserve and one whole tracked source tree of 33579008 rounded B:
| Stage | Input count | No-reclaim model B | Remaining after reserve/tree under 960MiB B |
|---|---:|---:|---:|
| Build-only | 4 | 529543137 | 309293087 |
| Runtime-only before root wheels | 127 | 974927650 | -136091426 |
| Combined historical inventory | 132 | 989725946 | -150889722 |
Build-only staged payload model is 46.5% smaller vs combined, not measured speed or actual peak. Proposal: preserve original immutable inputs outside candidate reach, independently admit OS/Python and build-only exact tools first, run existing one-attempt non-agent build in separate offline boundary with no dependency resolution/no network; validate and attest four outputs, then tear down. Separately admitted runtime installation still requires 126 external wheels + four new roots, verified installation/RECORD and reclaim/order/capacity proof. Never silently drop runtime dependencies, widen resources, bypass package semantics, or use source patch/lock substitution. If backend requests undeclared dependencies or output/capacity deviates, abort; no automatic retry. Real build and OS trials 0/1 consumed each, conditional approvals unchanged, independent reviews zero; release_authorized=false.
Prototype45911242889 and intake45911242878 success at baseline 5f8b889f43e4fde1c28b31bf578db2ff26c9d7ba; specialized jobs skipped. Tokenizers producer run33735388484 metadata rechecked: artifacts9885597962/9885528827 not expired, expiry2026-12-02T08:48:51Z. Prior exact acquisition gate remains; do not silently fetch/run candidate. Independent reviewer still required, collaborator-list endpoint unavailable via connector.
