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
