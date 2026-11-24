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
