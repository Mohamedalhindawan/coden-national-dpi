# R2 Python and wheel dynamic dependency reconciliation
Baseline 13eb44d95d245a1528eae6467720cb91f2969ecd.
CI 45493640893: 389 tests, 388 pass, 1 skip, all three ELF tests pass. CI 45493641016: Python ELF review success. Artifact 14966887924, SHA256 76a6664b6aec5f1b60d1d1d7ff91f51a5748d94d5bc594ff749ae059b0d07d54, five entries, independently rehashed and ZIP CRC clean. All nine records match original Python native inventory by path, byte size and SHA256. All nine readelf Machine records are x86-64. Wheel evidence artifact 14963367194 rehashed SHA256 90c1a2d1dbbccdd09ea2a1458ac0bf2a91e5620ad1050e01799ae89e23887de4, CRC clean; 75 wheel ELF records. No execution of candidate binaries.
## Name-level reconciliation
Python archive contains libtcl9.0.so and libtcl9tk9.0.so, referenced by _tkinter; no SONAME in these two records. libpython3.so DT_NEEDED contains literal $ORIGIN/../lib/libpython3.13.so.1.0, candidate file exists. No loader resolution proven. Tcl/Tk search-path records contain /tools/deps/lib (one duplicated colon entry), absolute build path must be considered under isolated runtime; no claim of exploit or harmlessness.
Combining Python and wheels yields ten remaining conventional OS library names after subtracting wheel SONAME matches and the three archive-local name/path candidates:
- ld-linux-x86-64.so.2
- libc.so.6
- libdl.so.2
- libgcc_s.so.1
- libm.so.6
- libpthread.so.0
- librt.so.1
- libstdc++.so.6
- libutil.so.1
- libz.so.1
Next check exact immutable Ubuntu base inventory and package owners. This is only name-level reconciliation; no recursive OS closure, symbol version compatibility, RPATH/RUNPATH behavior, static membership, vulnerability or legal admission. No build attempt consumed. Issue #162 remains open.

## Consumer version-definition reconciliation — 2026-11-25

Immutable head `827f0262b263c83d511b5e7a6ab9eac4bb32d0f2`. Prototype run 45508319174: 390 tests, 389 pass, one skip, new consumer version evidence regression test PASS. Static inventory run 45508319217 success, OS base run 45508319254 success. Independently downloaded ZIPs, matched GitHub-reported SHA-256 and checked ZIP CRC:
- Python static artifact 14975205345: `3167e6c5e7ee0eede88abc07da2a2cd82dc7217fcc336ecf121a65799da3c9d2`.
- Wheel inventory artifact 14972739144: `66bc9a3c03cb322a19a233c6178e307f7420402c36b8ef2641f004452e059727`.
- OS base artifact 14973698809: `a1650831eaf45e2d86c5b961cc5b963a16f013915cffcc9e992d4c77501215c3`.

| Check | Observed result |
|---|---:|
| Python ELF records | 9 |
| Wheel ELF records | 75 across 131 exact candidate wheels |
| Python version-need references | 96/96 matched |
| Wheel version-need references | 366/366 matched |
| Total consumer version-need references (counting references per file, not distinct symbols) | 462/462 matched |
| Missing or ambiguous providers for version-need references | 0 |
| Candidate provider names, including non-SONAME basenames | 93 |

Method: parse readelf -V definition and need sections; validate each File block count against its Name entries; compare exact (File, Name) pairs to version definitions of a uniquely named provider in the combined OS, Python and wheel inventory (SONAME preferred; basename fallback for records without SONAME). One duplicate candidate basename, SQLAlchemy _util_cy.cpython-313-x86_64-linux-gnu.so, appears in engine and sql paths; no version-need reference selected it. This is a static version namespace match, not a loader search-order or symbol-level resolution proof. Actual undefined symbol/export pairs, RPATH/RUNPATH behavior, static membership, source provenance closure, legal and vulnerability admission, and peak build footprint are still unverified. Do not treat these results as permission to run the candidate. No build attempt consumed or candidate binaries executed in this review. Issue #162 OPEN; release_authorized=false.

## Dynamic-symbol inventory reconciliation — 2026-11-25

