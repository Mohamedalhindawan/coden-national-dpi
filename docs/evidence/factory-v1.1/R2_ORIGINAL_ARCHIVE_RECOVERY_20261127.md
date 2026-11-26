# Original R2 prebuild archive recovery — 2026-11-27
Review-only. User supplied original CODEN_Coding_Profile_Prebuild_R2_REVIEW_ONLY.zip; locally read exact bytes, 197383 bytes, SHA256 bfdab41496d033756517a2327463859c42b951fda4a48a988b2bce9173c7c2cf matches historical checkpoint. All 16 members read; ZIP CRC clean; all 15 member digests in MANIFEST.sha256 independently recomputed and matched. Original archive is recovered, not a reconstructed substitute. No executable package acquired or run.
## Static reconciliation
- Exact lock SHA256 93447ba7c43d7c8bffe1bb66d99abad1eaffcbd0d11fe1ef5bb776c7155998a3 and export 0663c7b1e0336440b948d5dd7b297d83da2025107524fbe2f3891de606da4a7c match internal build-input references.
- 131 unique selected wheel metadata rows, each URL/name/version/hash matches exactly one lock entry. 126 runtime names, six build tool names, overlap packaging. Four additional runtime roots: openhands-sdk, openhands-tools, openhands-agent-server, openhands-workspace. Retained closure reports 252 runtime edges and six build edges, no issues or unreached; not a new traversal of installed packages.
- Retained SBOM component counts 210 Python and 249 Rust; prior scan reports zero findings in that scope. No fresh vulnerability scan, compiled membership or runtime proof. Two runtime notice gaps remain fastmcp-slim and tokenizers.
## Important discrepancy (do not silently repair)
inputs/build-inputs.json source_patch_sha256 is 03975e58f3606f67a9458eae3a28a4076d58296805ab20a537986f03fbe8cf50, but bundled source/coding-profile-source.patch SHA256 is 0609700a143b3fc8b0439f7ff2c74b75aa41c220fa9ba4294db35bac54b8f70f (matches internal MANIFEST.sha256 and historical packaging-source patch pin). Archive integrity PASS, cross-reference consistency FAIL. Establish exact patch history and intended build identity before use; no silent digest substitution.
## Later admission inputs still missing
Original prebuild archive predates three separately pinned Mode B metadata files. None of the 16 member digests matches:
- installation manifest 35147ce68c413cae772c9afe3782e0f3e3e07c7e9e5ba12a8324b199c7fb98f2
- import contract c22cbd20bf72167164dbfbb04a5912f42dbe849c6738d30899e2841911099157
- root build manifest f396d96fe5e8f3cf1f38c2c786f749929f4bc3cc40cd9470a590c43facb9d19b
Earlier archive recovery assumption that this ZIP alone would satisfy all four current pins is corrected. Do not substitute inputs/build-inputs.json or evidence/metadata-closure.json (different schema/digest). Exact later source records or separately reviewed superseding contract required. No four-file preflight PASS claimed.
Baseline b8e4b3aafd0115ae48d20e156e81a2a34843e5d4; #162 OPEN, R2 REPAIR_NOT_ADOPTED. No build, install, import, inference, agent run, paid API, merge or release. execution_authorized=false; release_authorized=false.
