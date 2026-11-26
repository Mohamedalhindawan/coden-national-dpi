# R2 patch identity reconciliation — 2026-11-27
Baseline bf9f2b2f39e1ff2fc4158d24d3a3200085ad56b1. Review-only; no change to original archive, build input receipt, pins or admission gates.
Freshly downloaded original historical artifacts 14951852741 and 14952123267; local SHA256 checks:
- 14951852741: fcce51ed192fe4679c09e6d33dfea29fc848aee5a0b3c83a0038ec05fcffbcdf, CRC clean, seven members. optional-tom-manifest.patch 1737 bytes, SHA256 03975e58f3606f67a9458eae3a28a4076d58296805ab20a537986f03fbe8cf50.
- 14952123267: 735c574275f306a143ef2a02d6e394a0d79acd842a671b2ba6af11fa337fa6e7, CRC clean, three members. coding-profile-source.patch 6522 bytes, SHA256 0609700a143b3fc8b0439f7ff2c74b75aa41c220fa9ba4294db35bac54b8f70f. Exact byte equality to user-uploaded original R2 ZIP member. Historical packaging-contract.json also matches its pinned hash b18e71b08ef6be21b3f7bee5af17618125ad3f6506b9f32a767fe2d66918460e.
Parsed both raw unified diffs at line-anchored diff --git boundaries; all three original path sections are byte-identical to corresponding sections in the combined seven-path patch (SDK pyproject.toml, Tools pyproject.toml, root pyproject.toml). Four additional sections: agent-server.spec, agent-server config.py, tool_router.py, SDK observability/laminar.py. No patch application or source execution in this checkpoint.
Cross-reference discrepancy explained: old manifest-only patch pin retained in inputs/build-inputs.json while combined patch bundled. Historical REVIEWED_BUILD_INPUT_RECEIPT.md explicitly identifies old patch; PACKAGING_METADATA_CLOSURE_CHECKPOINT.md explicitly identifies combined patch. Proposed disposition for independent reviewer: preserve both identities, distinguish resolver manifest-only patch from combined source build patch, apply combined patch once only when authorized. No silent re-pin, no final build admission. The original archive's mismatching cross-reference is not silently corrected; reviewed superseding build input record still needed.
Three later exact metadata file records located in Library (raw-byte materialization denied):
- r2-offline-installation-manifest-UNAPPROVED.json (100812 B)
- modeb-r2-import-contract-UNAPPROVED.json (29440 B)
- root-wheel-build-manifest-UNAPPROVED.json (12515 B).
Request original uploads, verify SHA256 against existing modeb_import_probe.py pins. No substitute or hash claim before access.
Prior exact baseline CI45909988415 and intake45909988394 success; specialized model/legacy acquisition jobs skipped. No new build, install, import, model or agent; #162 OPEN, release_authorized=false.
