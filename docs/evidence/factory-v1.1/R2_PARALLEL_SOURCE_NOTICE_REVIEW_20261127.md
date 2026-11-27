# R2 source and retained notice cross-check — 2026-11-27
Review only. Baseline a1b10b9dc9822b0996568d29f92bfbb75005c410; #162 open. Exact upstream commit 077f3fad6d31cd852be5c87176e0a93c3b446126. Current CI45910750245 job140218234932: 595 tests, 594 PASS, 1 optional SDK skip, 0 failures, OpenAPI OK; intake45910750266 success; specialized jobs skipped. PR210 independent reviews: 0 at observation.

## Track A: exact source identities
Fetched seven upstream files from immutable commit. Independently recalculated full Git blob SHA-1 from source text bytes (SHA-1 implementation checked against abc standard test vector); each matched GitHub full original blob ID. Replayed exact changed spans from the locally inspected 6522 B combined patch (each old span unique); computed full output blob IDs. All seven match abbreviated target IDs in original patch. In-memory text transformation only, not git apply, checkout, compilation or build. This corroborates patch identity but is not independently approved source-to-wheel provenance.

| Path | Original blob | Result blob |
|---|---|---|
| openhands-agent-server/openhands/agent_server/agent-server.spec | 9cb330d45e4ba8f49259b571167dfd567cc43430 | db92aa7e47f62f87481f0879964d73e9ac39eea3 |
| openhands-agent-server/openhands/agent_server/config.py | a5cddce61e99d6ebf32a1eaca9dc623b19e55151 | 5ed34667ee489539833bd13386b9042e31d9b5ff |
| openhands-agent-server/openhands/agent_server/tool_router.py | c79975f466b2f6fb841ca4b56a863c400f5234b5 | 5a28e3d769cbbd651c311a6dbcc7771612b6e7f6 |
| openhands-sdk/openhands/sdk/observability/laminar.py | d167cc3b8065159d06ddf9763698a244d6de557f | b2291326262c1bcd6680693fad62be5c4211db6e |
| openhands-sdk/pyproject.toml | 1304f0106a4229451882dcf28501df594a921d15 | 92a0a21cbf40b8aff8415f5fbfbc0d96efaa6614 |
| openhands-tools/pyproject.toml | a3dcf37c0cc35f2109282b8e682ed96f8f7d744f | aa80db6e06c55fd8c9842e0fae77ebd150851780 |
| pyproject.toml | 89afbb8a0b5a28b51bf6999fb490bb9b8e0c0c83 | f3132ca9ac05e57fc134e4aefb6def2698940386 |

All four upstream root pyproject files declare setuptools>=84.2.1 and wheel, setuptools.build_meta, matching pinned root build plan. Preserve previous discrepancy and reviewed superseding record requirement; no repin.

## Track B: retained notice evidence
Used original R2 remediation candidate and root build manifest, retained artifacts14952151177 and14953700367. All 126 runtime records match historical selected digest/version/root METADATA hash/notice count; decoded and rehashed 279 retained wheel evidence members (153 recorded notices +126 metadata), zero mismatch. Build plan retained member digests matched decoded bytes: setuptools 32/32, wheel 2/2, packaging 6/6 (packaging overlaps runtime). Historical records are not new actual wheel bytes, complete compiled membership, fresh scan or legal approval. Fastmcp-slim and tokenizers remain notice gaps.

## Track C: direct-Python source scope risk (open)
Source inspection at pinned commit confirms unchanged presets default.py (d70b10f95435faac5d0cfa527ccd15c74a25fe30), gemini.py (e63f5380cf5792422f97bfb6e7fd920f762fc290), gpt5.py (dd3e6275f45b35ffc2d836708415cc4267cab7d0) retain enable_browser=True default in registration/tool selection; explicit false in patched server startup does not prove all call sites cannot enable browser. tools/utils/timeout.py (a0083fede52fce94d9f201a8124ebb9492af04f5) retains func_timeout import, tom_consult/__init__.py remains tracked, and multiple Laminar imports remain outside the replaced predicate. PyInstaller excludes cannot be used as proof for direct Python root wheels. No claim that these paths actually execute or are exploitable in the candidate. Independent reviewer must verify built wheel contents and explicit allowed entrypoints, fail-closed negative reachability/import checks under admitted isolated runtime; if requirements fail, separate reviewed source amendment and full re-pin, not hidden mutation. No actual build, import, inference, agent, package acquisition, merge/deploy or approval. release_authorized=false.
