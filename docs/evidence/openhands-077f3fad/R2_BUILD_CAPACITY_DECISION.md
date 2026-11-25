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
