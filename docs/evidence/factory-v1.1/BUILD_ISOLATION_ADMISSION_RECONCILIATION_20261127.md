# Build and isolation admission — evidence reconciliation (2026-11-27)
Status: SYNTHETIC_ISOLATION_EVIDENCE_RECONCILED_NOT_ADMITTED. Baseline 2912200b8e290d71c82a64d0ad83ca37f03ebb63, PR210 draft, zero independent reviews at observation. Prototype45910965327 and intake45910965322 success; three specialized jobs skipped.
## Eight original artifacts actually downloaded and checked locally
All exact historical SHA256 and CRC matched; 52 members individually hashed. Cross-checked job conclusions and kernel-test assertions in retained logs. No new target execution.
| Run | Artifact | SHA256 |
|---|---|---|
|45493026390|14967367077|aa25f9f7be0ec9ef86da2ccc9535e8dbb1cb46dd8ea425b36f3f715dde2c7afa|
|45510585594|14975192779|52e4f3f45c8b2b625a95e89d68485a77b2e4f500d7d4ab1313bcbbd04e4f9a99|
|45511255281|14976455437|8cc445118ac8c937b24b2dca92ab4e00db591512bb51bd820ed03ba7a1d18d35|
|45511943846|14975382724|cbfcd48b3f9987237d279e008797804141a6f4d9b9961d9515399f540bfcc1e7|
|45713571118|15068232785|425c3bc544074eaccd39863a07e190c10b34b81f4f4df584025a618747066bb6|
|45717558261|15071365003|fdb739bf0b121bc414db8a7410f3e30d21f15f34bf4464cf8cd20159bcaf3bc2|
|45669078687|15048193186|b881d657df2edec67ebe51d444a2ec3f11a49cf9d5ee9426e1ed62a68deec955|
|45524219103|14982625325|a1c96f89ca67687511ad29c51ccb87f01e41275188803da5dcd3a25e317dcff3|

## Newly reconciled decisive evidence
Full synthetic build watchdog run45524219103 job138903408690 SUCCESS, elapsed601s, configured600s, container exit -1 after stop, tracked identities and resources_removed. Earlier 60s-only statement superseded for synthetic watchdog. 960MiB (1006632960 bytes) scratch, 61440 inodes, matching exact root build plan's scratch and duration; lower than approved 1GiB/65536 inode maxima, not an increase. Placeholder bytes911501982 and inodes19174; actual sampled used890144 KiB, free92896 KiB (95125504 bytes), used19180 inodes. Dense fixture is not actual build peak or per-file allocation. Separate S18 artifact shows parent+child same cgroup and workspace/HOME/TMP same tmpfs; allocation1006632960 bytes, extra write ENOSPC errno28, cleaned. This closes the isolated synthetic 600s watchdog and shared scratch overflow evidence gaps, not aggregate candidate admission.
OS-only synthetic 180s lifecycle completed181s; three mount negative cases rejected, one ordinary writable scratch and nine expected pseudo/device mounts, kernel resource accounting remains incomplete. Split UID containment and five broker cases match stored receipts; broker fixture expiry returns timeout, not grant_expired. No proof of actual SDK or Qwen. Local analysis container has read-only cgroup2 mount and no Podman/Docker executable; cannot reproduce full kernel boundary here.
## Remaining executable admission prerequisites (no implied approval)
1. Independent designated security/legal reviewer: exact source patch/roots, build-tool and Python vendored/static notices, R2 wheels including fastmcp-slim/tokenizers, reviewed glibc expiry disposition or current valid authorized certificate. Do not self-approve or rerun unchanged expired signatures. PR reviews zero.
2. Actual isolated runner preflight: aggregate ordinary and auxiliary writable storage/IPC/PTY/device accounting; exact read-only staged inputs/output boundaries, CPU/RAM/PID/no-swap/timeout and all-descendant cleanup under one measured candidate boundary. No privilege or quota expansion. Actual build peak unknown; current model reserve is not a measurement.
3. Only after independent prerequisites: one separately scoped OS-only trial using exact two signed-index-bound packages, no network, preserve maintainer scripts, verify exact package delta and rescans. No build attempt consumed. No host updates.
4. Exact admitted interpreter and OS plus exact 4 root source identities and 3 build tools; one non-agent offline build under original conditional approval. Capture output wheel hashes/RECORD/METADATA/SBOM/notices/source identities and actual resource use. Subsequent installation/import and real Conversation have separate gates.
Operator approvals #162 comments7144392543 and7147469552 remain conditional, both attempts unconsumed. No fresh runtime/OS install, build, SDK import, inference or agent; #162 OPEN. execution_authorized=false, release_authorized=false.
Local evidence package CODEN_Build_Isolation_Review_Evidence_20261127.zip 17467 B SHA256 090262fab2b69ae77f6ad8f1e475da0e7fda5b2cc112d0eaf776c540b0bed233 (8 original ZIPs + new JSON). JSON SHA256 598115205e45e26c601006b31ec44ce5bbb779c96f24e57a2e6779ea13843e9b. One auxiliary mount receipt lacks release field; not interpreted as authorization; all explicit fields false. No binary committed.
