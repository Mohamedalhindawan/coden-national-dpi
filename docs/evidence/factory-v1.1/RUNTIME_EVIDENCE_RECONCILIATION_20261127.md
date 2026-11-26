# Runtime evidence recovery and reconciliation — 2026-11-27
Review only, issue #162 OPEN. Baseline fd1a2ab6035a1def70b4fe07a18206094e80ea81. Exact-head CI run 45907788845 job 140208596400: 589 tests, 588 passed, 1 optional SDK skip, zero failures, OpenAPI OK; intake 45907788817 success.
## Actual local evidence recovery
Seven historical CODEN artifacts downloaded, wrapper SHA256 rehashed against retained records/API, all CRC clean (42 archive entries total):
| ID | SHA256 | Bytes | Members |
|---|---|---:|---:|
| 14974824590 | 351d31bce5264ede7500568f4c653b455f365e66ea623f3e9391e0878799c28a | 19170269 | 26 |
| 14966222504 | 05b50a7366cb138c49cc91ccbbb21ad4eeda9ccdc44970dd7a576eae411489a6 | 108908 | 4 |
| 14974862025 | c0a12f46ed63508dc164f78d58429435fe56cffdf0efcfe485f551bb59eeda93 | 225112 | 5 |
| 14974383159 | c13917dbb24822108ffd36981e4a0e624e50a61a60d8cc43e62fcf00bc3285e8 | 243543 | 3 |
| 14945823995 | c7269f6e3ddaba086832c8023f8df21797e3c7b2859b97699d66a88c2485ed94 | 682 | 2 |
| 14945099467 | cbb0c1fffbb7756a2207ccc93fdf6796288b72ae5e9e5bbc38fa7ec5b3c68294 | 552 | 1 |
| 14941957973 | c5fef4b931803b0e4ad4aca2f1fac809ebd8330f93eb8cd1c16061dcdf8062a8 | 967 | 1 |

- R2 wheel metadata: set equality across all 131 selected vs historical inventoried (name/version/digest/compressed bytes/runtime/build flags); 126 external runtime, 6 build candidates, overlap 1. Summed 105369096 compressed / 301372095 expanded bytes, 14517 members, match capacity receipt. Empty recorded notice paths remain exactly fastmcp-slim 4.2.0 and tokenizers 0.23.2.
- Python: identical inventory JSON across two ZIPs; checksum manifest rehashed, matching recorded interpreter identity; 44 text evidence byte counts and hashes revalidated (23 unique hashes); 1047 recorded link targets lexically contained in python/ only, not resolved filesystem proof. Nine ELF identities match original inventory by path/bytes/hash, 2 static archives and 6 PE candidates recorded. 75 wheel ELF records; 265 DT_NEEDED references counted, no new loader binding proof. Interpreter bytes not acquired.
- GNU glibc: four source members matched exact expected.tsv byte sizes and hashes inside previously collected evidence ZIP. Retained EXPKEYSIG and VALIDSIG status both present; no fresh signature verification, no expiry waiver. No source execution/extraction to filesystem.
- R2 missing originals: two named Project file records (r2-offline-installation-manifest-UNAPPROVED.json and modeb-r2-import-contract-UNAPPROVED.json) located in Library, raw-byte materialization denied. Neither digest verified; third root-build manifest not found. No content reconstruction accepted. Exact lock already recovered.
## Verified historical model receipts (not new inference)
- Run [45447230201](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45447230201), head 42c0d0fd59308d2154bed59cccc3bc247627d9f4: Qwen3 authenticated HTTP probe from OpenHands container, schema_match, 27 tokens, both authentication gates, internal bridge and tested metadata TCP denied, cleanup resources_removed, zero paid calls. SDK conversation and tool execution false.
- Run [45445935923](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45445935923), head 6a3e89bd6bbda4ebda32a73f239f6cd47b456929: Qwen3 four schema cases passed (count 27, summary 26, limit 20, empty 19 tokens); tools and SDK not executed.
- Run [45437519514](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45437519514), head 3d6715cb19e48df06995b6e74b9f5e97dbfc04ce: historical rootless OpenHands server/Qwen2.5 real connectivity only, 12 predicted tokens; receipt records cgroup, internal bridge, nonroot read-only capless containers, signed binary provenance, temporary bytes/inode limits. No SDK Conversation, coding tool, three-file output or live execution admission. Neither actual Ollama nor new Qwen inference here; llama.cpp reused. Historical receipts are not full isolation proofs or independent signoff.
## Delivery
Coordinator bundle CODEN_Runtime_Evidence_Recovery_20261127.zip: 19759110 bytes, 9 entries, SHA256 0c794344df1b7d05a170774a7e7de0069433800b69976ee0f7e2d60ab16868d7; reconciliation.json SHA256 ef11e3fd4cdd8a3bfdba59a37ed306dca651fbe13214bb32cd7e8d1c9a54e3e1. No binary committed to repository.
Continue exact R2 original metadata retrieval and independent scanner/legal/security/OS decisions; upstream Tokenizers acquisition separately scoped and unapproved. No download of target wheels or interpreter, no build, install, import, new model inference, live agent, merge/deploy. release_authorized=false.
