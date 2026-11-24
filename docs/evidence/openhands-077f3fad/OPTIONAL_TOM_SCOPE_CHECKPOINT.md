# Optional ToM scope checkpoint — 2026-11-24

Review only. Issue #162 OPEN. release_authorized=false.

Run 45459482500 PASS. Downloaded artifact 14951852741; independently recomputed ZIP SHA256 fcce51ed192fe4679c09e6d33dfea29fc848aee5a0b3c83a0038ec05fcffbcdf.
Verified scope-review.json: original 128 -> optional-ToM 126 non-dev registry names; removed json-repair and tom-swe; no added names and no lock name/version changes. The lock still contains 202 records including optional ToM. Candidate lock SHA256 6bcb3f75c6a1803e3c47cad87c4881c5e250431b876d79e1deec2f82bd1a4301; manifest patch 03975e58f3606f67a9458eae3a28a4076d58296805ab20a537986f03fbe8cf50; non-dev export acb0247cbcce90314ea3dc34cfff5cde5c6ae258c7bb2e32a607fe3a3c320c66. No install, build, runtime scan or approval.

Compared all 126 exported names to wheel review artifact 14952151177 in local container: 126 matching collected records. Three lack notice text in wheel (fastmcp-slim, jiter, tokenizers); upstream release-ref evidence exists, exact artifact linkage and native review remain. Agent-client-protocol lacks license declaration but wheel has license text. ToM-SWE, k8s-agent-sandbox and streamlit missing-notice cases are outside this non-dev export; no implied clearance of optional/dev artifacts.

Expanded Trivy 210/210 zero findings applies to earlier lock and discovered vendor identities, not the new installed runtime. Names/versions unchanged at lock level; actual runtime/build closure still needed.

Pinned upstream PyInstaller spec blob 9cb330d45e4ba8f49259b571167dfd567cc43430 uses collect_submodules on all openhands.tools and collects browser JS data; default server config enable_browser=True at blob a5cddce61e99d6ebf32a1eaca9dc623b19e55151. Merely changing requirements is insufficient. Before approved candidate build, explicitly scope PyInstaller collection/exclusions and startup feature registration; ensure audit controls remain. Build frontend/backends and native libraries are separate scope, not covered by 126 registry runtime candidates. Next review materializes only exact selected-wheel records and build-tool metadata, not wheels or a running installation. No --no-deps overlay or stock admission.
