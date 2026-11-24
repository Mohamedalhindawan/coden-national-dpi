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
