# CODEN AI Factory — P0 real Docker resource boundary: limited, evidence-based trial

**Status:** Draft PR #173 / partial P0 risk reduction only / NOT OpenHands agent execution.  
**Plan:** Founder-approved CODEN AI Factory v1.0 sections 22, 32, 49, 50, 65, 72, 78 and 80 unchanged.  
**Issue:** #162 OpenHands hard runtime isolation.

## Why this pilot rather than immediate OpenHands?

Actual official upstream OpenHands SDK DockerWorkspace pinned at source commit `077f3fad6d31cd852be5c87176e0a93c3b446126` (inspected in Draft #161) does **not** demonstrate native Docker `--cpus`, `--memory`, `--pids-limit`, `--cap-drop` or `--read-only` enforcement. Constructing the upstream DockerWorkspace can launch a container **before** local post-creation checks. Starting a real agent with that unchecked container would violate the v1.0 security gate.

This PR **does not** modify SDK internals, install OpenHands or claim to close issue #162. It demonstrates, in one short-lived CI test, Docker's ability to apply the necessary limits to a **different synthetic Docker Official BusyBox fixture**, then tests those settings from **inside the running guest**.

## Pinned test image and provenance

Exact official Docker image selected for test (not an agent-server image):

`docker.io/library/busybox@sha256:73aaf090f3d85aa34ee199857f03fa3a95c8ede2ffd4cc2cdb5b94e566b11662`

This digest is the published Docker Official `busybox:1.36.1` multiarch index. CI independently checks the pulled image's `RepoDigests`, OS and architecture. The runner is Linux amd64. This is an *image identity check*, not a transitive SBOM, code-signature or full rights/security review; those remain OPEN.

Documentation: https://docs.docker.com/reference/cli/docker/container/run/ and https://hub.docker.com/_/busybox/.

## Exact real OCI constraints and verified negative controls

The first-party Draft PR GitHub Actions job runs one named synthetic container using:

- CPU: `--cpus=1` and guest cgroup `cpu.max`.
- RAM: `--memory=256m --memory-swap=256m` and guest cgroup `memory.max`.
- Process count: `--pids-limit=64` and guest cgroup `pids.max`.
- Filesystem: `--read-only`; guest mount `ro`, rejection of writes to rootfs; one writable `--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=16m,mode=1777`.
- Linux privileges: `--user=65534:65534 --cap-drop=ALL --security-opt=no-new-privileges`, guest CapEff zero and NoNewPrivs one.
- Network: `--network=none`; no non-loopback network interface, no host networking, no public port mappings.
- Namespace/process/lifecycle: `--pid=private --ipc=private --rm`, bounded run, `trap cleanup EXIT`, no restart, no host mounts, no Docker socket or inherited credentials.
- Audit: check actual Docker `inspect` settings using `ai_factory/factory_docker_isolation_probe.py`; probe **never runs** docker or SDK and emits read-only sanitized JSON, with immutable image digest and `release_authorized=false`.

Unit and tampering tests in `tests/test_factory_docker_isolation_probe.py` reject missing/widened CPU/RAM/PID caps, inherited credentials, privileged/root users, writable root, mounts, egress, floating image tags, unrestricted restarts and unknown/absent Docker inspect schemas.

## Exact limits of the conclusion

**What a GREEN CI run can prove:** a specific Docker daemon/runner successfully created one synthetic *non-root* container with the requested cgroup, filesystem, network and privilege restrictions, and guest checks observed those boundaries.

**What it does NOT prove:**
- The host Docker daemon is **rootless**; GitHub-hosted Docker may be rootful. Report `rootless_daemon_verified=false`.
- An audited image digest, transitive SBOM, vulnerability status and combined licenses for the **real OpenHands agent-server**.
- Actual correct mounting of the OpenHands workspace or the Ollama model endpoint while retaining strict egress deny.
- Complete disk/inode/host data limits for an OpenHands code-writing sandbox.
- Continuous independent host enforcement, nested child trees, agent-controlled terminal tools, API-specific credential leakage, or production readiness.
- A real OpenHands SDK Conversation or multi-file model execution. **`openhands_live_execution_authorized=false` always.**

In particular, **`--network=none` is suitable for this fixture but prevents model communication**: a future real agent with an isolated Ollama network needs independently checked network ACL and deny-external-egress, not merely a named bridge. Rootless non-root container users and rootless host Docker are different concepts.

## Remaining requirements and Human review

1. Independent non-rootful/rootless operator runtime or explicitly approved safer rootless/pod sandbox. Runtime must apply limits to both the **actual SDK agent server and all child commands**, not just this fixture.
2. Exact agent-server image digest; full software-agent-sdk/openhands-workspace/agent-server/terminal dependencies locked and SBOM/license/security reviewed.
3. Network isolation that permits only a verified local Ollama service, strict egress/secret/volume restrictions, disk budget and safe time-bound teardown, verified with adversarial tests.
4. One operator-approved genuine OpenHands SDK Conversation on three synthetic files with independent holdout tests and immutable review evidence (#148), no automatic release.
5. All existing Draft PRs human reviewed, source catalog states unchanged, issue #162 remains BLOCKED until everything is observed and approved.

The sandbox work is **real technical progress**, but is not a certified or approved factory runtime. No paid inference, autonomous merging, source approval or changes to the frozen v1.0 plan.
