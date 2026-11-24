# R2 OS base library presence review
Baseline 1126a0017c079aa094008c8ee95636a60e5f6f89, run 45493938376 success. Artifact 14967052943, local ZIP SHA256 b198cb509b752fb083cbfcd44ec85a3a7640aceb1ca26c5457be63350671d05d, four entries, CRC clean. Base docker.io/library/ubuntu@sha256:9a04f13b3f80ef056361e30868593b1cfd2279fe19e4081cb93a90bf56819d6a amd64. All ten required external library names found, actual canonical file hashes recorded, all ten canonical paths have dpkg-query owners. Failed lookups for /lib alias paths are not missing files; /usr/lib canonical paths matched. No additional packages needed for these ten names.
| Package | Version | Library count |
|---|---|---:|
| libc6:amd64 | 2.39-0ubuntu8.9 | 7 |
| libgcc-s1:amd64 | 14.2.0-4ubuntu2~24.04.1 | 1 |
| libstdc++6:amd64 | 14.2.0-4ubuntu2~24.04.1 | 1 |
| zlib1g:amd64 | 1:1.3.dfsg-3.1ubuntu2.3 | 1 |
Next collect provider ELF dynamic and version-definition evidence, copyright notices and security evidence for exact packages. Presence is not symbol compatibility, recursive loader closure, provenance, legal or vulnerability admission. No source build or candidate execution. Conditional approval remains unconsumed, issue #162 OPEN.