Exact reviewed head `0f0c217d17bb1504956909b8f1eb2ff76a014a35`. Prototype run 45508686569: 391 tests, 390 pass, one skip; dynamic symbol evidence regression PASS. Static inventory run 45508686542 and OS base run 45508686498 succeeded. Independent local ZIP SHA-256 and CRC checks passed for all three artifacts:
- Python 14973762981: `06f4745cfe84facb5c3f1d96e2f5d88ed6fe9204d6c05c74ca889688faeaccbb`.
- Wheels 14974722081: `e83e66dceb324f76b6e00192a2619628260896a40dc97c2a13e0c1d3c675d1e9`.
- OS 14974566552: `400d0a6fc386ae8635673afcb3129ce2f5c6befc91c0620b6762bd8f38ab68bb`.
Python and wheel inventories exactly equal the preceding artifacts 14975205345 and 14972739144 after removing only the added dynamic_symbols fields.

| Count (per-object named UND symbol entries, not unique names) | Python (9) | Wheels (75) | OS (10) |
|---|---:|---:|---:|
| Named undefined entries | 1931 | 9375 | 302 |
| Versioned | 1706 | 2599 | 270 |
| Exact named provider exports same symbol/version | 1409 | 2269 | 270 |
| Alternate inventory export only | 297 | 330 | 0 |
| Versioned missing from all exports | 0 | 0 | 0 |
| Unversioned GLOBAL with candidate | 196 | 6518 | 0 |
| Unversioned WEAK with candidate | 4 | 27 | 0 |
| Unversioned WEAK without candidate | 25 | 231 | 32 |

All 627 alternate-only versioned entries map from compatibility DSOs to matching libc.so.6 exports: libpthread.so.0 573, libdl.so.2 31, librt.so.1 17, libutil.so.1 6. This is a candidate export match, not proof of runtime binding. No versioned entry had an ambiguous or absent named provider or an unmapped version index in the inventory. Unversioned GLOBAL candidate absence: zero across the three groups. Weak missing entries remain explicit (256 among consumers, 32 among OS providers); no blanket claim of safety.

Independent local method: parse each readelf .dynsym table with complete contiguous row count validated against declared table size; skip anonymous null entry; map each named versioned UND entry via numeric version index and exact version name in the object's GNU version-need table (validate each File block count); select unique provider SONAME or basename when SONAME absent; compare exact symbol and version to defined GLOBAL/WEAK/UNIQUE DEFAULT/PROTECTED exports. For alternate-only matches record separately any exporting object. For unversioned UND entries test candidate inventory exports with same name and unversioned or default-version export. No relocation, type compatibility, namespace, loader ordering, visibility context, absolute search path, or actual binding verification is implied. Local analysis is an independent diagnostic, not a new production test or authorization. Next: reconcile loader search paths and scope, especially compatibility DSO fallback and Python extension global symbols; finish supply-chain and legal admission and capacity gates. No candidate execution, no build attempt consumed, no main merge or deployment. Issue #162 remains OPEN; release_authorized=false.

## Static loader path candidate review — 2026-11-25

Review baseline `f035bd010743ca731daea86e14dd54daa5e912ed`. Reopened the three dynamic-symbol evidence ZIPs 14973762981, 14974722081 and 14974566552; SHA-256 matched the preceding checkpoint and each ZIP CRC check passed. No download of candidate binaries, loader invocation, extraction, or installation.

For each of the nine Python ELF records and 75 wheel ELF records, enumerated DT_NEEDED entries, splitting recorded search paths on colon. For paths containing $ORIGIN, normalized relative to the individual consumer's archive directory. Matched only actual recorded ELF paths within the same archive/wheel; otherwise checked the ten known OS names against the exact base evidence. Did not assume LD_LIBRARY_PATH, cross-wheel global scope, loader cache changes, inherited RPATH or an actual installation path.

| Direct dependency path candidate category | References |
|---|---:|
| Exact base OS library names | 239 |
| Archive-local path via recorded $ORIGIN search directory (all Pillow) | 23 |
| Explicit $ORIGIN-containing DT_NEEDED path (libpython3.so) | 1 |
| No candidate via recorded direct search paths | 2 |
| Total Python + wheel DT_NEEDED references | 265 |

