# R2 OS base library presence review
Baseline 1126a0017c079aa094008c8ee95636a60e5f6f89, run 45493938376 success. Artifact 14967052943, local ZIP SHA256 b198cb509b752fb083cbfcd44ec85a3a7640aceb1ca26c5457be63350671d05d, four entries, CRC clean. Base docker.io/library/ubuntu@sha256:9a04f13b3f80ef056361e30868593b1cfd2279fe19e4081cb93a90bf56819d6a amd64. All ten required external library names found, actual canonical file hashes recorded, all ten canonical paths have dpkg-query owners. Failed lookups for /lib alias paths are not missing files; /usr/lib canonical paths matched. No additional packages needed for these ten names.
| Package | Version | Library count |
|---|---|---:|
| libc6:amd64 | 2.39-0ubuntu8.9 | 7 |
| libgcc-s1:amd64 | 14.2.0-4ubuntu2~24.04.1 | 1 |
| libstdc++6:amd64 | 14.2.0-4ubuntu2~24.04.1 | 1 |
| zlib1g:amd64 | 1:1.3.dfsg-3.1ubuntu2.3 | 1 |
Next collect provider ELF dynamic and version-definition evidence, copyright notices and security evidence for exact packages. Presence is not symbol compatibility, recursive loader closure, provenance, legal or vulnerability admission. No source build or candidate execution. Conditional approval remains unconsumed, issue #162 OPEN.

## Independent provider-version reconciliation — checkpoint 2026-11-25

Reviewed immutable head `6eba10e3874b027ebb30908ddd9df2c0772ffc93` without executing candidate binaries.
- OS run 45507299861 / artifact 14974255454, locally rehashed ZIP SHA-256 `52131ced3f3aeb16c8d3129d247b54a171035ea69a6a74c0689deb97f0538749`, CRC clean.
- Python run 45507299870 / artifact 14974390425, locally rehashed ZIP SHA-256 `a30f895a1bb10f6924beaf474857304ce831d1f9c6d950c4a127e523ef75c4fc`, CRC clean.
- Wheel artifact 14963367194, locally rehashed ZIP SHA-256 `90c1a2d1dbbccdd09ea2a1458ac0bf2a91e5620ad1050e01799ae89e23887de4`, CRC clean; all 131 records' names, versions, wheel digests, native records and notice paths identical to artifact 14957444282 (ZIP SHA-256 `f1ec9f3d0b9ed6cf3c8e2d494b589b1ed0bd4a7a0d3e151c9b4b09e50eee3b46`).

| Static check | Result |
|---|---|
| OS provider SONAME records | 10 unique |
| Provider-to-provider DT_NEEDED edges | 14/14 names represented |
| OS provider version-need references | 56/56 exact version names present in corresponding provider version-definition tables |
| OS package copyright notices | All four collected; no NOTICE_MISSING marker |
| Wheel ELF records | 75, all x86-64; 233 DT_NEEDED references |
| Python ELF records | 9; 32 DT_NEEDED references |
| Consumer DT_NEEDED basename candidates | No missing names in inventoried provider sets; not actual resolution |
| Non-ELF candidate flags | 8 PE candidates in setuptools wheels; 6 PE candidates and 2 static archives in Python archive |
| Wheel notice gaps | fastmcp-slim 4.2.0 and tokenizers 0.23.2 |

Method: parse provider readelf -W -h -d -V evidence by SONAME, extract NEEDED edges, compare every version-need File/Name pair against that provider's version definitions; compare Python and wheel NEEDED basenames against corresponding inventoried basenames and OS SONAMEs. This does not prove individual exported symbol availability, runtime search order, transitive consumer binding, or static component membership. Consumer inventories currently lack version-need records, so full consumer symbol compatibility is BLOCKED. Absolute /tools/deps/lib paths remain under review. PE magic is not proof of executable format or runtime use; review separately.

Expanded regular Python bytes 386276509 plus expanded wheel member bytes 301372095 = 687648604 bytes (static inventory only). Not a measured installation or peak build footprint; do not infer 1 GiB capacity PASS. Signed release inputs remain unverified (see PR conversation); legal and vulnerability admission remain open. Next: collect version needs for all exact consumer ELF records using static inspection, compare to corresponding provider versions, then separately verify actual symbol names and loader search semantics. No build attempt consumed; no installation, network-enabled agent, deployment or merge. Issue #162 remains OPEN. `release_authorized=false`.

## Exact Ubuntu vulnerability scan and package coverage — 2026-11-25

Reviewed immutable head `bccdd0fb3e7b58a7634230e028bdddce802d5e09`. Trivy 0.69.3 remote image vulnerability report from run 45509556451, artifact 14973763939, created 2026-11-24T23:23:44.190070629Z. Independently rehashed the downloaded ZIP as 462f9f45e2456601e0810e7d8917fe65147ff22dd8a9b8ae22e65134ba577f28 (matches GitHub; CRC clean). Reopened previous independent dpkg/base evidence artifact 14973719758, hash 3b595d0b8ca362457d577ae6485ddb010afe77c89296a6f9392a4c9a15feff4a, CRC clean. Exact image digest 9a04f13b3f80ef056361e30868593b1cfd2279fe19e4081cb93a90bf56819d6a and image config ID 2b147973fd863c93ced60f325461fe0e262b91317b008e6a2d961f13e81af0e4 agree across the Podman and scanner evidence; architecture amd64, Ubuntu 24.04.

Independent coverage reconciliation: parse dpkg-query TSV name/version/architecture (strip the multiarch suffix from binary package name only); reconstruct Trivy Debian versions from Epoch, Version and Release (retain nonzero epoch and release). All 92 exact triples matched; zero missing or extra. No vulnerability suppression. Results: 35 package-finding rows (20 unique CVE IDs), 30 MEDIUM rows (17 unique IDs), 5 LOW rows (3 unique IDs), zero HIGH/CRITICAL/UNKNOWN rows. Twelve rows have FixedVersion (six unique CVEs in both libc6 and libc-bin); 23 rows have no FixedVersion and are marked affected in report. Fixable rows: CVE-2026-18374, CVE-2026-84243, CVE-2026-8674, CVE-2026-86805, CVE-2026-95818, CVE-2026-97399. Installed glibc 2.39-0ubuntu8.9, scanner-reported fixed version 2.39-0ubuntu8.12 for both packages. No findings reported for the other three required provider owners libgcc-s1, libstdc++6, zlib1g. Findings are scanner observations at report time, not proof of exploitability, current upstream status, or absence of vulnerabilities.

Decision: base high/critical scan criterion met for this exact report; security admission remains OPEN. Prefer review of a newer official Ubuntu 24.04 amd64 image resolved to an immutable digest, independently re-scan and compare exact package identities, ten library bytes, interpreter alias and ABI evidence before considering replacement. Do not silently run apt upgrade on the frozen base, suppress remaining medium/low rows, or inherit previous provider hashes/approval onto a changed image. Document risk disposition for all remaining findings and review bundled Python/Pillow/Rust components separately. No candidate install, build or execution; attempt not consumed; issue #162 OPEN; release_authorized=false.
