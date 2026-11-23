# OpenHands source and host checkpoint

Base: [Draft #175](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/175), commit `5def8197a67346972e0992f2f0ff05787096145e`. Live session blocked under [#162](https://github.com/Mohamedalhindawan/coden-national-dpi/issues/162). Plan v1.0 is tracked in #168.

## Previous work reused

The runtime dependency chain is #148 → #149 → #161 → #173 → #174 → #175. #163 is the assignment tracked by #164. #164–167 and #169–172 cover model-generated metrics, source review, tooling, and queue recovery. These branches were reviewed as parallel work. The [previous Qwen run](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45272593446) completed successfully on the base SHA. GitHub lists [receipt archive 14865862355](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45272593446/artifacts/14865862355) with archive digest `a3f6a57cad76ed684e5d4ee22bab2ec4a51eefb01ce8b093ae95806eb93364f1`; reuse the historical result for the bounded model trial only.

## Source evidence

Reviewed [the upstream commit](https://github.com/OpenHands/software-agent-sdk/tree/077f3fad6d31cd852be5c87176e0a93c3b446126), its root MIT license, four package manifests, image publication workflow and complete uv.lock. The source lock's Git blob is `d0c1f0b5570e6af35b7da7b5b13eb957d4658d96` and its SHA-256 is `71c5479cb609b60872a7cbd34da764a0804c2e50c2658dba1bb5255e180d3603`.

[source-lock.cdx.json](source-lock.cdx.json) inventories the universal source lock. Independent comparison matched all 416 name/version records; deleting one component in memory caused the comparison to fail as expected. Four editable projects (SDK, tools, agent-server, workspace) match their manifests at 1.63.1. All 412 registry records refer to PyPI and declare at least one distribution. All 3,024 listed distributions carry syntactically valid SHA-256 hashes. The check inspects lock metadata only. The lock spans platforms, optional and development dependencies. Installed packages, OS layers, distribution bytes, individual licenses and vulnerability status still require review against an immutable image.

The release tag v1.63.1 resolves to `722e5d403cf75d4e032b79296cfaf178f8678a93`. Its lock blob is `cb29af9ccac9fed4d3451891f388962ac12a57c4`. Comparing the release and pinned source also found 26 changed paths under openhands-agent-server. A version label alone cannot establish equivalence. The upstream server.yml identifies ghcr.io/openhands/agent-server as the image repository. The metadata workflow resolves the documented commit-derived Python tag anonymously and cross-checks manifest bytes by digest. A matching tag or digest still needs builder provenance linking it to the full commit.

## Observations on the Work host

| Read-only observation | Result |
| --- | --- |
| Effective UID | 1000 |
| Docker and Podman commands, standard rootless and system Docker sockets | Absent |
| /sys/fs/cgroup, cgroup.controllers | Absent; /proc/self/cgroup returned 0::/ |
| Python OpenHands package lookup | Absent |
| Anonymous HTTPS request to ghcr.io/v2/ | Timed out, HTTP 000 |

## Executed checks on GitHub-hosted public runners

A separate [rootless Podman probe](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45275067691) verified cgroup v2 delegation, half a CPU, 64 MiB RAM and 16 PIDs on a synthetic non-root BusyBox workload. Its child shared the parent's cgroup, had zero effective capabilities and no-new-privileges; the container had loopback only and no system Docker socket. This measures a different workload from the official agent. The default Docker daemon in the metadata job reported rootless=false. The [prototype contract job](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45275067689) is independent of both image gates.

The source CycloneDX inventory passed the official CycloneDX 1.5 JSON schema. Syft generated the **separate image SPDX inventories** below. Both image artifacts and the Qwen receipt were downloaded, SHA-256 checked and archived here to survive expiration of the CI artifacts. No image was executed during scanning.

| Upstream Python candidate | linux/amd64 manifest SHA-256 | SPDX packages | Missing/unknown declared license | HIGH findings |
| --- | --- | ---: | ---: | ---: |
| Default | 2674cd2659e626452ac46a76fe71aded046311210c7e0cc6ffcb194668037506 | 3,292 | 2,150 | 10 via SBOM scan |
| Minimal | 9a36355fa2baacaae1c6dd5a1a80492bba89d1dec5a536af572ba5fb3e96e22f | 280 | 10 | 124 via direct image scan |

- [Default scan](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45274550368) and [full-image-review.zip](full-image-review.zip), archive SHA-256 `0b53fa311bed1765915569ad578b6c3b7ced5943d3507d98f65a48e07702f28d`. Trivy reported OS family none when consuming the SPDX, so these results do not cover OS vulnerabilities. The HIGH records concerned embedded Go dependencies of container tooling. Two docker/docker records had no reported fixed version.
- To address those findings we evaluated the official minimal variant from the same pinned source; its build definition omits the additional container capabilities. [Direct scan](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/45275067686) and [minimal-image-review.zip](minimal-image-review.zip), archive SHA-256 `6b773af239eb96921e17e329ce99a3c33e1dcd35a8afe9eef2570156b7d8c843`. Trivy recognized Debian 13.7. All 124 HIGH records are OS-package findings covering 36 advisory IDs; 68 records have no fixed version listed by this scan. The raw report contains available fix versions per package. The different scan scopes prevent direct comparison of finding counts. Neither scan establishes coverage of all dependencies bundled into the agent binary.
- [qwen-pr175-receipt.zip](qwen-pr175-receipt.zip), SHA-256 `a3f6a57cad76ed684e5d4ee22bab2ec4a51eefb01ce8b093ae95806eb93364f1`. Original receipt reports eight predicted tokens, zero paid calls, and no official OpenHands session. No inference replay.
- The PR shows two failed image admission gates on their respective revisions. The scanners completed and uploaded evidence before admission rejected their results. No severity suppression or release approval.

## Runtime handoff under issue #162

Start with the minimal image report. Rebuild or obtain a patched, provenance-verifiable image, rescan its new digest and resolve outstanding license and bundled-binary coverage. Confirm actual process and child limits, disk/inodes, secrets, cleanup and authenticated local-only model communication in the selected agent runtime. The current bridge only accepts an Ollama provider name; #175 exercised llama.cpp /completion. Prove authenticated chat/tool compatibility before starting a session. #148 currently accepts one Python implementation, a Python test and a README. A three-code-file task requires an independently reviewed candidate contract. No agent-created source was produced or tested, and issue #162 remains open.