Both unresolved direct search cases belong to python/lib/python3.13/lib-dynload/_tkinter.cpython-313-x86_64-linux-gnu.so: libtcl9.0.so and libtcl9tk9.0.so. Both files exist in python/lib, but _tkinter has no recorded search path. Tcl/Tk objects have /tools/deps/lib absolute build paths: one occurrence on Tcl and two identical occurrences on Tk. No assumption that these directories exist or are safe in the runtime. Pillow has five $ORIGIN/../pillow.libs entries and eight $ORIGIN entries; all 23 non-OS direct dependencies match actual same-wheel member paths. Freetype/harfbuzz form a mutual dependency cycle; this is not itself proof of failure or success.

Current collector combines RPATH and RUNPATH into search_paths, losing tag semantics, so inheritance, precedence and complete loader scope cannot be inferred. Interpreter PT_INTERP, relocation/type checks, installed directory layout, and actual loader binding remain unverified. The build candidate includes PyInstaller; do not silently remove Tcl/Tk or declare tkinter unreachable without inspecting the exact coding-only source and packaging hooks. Prefer an upstream-supported immutable build/profile correction over binary patching; any alternative interpreter or archive changes require new identity, provenance, licensing, capacity and dependency evidence. No unrestricted LD_LIBRARY_PATH workaround, no host directory mount, no candidate execution, no build attempt consumed. Next: preserve RPATH versus RUNPATH and PT_INTERP in existing evidence collector with regression tests, review exact packaging reachability of Tcl/Tk, and determine whether a controlled runtime check or profile remediation is needed. Issue #162 OPEN; release_authorized=false.

## Loader tag and headless packaging scope checkpoint — 2026-11-25

Baseline `638b03c13018e8897f46dcfdd4998a7c3f084875`. Prototype run 45509201929 succeeded: 393 tests, 392 pass, one skip; both interpreter and RPATH/RUNPATH regression tests green. Independently downloaded and checked ZIP CRC and SHA256:
- Python 14974862025: c0a12f46ed63508dc164f78d58429435fe56cffdf0efcfe485f551bb59eeda93.
- Wheel 14974383159: c13917dbb24822108ffd36981e4a0e624e50a61a60d8cc43e62fcf00bc3285e8.
- Prior packaging source artifact 14952123267: 735c574275f306a143ef2a02d6e394a0d79acd842a671b2ba6af11fa337fa6e7; exact patch digest 0609700a143b3fc8b0439f7ff2c74b75aa41c220fa9ba4294db35bac54b8f70f.

All nine Python and 75 wheel ELF records carry separately recorded RPATH, RUNPATH and PT_INTERP. No RUNPATH entries. RPATH: three Python objects (main executable $ORIGIN/../lib; Tcl /tools/deps/lib; Tk duplicate /tools/deps/lib) and 13 Pillow objects. Three PT_INTERP entries: Python executable and two PyInstaller Linux bootloaders, all /lib64/ld-linux-x86-64.so.2. Prior OS evidence verifies canonical loader bytes, but exact /lib64 alias still needs confirmation.

Correction/refinement of previous direct-only check: executable python/bin/python3.13 has DT_RPATH=$ORIGIN/../lib and no DT_RUNPATH. Normalizing relative to its recorded archive directory yields python/lib. Both libtcl9.0.so and libtcl9tk9.0.so exist there by exact member path. _tkinter has no RPATH/RUNPATH. Under glibc inherited DT_RPATH search semantics (https://www.man7.org/linux/man-pages/man8/ld.so.8.html), both formerly unmatched direct-only edges have a conditional executable-relative candidate. Thus 263 direct candidates + 2 conditional inherited candidates = 265/265 path candidates; NOT actual binding or a final loader pass. Do not assume arbitrary launching mode, actual staged symlinks, inheritance/scope, or absence of conflicting absolute build directories.

Read official pinned OpenHands spec at 077f3fad6d31cd852be5c87176e0a93c3b446126, path openhands-agent-server/openhands/agent_server/agent-server.spec, blob 9cb330d45e4ba8f49259b571167dfd567cc43430. Analysis excludes tkinter upstream; the verified coding-only patch preserves that exclusion. This reduces expected final bundle reachability but does not prove absence from build discovery, since PyInstaller may probe Tcl/Tk. No deletion, binary patch, broad LD_LIBRARY_PATH, or additional dependency needed on present evidence. Keep exact interpreter candidate and verify /lib64 alias, trusted staged layout, and conditional isolated import/load smoke check only after applicable pre-execution approvals. No candidate execution or installation. Legal, supply-chain, security and capacity gates remain open. Build attempt not consumed; Issue #162 OPEN; release_authorized=false.
