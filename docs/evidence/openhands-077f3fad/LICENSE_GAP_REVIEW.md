# P0 OpenHands license metadata gap: review checkpoint (2026-11-24)

Status: **BLOCKED — evidence review only; unapproved.** Continues #183 and #162. Master Plan v1.0 unchanged.

## Observed evidence
- Exact #183 tested head: `50f1304b7dd6bce726df47e89af1a213bfd9c2d6`. GitHub Actions reports completed/success for [runtime](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45441979951), [prototype checks](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45441979958) and [intake](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45441980011). Historical evidence, not new test execution. The runtime tested an operator-authored tool action, not an SDK Conversation.
- Retrieved the actual repository ZIP [fixed-source-provenance.zip](https://github.com/Mohamedalhindawan/coden-national-dpi/blob/50f1304b7dd6bce726df47e89af1a213bfd9c2d6/docs/evidence/openhands-077f3fad/fixed-source-provenance.zip) via GitHub Contents API (blob `b06c6826c86692f2a07e2b75fd2ca0a36b091a4f`). Decoded ZIP directory and DEFLATE entries, checked expanded sizes and parsed `build-environment.json` and `materials.json` without executing any package. **232 records, 9 missing all three license metadata fields** (expression, classifier list, file list); the other 223 have at least one field, not necessarily a complete or approved license.
- The embedded materials record reports environment SHA256 `62bff3d305d139e881dc83ed390f10a6db44b3860a055eca25ec60af3c9c920a`, repaired lock SHA256 `6d8348da6768ae32bb7665bdc7ca2525d53e576e13729fcc41f0a28df7c25b69`, build run 45431783950. These reported digests and historical attestation were not freshly cryptographically reverified here.
- Independently fetched the upstream [LICENSE](https://github.com/OpenHands/software-agent-sdk/blob/077f3fad6d31cd852be5c87176e0a93c3b446126/LICENSE) at exact commit `077f3fad6d31cd852be5c87176e0a93c3b446126`: MIT, Git blob `b0bd86a6335a564bd3766666bebbf014fd6a8013`. The four package manifests at that same commit identify version 1.63.1. Root license is direct source evidence, not proof of complete wheel/binary notices or nested third-party rights.

## Nine exact gaps

| Package | Version | Evidence/status |
| --- | --- | --- |
| agent-client-protocol | 1.0.0 | Unresolved; exact release page could not be fetched. SDK manifest lists it as a direct dependency. |
| browser-use-sdk | 2.0.15 | [Exact PyPI release](https://pypi.org/project/browser-use-sdk/2.0.15/) indexed; no verified license text for this distribution. Do not enable external Browser Use cloud. |
| jsonref | 1.1.0 | [Exact PyPI release](https://pypi.org/project/jsonref/1.1.0/) indexed; third-party [MIT metadata lead](https://pypistats.org/packages/jsonref), not a verified artifact license. |
| lmnr-claude-code-proxy | 0.1.23 | [Exact PyPI release](https://pypi.org/project/lmnr-claude-code-proxy/0.1.23/) indexed; license unresolved; do not enable proxy or external calls. |
| openhands-agent-server | 1.63.1 | Upstream root MIT; [manifest](https://github.com/OpenHands/software-agent-sdk/blob/077f3fad6d31cd852be5c87176e0a93c3b446126/openhands-agent-server/pyproject.toml), blob c7ee2951a30227a1dd67b6d64f17032e8f550a52. Package notices pending. |
| openhands-sdk | 1.63.1 | Upstream root MIT; [manifest](https://github.com/OpenHands/software-agent-sdk/blob/077f3fad6d31cd852be5c87176e0a93c3b446126/openhands-sdk/pyproject.toml), blob 1304f0106a4229451882dcf28501df594a921d15. Package notices pending. |
| openhands-tools | 1.63.1 | Upstream root MIT; [manifest](https://github.com/OpenHands/software-agent-sdk/blob/077f3fad6d31cd852be5c87176e0a93c3b446126/openhands-tools/pyproject.toml), blob a3dcf37c0cc35f2109282b8e682ed96f8f7d744f. Package notices pending. |
| openhands-workspace | 1.63.1 | Upstream root MIT; [manifest](https://github.com/OpenHands/software-agent-sdk/blob/077f3fad6d31cd852be5c87176e0a93c3b446126/openhands-workspace/pyproject.toml), blob 3da2c0bdc2c818d9b3aedc3ae7f64a30b0a31034. Package notices pending. |
| protobuf | 6.33.5 | [Exact PyPI metadata](https://pypi.org/project/protobuf/6.33.5/) lists 3-Clause BSD; exact installed artifact and bundled notices still pending. |

## Next admission gate (not implemented or authorized)
1. Reverify archive/material hashes and attestations; use the repaired resolved lock and actual target platform to identify exact selected wheel/sdist hashes, not an arbitrary same-version distribution.
2. Inspect those artifacts statically (no imports/install), collect LICENSE/NOTICE/COPYING and nested third-party texts; map dependency graph to actual frozen runtime vs build-only packages. Do not assume all 232 distributions are shipped or only the nine require review.
3. Review the 30 OS and seven Python medium findings recorded by #179; complete exact runtime closure SBOM and notices and obtain independent reviewer/operator signoff. Never waive unknown licenses or security findings silently.
4. Separate future preflight: local Qwen authentication and model-generated structured tool-call compatibility, comprehensive egress/metadata blocking, watchdog and cleanup. Only after required approvals may a bounded synthetic official SDK Conversation attempt three files with independent #148 acceptance.
5. Keep issue #162 OPEN. No live session, model-selected command, production deployment, paid calls, security policy changes, or merge. This checkpoint is documentation only; no new code tests or live runs were executed.

`openhands_sdk_conversation_ran=false`, `license_admission_approved=false`, `release_authorized=false`, `production_authorized=false`, `automatic_merge=false`.


## Locked distribution artifact candidates (2026-11-24, accelerated iteration)

Read the archived `resolved.lock` ZIP entry from Git blob `b06c6826c86692f2a07e2b75fd2ca0a36b091a4f` at #184 head `13a732128b83535cecee21023fbd664073c3a298`. The expanded entry size matched the central directory. Parsed package blocks for all nine records. Five are PyPI registry dependencies and four are editable local source packages. Listed wheel candidates are compatible with the recorded Python 3.13.15/Linux x86_64 build environment, but actual selected wheel evidence is not yet established. The values below are copied from the archived lock, **not** freshly calculated artifact hashes.

| Package | Candidate wheel tag | Locked SHA-256 |
|---|---|---|
| agent-client-protocol 1.0.0 | py3-none-any | `179c14266997841438ee15245a2668d31b2c695c13bff87d01c36e016185ddd0` |
| browser-use-sdk 2.0.15 | py3-none-any | `5d8ba3836070c67a9774baac556b233e22f266823d3dee34295d98869bec7752` |
| jsonref 1.1.0 | py3-none-any | `590dc7773df6c21cbf948b5dac07a72a251db28b0238ceecce0a2abfa8ec30a9` |
| lmnr-claude-code-proxy 0.1.23 | cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64 | `0fd8e1bfeef82802c8a74533a6d27e7c7912c7db68358ca67976f1635311503f` |
| protobuf 6.33.5 | cp39-abi3-manylinux2014_x86_64 | `cbf16ba3350fb7b889fca858fb215967792dc125b35c7976ca4818bee3521cf0` |
| protobuf 6.33.5 | py3-none-any (alternate) | `69915a973dd0f60f31a08b8318b73eab2bd6a392c79184b3612226b0a3f8ec02` |

All four OpenHands entries at 1.63.1 specify `source = { editable = "<package directory>" }`, not separate PyPI wheels. Review the exact source commit and nested notices for these packages instead of using unrelated published wheels.

Static artifact retrieval: attempts to open all five selected wheel candidate URLs were unsuccessful in the current browsing environment; direct retrieval of the jsonref candidate was also blocked. No wheel archive was downloaded, installed, imported or executed. All five third-party artifact license checks remain **BLOCKED**. Prior metadata leads in this file are not verified licenses.

Next bounded CI task: use the exact archived lock and read-only public CI with pinned actions, download only compatible artifacts from the recorded files.pythonhosted.org URLs, independently SHA-256 check before ZIP inspection, reject unexpected names/path traversal and oversized entries, collect LICENSE/NOTICE/COPYING and METADATA with source hashes, including any nested bundled dependency notices. Verify actual wheel selection separately. Do not run package code or grant license/security admission. Keep review artifact and manual review requirement. No repeat of earlier real-model/runtime jobs is required for this static audit.

Verified existing [#184 initial-head Prototype checks](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45442822864) completed successfully. This is historical CI for the initial documentation commit, not an execution of the proposed artifact audit.


## Observed static CI results and artifact review (2026-11-24)

Verified head `91da8b7bbf25c206c7f780076ef6a286283f7d0e`: [static audit](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45443675358) SUCCESS, focused 5/5; [prototype](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45443675667) SUCCESS, 272 run (271 pass, 1 skipped), OpenAPI pass; [intake](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45443675305) SUCCESS. No package installation or execution in static audit.

Downloaded actual [artifact 14945446397](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45443675358/artifacts/14945446397) and independently computed ZIP SHA-256 `c77b93ba1033907bb89a9cc6a42e64773ca3fdaa75675bf03b6a40755fb6021e`, matching GitHub. Parsed all six candidate records, decoded each collected metadata/notice file and independently checked its SHA-256 against the receipt. Source wheel hashes were checked by CI, not recomputed locally from original wheels. This supersedes the earlier blocked candidate retrieval result, NOT the installed-distribution selection or legal approval gate.

| Exact candidate | Observed license evidence | Status |
|---|---|---|
| agent-client-protocol 1.0.0 | Apache-2.0 text in dist-info/licenses/LICENSE, SHA-256 cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30 | Text observed; obligations review pending |
| jsonref 1.1.0 | MIT metadata and text, SHA-256 c93d594f97a1bc45d04908cd47c707cd7ff078f038a011443e0049ed28da3f31 | Text observed; obligations review pending |
| protobuf 6.33.5 | Both ABI3 and pure Python candidates contain identical BSD-3-Clause text, SHA-256 6e5e117324afd944dcf67f36cf329843bc1a92229a8cd9bb573d7a83130fea7d | Text observed; native bundled notices/selection pending |
| browser-use-sdk 2.0.15 | METADATA only, no license field or notice collected; exact source LICENSE lookup at v2.0.15 and 2.0.15 failed | BLOCKED; no assumption of open-source rights; keep disabled |
| lmnr-claude-code-proxy 0.1.23 | METADATA only, no license field or notice collected; attempted upstream LICENSE lookup failed | BLOCKED; keep disabled |

Four editable OpenHands packages retain the earlier MIT root-source evidence, with package-specific/nested obligations pending. Of nine original metadata gaps, three now have direct candidate wheel license text, four root-source evidence, and two unresolved wheel license texts. None has final legal approval.

## Independent review of previously recorded vulnerability scan

Downloaded [artifact 14940190698](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45431783950/artifacts/14940190698) and independently checked ZIP SHA-256 `684eba3009dc8885f9a3199220996083b32b139cab7d0a13fb63f6e2ac034760`, matching GitHub. Parsed both scan JSONs: Python environment 7 MEDIUM / 1 LOW; OS 30 MEDIUM / 5 LOW; no HIGH or CRITICAL rows in either scan. These are prior scan results, not a fresh vulnerability database scan.

All seven Python MEDIUM records have a reported fixed version across five packages:

| Package | Recorded installed | Highest reported fix in archived scan | Advisory IDs |
|---|---|---|---|
| mako | 1.3.12 | 1.4.2 | CVE-2026-102991 |
| multidict | 6.7.0 | 6.9.1 | CVE-2026-104874 |
| opentelemetry-api | 1.39.1 | 1.45.2 | CVE-2026-114603, CVE-2026-126360 |
| pyjwt | 2.14.0 | 2.15.0 | CVE-2026-101918, CVE-2026-102275 |
| setuptools | 80.9.0 | 83.0.0 | CVE-2026-59890 |

OS: twelve records across libc-bin and libc6 report fix 2.39-0ubuntu8.12, versus installed 2.39-0ubuntu8.9; eighteen other medium records report no fixed version in the archived scan. Counts are package/advisory rows, not unique CVEs.

Next: verify current upstream compatibility and signed OS availability before a separate hash-pinned rebuild/rescan. Prefer excluding unneeded optional dependencies only after proven runtime reachability and supported build changes; otherwise obtain exact artifact rights or keep admission blocked. Prepare tool-call schema compatibility tests without executing model-selected commands. #162 remains open. No runtime admission, no package upgrades applied, no new live SDK tests or merges. All approvals false.
