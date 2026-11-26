# Critical-path evidence preservation and admission queue — 2026-11-27
Review-only. Baseline f38c3242e75c99ae30aad0ecf557af89e22dc19b; issue #162 OPEN. release_authorized=false.
## Time-sensitive evidence (metadata freshly queried)
| Producer run | Artifact ID | Reported wrapper SHA-256 | ZIP bytes | UTC expiry |
|---|---:|---|---:|---|
| [CODEN 45461338865](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45461338865) | 14953280210 | 37d29fb4d202ef634d4f8f036519e62ec4fafe2062b4221ed0bf8b4dbe814f6a | 94163 | 2026-12-01 18:36:36 |
| [CODEN 45461645493](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45461645493) | 14953700367 | 68c72538a3e6b4fb83af9cb4eb95840d2cfb379cbd8cce21969d916505199167 | 99786 | 2026-12-01 18:38:42 |
| [Tokenizers 33735388484](https://github.com/huggingface/tokenizers/actions/runs/33735388484) | 9885597962 | 26cefb048f96a11e605e5937de700355b3d58c732c7b58bdfaaa5ed513751d0a | 3354040 | 2026-12-02 08:48:51 |
| same | 9885528827 | cb3490cd18f5ba9e3ae81043d7e58318c3604787610d7427967bdd4ad8675c49 | 385989 | 2026-12-02 08:48:51 |
All four API records reported expired=false. Metadata only; no new ZIP acquired or inner digest verified. The first two are historical CODEN evidence artifacts; preserve verified retained originals, not a substitute for the missing complete coordinator R2 archive. The two Tokenizers artifacts require independently accepted scanner/environment and explicit expanded acquisition permission. No implied approval from metadata or expiry.
## R2 and OS
- Missing exact coordinator archive CODEN_Coding_Profile_Prebuild_R2_REVIEW_ONLY.zip (expected historical SHA256 bfdab41496d033756517a2327463859c42b951fda4a48a988b2bce9173c7c2cf), or four matching metadata files. Validate using modeb_import_probe.validate_r2_bundle. No reconstructed digest substituted.
- Strict static three-wheel scanner is inspect_r2_static_batch, never module main. Separate independent review of scanner, environment, provenance and legal obligations.
- Existing workflow .github/workflows/factory-r2-native-wheel-inventory.yml at blob 7e95ce966b410eb064fb9cd134adeabf1fd29de0 has historical 131-wheel acquisition code, not the strict three-wheel scope. Do not rerun or broaden its branch guard as a shortcut.
- Existing OS workflow .github/workflows/factory-r2-os-base-evidence.yml at blob 1f03958908142953fe04ea1ad0340743cf91438d is bound to historical branch, immutable Ubuntu image, and review-only flags. A skipped job is not fresh OS evidence. Do not broaden the guard or waive GNU EXPKEYSIG. Independent decision needed for exact distributor-authenticated alternative and Python artifacts.
## Qwen
Existing factory_qwen_tool_schema.py blob 61e62aacd1e492fae97f376f1f75e9c4a6a3f8de validates response shape and digest; it does not attest model identity, origin or real inference. Reuse existing local-only gateway and benchmark after separately approved environment and exact local model identity; do not add provider routers to the critical path.
## Next authorized decision
Independent human reviewers must accept or reject G01 and exact R2/OS scope, with recorded identities, exact hashes and exceptions; operator permission remains separate. Then scoped static acquisition, build, artifact admission, offline install, import, actual process-tree isolation, local inference and separately approved first agent trial. No target downloads, build, install, import, paid API, merge, deployment or live agent in this checkpoint.
