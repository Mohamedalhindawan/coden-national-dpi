# CODEN Codex tooling audit · 2026-11-20

## Revisions and observed behavior

| Source | Evidence | Status |
|---|---|---|
| main at `921b2b848366a2a7a368660d5460ca5e6d712ba3` | 76 tracked files. Static Arabic Tamam app, draft YAML API, ADR template/index, capability register, technology radar, 11 visual skills, Python contract tests. | Implemented demo and documentation. Governance and full factory lifecycle in the master playbook are target architecture. |
| [#117](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/117) at `c49737b01ee679e95320fdb931fc807c7a05c963` | 87 files. Six Codex skills and four TOML role descriptions. 11/11 tests passed locally on the untouched base. | Basis of this PR. Profile recognition and agent execution on mobile remain unverified. |
| [#26](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/26) at `2c775421baa89a5dc89d34a2777d90dad4690a8f` | Enterprise skills, DAG, queue, workers, recovery, FinOps, simulated model gateway, receipt-scoring benchmark. Inspected gateway code and ran its eight tests from an isolated export. | 8/8 passed. Gateway filters by classification, capability, context and estimated cost. No provider execution. Other modules inventoried, execution unverified here. |
| [#50](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/50) at `d24f95a7ffe801332017f5580c801ee567712e80` | Additional playbook skill catalog. | Overlap with #26 and project entry points in #117. Link accepted material after governance review. |
| [#124](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/124) at `26ba063e8c444f80cf6f4bf5b165a2169302db0a` | Builds on #116 intake and #118 offline queue. Three local stages, SQL QA, isolated in-memory fixtures, bounded attempts, read-only Codex artifact adapter. | 45/45 tests passed on this separate branch during planning. Adapter exercised with mocked HTTP. Real model execution unverified. |
| [#120](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/120) at `6966e775dbb81f9c20a8213254039fd188eeb01a` | Adds per-ref cancellation and 15-minute timeout to existing workflow. | Pending branch. Keep this PR independent of its workflow edits. |

Enumerated 112 remote branch tips before publishing this branch. Searched their trees for MCP, LiteLLM, gateway and proposed tooling filenames, and searched Python, JS/TS, TOML, JSON, YAML, requirements and Dockerfile content for LiteLLM and MCP server configuration keys. The sole matched configuration-format path was the technology catalogue. The model gateway implementation appeared on three branches. No active LiteLLM server or repo-configured MCP integration was evidenced. Operator-local installations and running external infrastructure were outside this inspection.

## Controls and gaps

The existing read-only GitHub workflow runs Python discovery and validates OpenAPI with validator 0.7.2. The Actions use major-version tags. Full action SHA pinning and a secret-scanner gate remain open. The new tests run through the existing discovery command. CI diagnosis is manual and reads GitHub. Treat log contents as untrusted and redact before sharing. The playbook requires synthetic data, test-first development, dedicated branches, human approval for spending and sensitive actions, and human review before merge. No workflow, deployment, account permission or secret changes are part of this PR.

The earlier free-tool audit tracks proposals, including potentially stale quotas. The new registry records pinned source, licensing, selection, and test evidence. Usage telemetry for previously configured skills is unavailable. Dormancy cannot be established from filenames. [Earlier audit](FREE_AI_TOOLS_AUDIT.md) · [Registry](codex-integration-registry.md)
