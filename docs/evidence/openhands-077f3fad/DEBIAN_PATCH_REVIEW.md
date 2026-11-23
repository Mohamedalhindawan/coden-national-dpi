# Debian patch availability for the OpenHands minimal image

[Draft #176](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/176) identified 124 HIGH package/advisory records. [Package verification run](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45276110478) inspected the stopped image at linux/amd64 digest `sha256:9a36355fa2baacaae1c6dd5a1a80492bba89d1dec5a536af572ba5fb3e96e22f` and copied its actual dpkg database. Read-only source for [Debian archive fingerprints](https://ftp-master.debian.org/keys.html).

| Baseline population | Signed APT result |
| --- | --- |
| 56 findings (14 distinct advisories across four Kerberos libraries) | Resolver selected Debian-Security 1.21.3-5+deb13u2 for libgssapi-krb5-2, libk5crypto3, libkrb5-3 and libkrb5support0. Solver simulation and authenticated download completed. |
| 62 findings | No fixed version in the archived scan and the signed candidate matched the installed version. |
| 6 findings | Across three OpenSSL packages, Debian offers 3.5.9-1~deb13u1. The Debian tracker lists that version as vulnerable for both [CVE-2026-107494](https://security-tracker.debian.org/tracker/CVE-2026-107494) and [CVE-2026-124709](https://security-tracker.debian.org/tracker/CVE-2026-124709). |

[Archived evidence](debian-patch-review.zip) contains the 124 observations, four downloaded package SHA-256 values, solver transcript and signed repository index hashes. Archive SHA-256 `a9c33813a871022ef9fd322e33a56bfab662a6a8658a7d5fdd5889bbef2badde`. Independently reconciled every package/advisory/version tuple against the original Trivy archive and compared candidate/fixed versions with dpkg. The four package files were downloaded on the ephemeral CI runner. Only their hashes and resolver evidence are retained.

**Decision:** Signed Debian updates alone cannot admit this digest. No packages were installed, no patched image was produced, and no vulnerability was closed on a rescanned image. Actual image admission, agent containment, authenticated Qwen tool calls and three-file generation remain open in [#162](https://github.com/Mohamedalhindawan/coden-national-dpi/issues/162). Resume image evaluation from a separately pinned and provenance-verifiable rebuilt candidate, carrying forward the previous inventories and acceptance criteria.
