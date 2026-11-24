# R2 Pillow embedded BOM reconciliation and bounded build decision
2026-11-24 | REVIEW ONLY | release_authorized=false | Issue #162 OPEN

## Evidence verified
Run 45474104833 PASS. Artifact 14956229625 downloaded, ZIP SHA256 e8b53c77b70683175c644fb8534117d566bc24d8128561246e12b471ecdb4dc1, CRC clean, 6 members. Exact wheel SHA256 5f56499c1a74d2b862beb0c33b8016f99d095858455df9d21583bbbc1c15b582. All 138 hashed RECORD members verified in CI. Independently matched all 26 Pillow ELF paths, sizes and hashes from native inventory artifact 14958960603 to extracted RECORD, and rehashed both BOMs and matched RECORD. Earlier single-BOM assumption failure 45473843878 retained.

- auditwheel.cdx.json: SHA256 8267ecfe860ec140d65b7dad60c7951cc139a425de158b14f90a3adadec4eb32, CycloneDX 1.4, 2 component records (Pillow root identity repeated plus libXau 1.0.9-3.el8 RPM).
- pillow-13.0.0.cdx.json: SHA256 fe1ca6e3a4f73e7018a3805a75a19377453f342d203712f37387ad6ee853fd44, CycloneDX 1.7, 24 component records, including optional/excluded and vendored source declarations. Do not sum counts as distinct installed components.

## Bundled library family reconciliation
18 independently inventoried SONAMEs correspond to 14 library families. 13 SONAMEs map by name/family to 10 producer-BOM families; five SONAMEs across four families absent from both embedded BOMs have release manifest corroboration. This is name-based attribution, not reproducible build proof or exact binary version verification. Source manifest .github/dependencies.json at official Pillow tag 13.0.0 git blob 989997da27b88936a9b8a5955fa67bf9441ad45a.

| Family | SONAME count | Producer-declared version | Evidence |
|---|---:|---|---|
| libXau | 1 | 1.0.9-3.el8 | auditwheel RPM |
| libavif | 1 | 1.4.2 | Pillow BOM |
| Brotli | 2 | 1.2.0 | manifest only; absent from both BOMs |
| FreeType | 1 | 2.14.3 | Pillow BOM |
| HarfBuzz | 1 | 14.5.0 | Pillow BOM |
| libjpeg-turbo | 1 | 3.2.0 | Pillow BOM |
| Little CMS | 1 | 2.19.1 | Pillow BOM |
| XZ/liblzma | 1 | 5.8.4 | manifest only; absent from both BOMs |
| OpenJPEG | 1 | 2.5.4 | Pillow BOM |
| libpng | 1 | 1.6.58 | manifest only; absent from both BOMs |
| WebP (includes sharpyuv, demux, mux) | 4 | 1.6.0 | Pillow BOM family |
| libtiff | 1 | 4.7.2 | Pillow BOM |
| libxcb | 1 | 1.17.0 | Pillow BOM |
| Zstandard | 1 | 1.5.7 | manifest only; absent from both BOMs |

Pillow BOM optional libimagequant GPL-3.0-or-later is not observed as bundled SONAME; upstream pyproject disables imagequant. FriBiDi LGPL-2.1-or-later is optional runtime-loaded via shim; lack of SONAME does not prove absence of dynamically loaded or statically linked code. pybind11 marked excluded; zlib declaration does not resolve libz.so.1 to an installed version. Preserve actual notices. Source manifest version strings are not native security scanner coverage. Do not invent PURLs, declare these versions vulnerability-free, or infer final compliance.

## Decision boundary: isolated build experiment, not live agent
Static review now supports a finite list of unresolved conditions, not a request to repeat all previous checks. Operator must approve specific non-agent experiment separately from live Conversation (Gate 0, GROK_MODE_GATE_REVIEW.md). Proposed scope: pinned R2 lock and four modified source packages, exact 131 registry artifacts, immutable interpreter/base, read-only staged inputs, no network during build, no credentials, no production mounts or privileged socket, bounded CPU/RAM/PIDs/disk/time, operator-managed rootless boundary, independent timeout/cleanup evidence. Synthetic envelope previously used 2 CPU, 2 GiB RAM, 128 PIDs, 128 MiB scratch, 8192 inodes and 60 s; these limits are not proven sufficient for a real build. Do not silently enlarge limits or spend money. Measure staged input size and propose explicit bounded build capacity before execution. Preserve failures. No actual install/build authorization yet; license/legal obligations (notably missing notices, native and static Rust dependencies) require review before use/distribution. No live Conversation until post-build runtime SBOM, imports, isolation and separate human approval. No main merge or deployment. All PRs remain drafts.
