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

## Resume boundary

1. Review the PR's manifest-inspection job. Record its outcome separately from the host observations. If the commit-derived image has no verifiable producer/source binding, select an auditable image build from the pinned commit. Preserve the index and architecture-specific digest, signed build evidence, actual image SBOM, licenses and vulnerability findings before admission.
2. On the selected rootless runner verify actual agent-server and child cgroups, CPU, RAM, PIDs, disk/inodes, wall time, cleanup, mount and secret boundaries. Prove authenticated access to the model and deny other egress. #173–175 concern different workloads.
3. Once gates pass, use #149 for one official Conversation against Qwen. Capture sanitized trace and export. Apply #148's independent verifier. Its current exact contract is app/logic.py, tests/test_logic.py, README.md; a requirement for three code files needs a new reviewed contract before the run.
4. This checkpoint has no agent output, test result for a generated candidate, release authorization or production approval.
