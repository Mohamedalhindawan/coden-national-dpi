# R2 glibc disposable OS remediation experiment — decision package

2026-11-25 | PROPOSED / NOT AUTHORIZED | Issue #162 OPEN
os_remediation_authorized=false; build_authorized=false; live_conversation_authorized=false; release_authorized=false.

## Independently verified inputs
Reviewed baseline ea965564988b9971ca1443ed52fe64313e3e8d66. Reopened local ZIPs 14974697509 (0241d45e47c8ad063c79c5f20e5d58bb99f971d8663141383a3536460a889257), 14973918329 (834753409377bb93e1efe0d97d89b1272ad0a84d4e90c8754d0597652d85be0d), and 14975291902 (f52af7c58eaba8241535267d355d7f27b29044ba4fcc8841cd77bc2e03b95e15); recomputed hashes and ZIP CRC, all match.
Frozen base docker.io/library/ubuntu@sha256:9a04f13b3f80ef056361e30868593b1cfd2279fe19e4081cb93a90bf56819d6a, linux/amd64.
Both exact packages 2.39-0ubuntu8.12, signed APT index-bound, upstream security archive:
- libc6, 3264258 compressed bytes, SHA256 d821b41fc59cb4978ecd53bc83e5c964ac15d305c8d2ac4c8a35aebe55010fb9.
- libc-bin, 681714 compressed bytes, SHA256 22f0393621e72ed1b53d228ee332180269182b5445761c7d7b74f5cba75a1dd6.
Simulation: precisely 2 upgrades, 0 installs, 0 removals, 2 unrelated packages not upgraded. libc6 depends on libgcc-s1; libc-bin depends on libc6 >2.39 and <2.40. No network resolution or installation authorized.
Listing-derived capacity: libc6 299 entries, 284 regular files / 13234891 bytes; libc-bin 57 entries, 34 regular files / 2142584 bytes; combined 356 entries, 318 regular files / 15377475 bytes and 3945972 compressed bytes. This is NOT peak writable storage or RAM measurement.
Four maintainer shell scripts checked with local /bin/sh -n, all exit 0; syntax only, no candidate script execution:
- libc-bin.postinst 11993c6ae210c6fa149dcaf55bb46db7f9c301bb986d70115ce817f4db962caf
- libc6.postinst 03bfa319bca128ba5766427c9150232b1498e1944bf28af359c5026c3fb99fd9
- libc6.postrm 204fed75c70ca60fa6838d73eab940a12b030fc9beac43f2c18dd3aad75dc3ad
- libc6.preinst 0fca8cbd215a3f6c45d71c754354d06889d0fbc77577866096488efd265ffcf3
Two triggers (libc-bin and libc6) retained. Scripts reference debconf, service restart, ldconfig, systemd branches and dpkg-divert. Do not skip package scripts or assume syntax proves behavior. Prior static review preserves all 4417 export keys across seven changed providers.

## Proposed separate authorization and bounded recipe
Prior operator receipt #162 comment 7144392543 authorizes ONE conditional non-agent OpenHands build, not a writable-root OS update with maintainer scripts. Do not consume that attempt for this experiment. No executable installation workflow is enabled by this document.

1. Stage only two exact .deb files; verify package identity, architecture, hash and size on host before staging and within the isolated boundary. Stage source/copyright evidence separately for legal review. Do not expose credentials, production mounts, host sockets or unrelated files.
2. Before any real installation, prove the disposable writable-root storage and complete cleanup using synthetic content. The prior read-only-root plus private scratch proof cannot be reused as proof of a bounded writable root. Use rootless Podman user namespace, never host root; private PID/IPC/cgroup namespaces, no network, no privileged mode, no host devices or service sockets, no-new-privileges. Establish a minimal namespace-only capability profile required for ordinary dpkg; do not assume cap-drop-all works and do not automatically expand privileges on failure. Explicit review required if profile differs.
3. Proposed ceilings for one separate OS experiment: 2 CPU, 4 GiB RAM including tmpfs, zero swap, 128 PIDs, total private writable storage at most 1 GiB / 65536 inodes (including root writable layer, temp space and package databases), 180 seconds wall clock plus bounded cleanup. Measure actual staged and peak usage. If any limit cannot be proven, stop before installation. No paid API, no automatic retry or escalation. Use immutable old base; no apt upgrade, no package resolution, no network during installation.
4. Once operator approval and preflight exist, run ordinary dpkg installation of only the two verified local packages inside disposable rootless environment. Keep maintainer scripts and triggers enabled; no host package changes. Record full sanitized exit status, logs, process identity accounting and cleanup. Abort on script error or unexpected package/config change.
5. Before treating output as a candidate, verify dpkg audit clean and exact package delta (92 package identities, only two version changes), hashes for seven expected changed providers and three unchanged providers, canonical /lib64 loader alias and path, loader/cache sanity and basic trusted OS command smoke checks. Capture notices and source obligations. Produce a local immutable image or OCI artifact only within approved capacity and policy; do not push or deploy. Independently re-scan exact output with Trivy, compare full coverage and findings against old 35 rows and six targeted CVEs; retain residual risk decisions and evidence. A scan without those CVEs is not legal admission or runtime security proof.
6. Remove disposable resources on all exits, verify no tracked process survives and no unexpected host changes. Keep only sanitized evidence. Original digest remains frozen, rollback is discard candidate. Any new base requires explicit admission, provenance, license, capacity and full runtime validation. No OpenHands source build or Python candidate execution in this experiment.

## Decision requested
Approve one separate bounded isolated OS-only glibc remediation experiment subject to the above preflight and rights review, or defer and retain the original base for further static evidence. This decision does not authorize a live agent, main merge, release, deployment, host installation, or automatic retry.
