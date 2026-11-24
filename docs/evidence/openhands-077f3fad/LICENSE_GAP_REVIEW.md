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
