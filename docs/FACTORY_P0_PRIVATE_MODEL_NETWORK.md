# CODEN AI Factory — P0 private-network access to a *synthetic* local-model endpoint

**Draft PR #174 (UNAPPROVED)**, stacked on real OCI cgroup-boundary #173 → OpenHands SDK pinned source #161 → SDK bridge #149 → multi-file reviewer #148.  
**Frozen Founder Plan v1.0** preserved, sections 22, 32, 49, 50, 65, 72, 78, 80.  
**OpenHands runtime isolation issue #162: STILL BLOCKED.** No public deployment or permission to merge.

## Why a new proof is useful

The previous real Docker #173 proof validated a single resource-capped container with `--network=none`. That is appropriately restrictive for a synthetic task, but a real OpenHands agent-server eventually needs access to a **local Ollama model endpoint**. The dangerous shortcut would be allowing a public Internet-enabled bridge just to give the agent model access.

This PR uses Docker's **real `docker network create --internal --driver bridge`** with exactly two temporary containers, both based on the **same immutable Docker Official BusyBox test image**:

`docker.io/library/busybox@sha256:73aaf090f3d85aa34ee199857f03fa3a95c8ede2ffd4cc2cdb5b94e566b11662`

- **Synthetic model endpoint:** a tiny local BusyBox `httpd` responding at `http://ollama:11434/health` with exactly `CODEN_SYNTHETIC_MODEL_ENDPOINT_ONLY`. This is a **mock HTTP endpoint**, **not** an Ollama server, trained model, agent/tool call or inference.
- **Synthetic agent client:** a second container that uses `wget` to reach only that synthetic endpoint, then independently tries outbound `http://1.1.1.1/` and `http://example.com/`. A successful outside request **fails the CI job**; an in-network mock HTTP failure also fails.
- The network is internal, local bridge, first-party run-unique name, with exactly two attached container IDs and **zero published host ports** in inspect.
- Both containers are `uid=65534`, `--cap-drop=ALL`, `--security-opt=no-new-privileges`, `--read-only`, 16 MiB bounded `/tmp` tmpfs, no host mounts/secret inheritance/Docker socket, `--cpus=1 --memory=256m --memory-swap=256m --pids-limit=64`. The guest verifies cgroup limits, effective capabilities and filesystem permissions.

A new **read-only fail-closed verifier** at `ai_factory/factory_internal_model_network_probe.py` validates actual Docker network and both container inspect JSONs, requiring the same network identity, cgroup requests, no host port forwarding, no extra participants/volumes/capabilities/credentials. It NEVER starts a container, contacts an LLM or approves deployment. `tests/test_factory_internal_model_network.py` includes positive and adverse tests for tampered network metadata, malicious image, extra network services, public ports, missing limits and wrong network IDs. CI creates an intentionally short-lived actual internal network, runs the two real containers and retains **only sanitized result JSON**, followed by explicit teardown.

## What a GREEN test proves — and does NOT

It can demonstrate **on one named GitHub-hosted Docker runner**:

1. Two real resource-capped synthetic containers can communicate with an internal DNS alias `ollama` on TCP 11434.
2. The actual client guest cannot complete the tested public IP and public DNS HTTP requests through that Docker internal network.
3. Docker inspect metadata shows exactly two network participants, no host ports, no unapproved mounts, no added Linux privileges.
4. Real guest has CPU/RAM/PID cgroup caps, no effective Linux capabilities, non-root user, no-new-privileges and immutable rootfs.

It does **NOT** demonstrate that every possible exfiltration path is blocked. A Docker internal bridge permits communication with other containers on that bridge if the privileged daemon joins them later. It is not a complete per-service allowlist/firewall or tenant isolation against the Docker host. **GitHub-hosted Docker rootless is not verified.** It is not proof that the real OpenHands image/SDK, all subprocesses or Ollama endpoint are constrained. Some system routing/host-bridge surfaces require independent adversarial verification.

No real OpenHands `Conversation`, no actual Ollama model, no 3-file agent-created project, no agency/user/beneficiary data, no API keys, no paid inference, no auto-merge and no production authorization.

## P0 remaining: Human review and actual OpenHands

1. Establish an audited rootless/isolated operator-managed container runtime that enforces CPU/RAM/PIDs, disk/inodes, child-process, teardown and network controls on the actual OpenHands agent server; do not bypass #162.
2. Pin and independently review the **real OpenHands agent-server image digest** and all SDK/transitive dependencies, including SBOM, license and vulnerability/provenance checks.
3. Run a **real local Ollama** endpoint with model weight hash/license review. Independently verify explicit service identity, port and isolated egress under the actual runtime (not a mock HTTP stub).
4. With explicit human operator authorization, execute **one official SDK Conversation** to create exactly three synthetic files and independently test against held-out acceptance through #148.
5. Keep production/release/merges pending human review and evidence. `openhands_live_execution_authorized=false` in every receipt.

**No new institutional engines:** this is a narrow OpenHands #162 isolation investigation under the approved CODEN AI Factory v1.0, not a rewrite of the architecture.
