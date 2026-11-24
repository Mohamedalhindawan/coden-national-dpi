# OpenHands runtime closure and watchdog evidence — 2026-11-24

Status: partial runtime inventory; independent review still required; not an admission or release.

## Watchdog — observed PASS

At exact head e666a33fabf7d10bd522cc060f59820fbc706aea, [watchdog run 45446327401](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45446327401) succeeded. Downloaded artifact 14945873205; independently computed ZIP SHA-256 e683279cc0e6da1375b56c6b25ee954079afb87f2053b9c6ec83703b0c51f800 matched GitHub. Receipt: 60-second configured deadline, observed 61 seconds, 3 observed original host process identities gone, container stopped, cleanup receipt container_and_volumes_removed. Real signed server and fixed operator-owned sleep child only. This does not prove SDK-created child cleanup in an actual conversation. Prototype 45446327669: 283 passed, 1 skipped, 284 run.

## Direct static inspection of the actual frozen binary

Downloaded original [source product 14937864045](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45431783950/artifacts/14937864045). ZIP SHA-256 aff71bd1eec916e137187e8a49084a7fe9bd6f51432d6ac5dacde7473b0e6775 matched provider metadata; extracted binary bytes in memory and independently checked SHA-256 5ad5fa2bb86256b510df3bfbbd9653fbc60a243ea744a579d3ca4c6fd9e91cf3. No binary executed, no embedded module imported; inspected PyInstaller CArchive records and deserialized only its PYZ index. Index is not a package-to-file closure or complete SBOM.

- CArchive: 4,138 records, including 115 native/binary records and 3,981 data records.
- PYZ: 11,344 module names across 296 top-level names; Python 3.13 archive.
- 32 distributions with embedded dist-info METADATA.
- browser_use_sdk: 102 PYZ entries plus browser_use_sdk-2.0.15.dist-info/METADATA and RECORD; no dedicated license entry observed in that dist-info directory.
- lmnr_claude_code_proxy: one PYZ entry plus native lmnr_claude_code_proxy.cpython-313-x86_64-linux-gnu.so.
- Other observed namespaces: acp (26), jsonref (1), openhands (575), google.protobuf (37).
- Medium-vulnerability relevant namespaces present: multidict (4), opentelemetry (153; embedded opentelemetry-api 1.39.1 metadata), jwt (11), setuptools (116). No mako namespace in PYZ; this alone does not prove absence from complete runtime. Namespace counts are not distribution version proofs.

The two unresolved license packages are **actually bundled**, not merely build-only. Disabling their features is insufficient to establish redistribution rights. Obtain authoritative exact artifact rights or verify a supported reduced build excluding them and its transitive closure. Do not assume omission is safe, remove required code without compatibility evidence, or approve the frozen artifact.

Local full inventory JSON SHA256 e3112c9993527f5f051a5d3a03c0f5177a0a3cc66085e101b450729d68e91b01 and CArchive index SHA256 4fa3891100da378a60f27040dee13e110ac0a6b64d3278d394b38858f49149d7 were generated during static inspection; these full indexes are not stored in this Git commit. This file preserves verified findings and source references. Next: map namespace/native data to exact locked distributions, independently verify rights and rebuilt artifact/scan, then demonstrate authenticated Qwen3 link under operator isolation; keep #162 open. No SDK Conversation, generated command, paid API, merge, or production approval.
