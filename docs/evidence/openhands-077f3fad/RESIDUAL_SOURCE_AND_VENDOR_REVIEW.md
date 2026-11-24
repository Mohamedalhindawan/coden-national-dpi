# Residual source notices and vendored metadata — 2026-11-24

Status: evidence review, not legal admission. Issue #162 OPEN. release_authorized=false.

## Verified artifacts
- Run 45458755146 succeeded. ZIP 14951971875 SHA256 3e82d0a7a3762880ca14b10ff00bdf55e89e1b369423de6e9228d2eb76cff28b independently recomputed in local container; every stored source evidence byte hash checked. Six exact locked sdists collected; none has a root LICENSE/NOTICE.
- Wheel artifact 14952151177 SHA256 dc90b88c050aaa59e9e536453f7e83e680f73c5e054dc2083ee58e0be5fe23d8 independently recomputed; 198/198 records. Nine collector tests passed 45458414336. Prototype 45458469026: 299 passed, 1 skipped, hardened import checks 4/4 unit tests only.

## Source and upstream notice evidence
| Package | Version | Exact sdist evidence | Upstream release ref and LICENSE blob | Decision |
|---|---|---|---|---|
| fastmcp-slim | 4.2.0 | Apache-2.0 declaration | https://github.com/PrefectHQ/fastmcp/blob/v4.2.0/LICENSE ; f49a4e16e68b128803cc2dcea614603632b04eac | release-ref evidence, archive linkage and notices review |
| jiter | 0.11.0 | MIT declaration and crates/jiter/LICENSE | https://github.com/pydantic/jiter/blob/v0.11.0/LICENSE ; 47de40dc06ba673d480a12ef728ce62fe43e3151 | review native dependencies and linkage |
| k8s-agent-sandbox | 0.5.1 | no source license declaration found in inspected metadata | https://github.com/kubernetes-sigs/agent-sandbox/blob/v0.5.1/LICENSE ; 8dada3edaf50dbc082c9a125058f25def75e625a (Apache-2.0) | optional workspace extra, linkage pending |
| streamlit | 1.67.0 | Apache-2.0 declaration | https://github.com/streamlit/streamlit/blob/1.67.0/LICENSE ; 57bc88a15a0ee8266c259b2667e64608d3f7e292 | dev-group root, linkage pending |
| tokenizers | 0.23.1 | tokenizers/LICENSE and Rust Apache-2.0 declaration | https://github.com/huggingface/tokenizers/blob/v0.23.1/LICENSE ; 261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64 | review bindings and native dependency linkage |
| tom-swe | 1.0.3 | MIT declaration only | upstream LICENSE lookup at 1.0.3/v1.0.3 and LICENSE.md at v1.0.3 failed; no exact text retrieved | BLOCKED for admission |

Five upstream files retrieved via GitHub connector at named release refs, blob IDs recorded; release refs are not a proof that wheel was built from the corresponding commit. No blanket license approval. No rights inference from a missing lookup.

## Scope from exact candidate lock (202 records, 198 registry + four editable)
Reverse edges: fastmcp -> fastmcp-slim[client,server]; openai -> jiter; litellm -> tokenizers; openhands-tools -> tom-swe (required); openhands-workspace optional agent-sandbox -> k8s-agent-sandbox; root dev group -> streamlit. Do not count the full lock as a deployed runtime. Removing a required dependency needs an explicit reviewed source change, not a metadata override.

## Vendored distribution gap
Read all nested METADATA records from 198 wheel evidence files; 12 nested setuptools distributions, eight name/version pairs absent from candidate lock:
- autocommand 2.2.2 (LGPLv3 declaration)
- backports-tarfile 1.2.0
- importlib-metadata 8.7.1
- jaraco-text 4.0.0
- jaraco-context 6.1.0
- jaraco-functools 4.4.0
- more-itertools 10.8.0
- tomli 2.4.0
Four already represented in lock: packaging 26.3, platformdirs 4.4.0, wheel 0.46.3, zipp 3.23.0. Their presence as vendor copies still needs attribution. This evidence is not a complete inventory of all vendored/native code. Previous Trivy 202/202 lock scan did not cover the eight additional exact name/version pairs. Never label it complete runtime scan.

Next: scan union of exact lock and nested metadata with verified coverage; distinguish build-only from runtime via actual build closure before admission; obtain ToM-SWE notice, Rust and native dependency evidence, independent legal/security review. No install or live Conversation authorized.
