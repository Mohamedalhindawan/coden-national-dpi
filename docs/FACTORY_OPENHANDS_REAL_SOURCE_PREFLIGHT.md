# CODEN AI Factory — Real OpenHands source compatibility and runtime safety gate

**2026-11-23 — Draft / UNAPPROVED.** This is a pinned **source inspection**, not a running OpenHands agent.

## Adopt-First evidence

The OpenHands package and DockerWorkspace source were retrieved from the official repository at immutable Git commit:

`077f3fad6d31cd852be5c87176e0a93c3b446126`

Repository: https://github.com/OpenHands/software-agent-sdk

| Pinned source | Upstream path | Git blob object SHA-1 |
|---|---|---|
| source-004 (DockerWorkspace) | `openhands-workspace/openhands/workspace/docker/workspace.py` | `0a28fb27053f5e830b91914bdb4592aec30d3cc1` |
| SDK package metadata | `openhands-sdk/pyproject.toml` | `1304f0106a4229451882dcf28501df594a921d15` |
| Workspace package metadata | `openhands-workspace/pyproject.toml` | `3da2c0bdc2c818d9b3aedc3ae7f64a30b0a31034` |
| Root license | `LICENSE` | `b0bd86a6335a564bd3766666bebbf014fd6a8013` |

All four source assets have been stored as **read-only review copies** under `third_party/source_pilots/openhands-077f3fad/`; nothing in the factory executes them. The original LICENSE is MIT, copyright OpenHands contributors; independent commercial/distribution/subdirectory license review is still required before use beyond inspection.

The pinned metadata identifies `openhands-sdk` and `openhands-workspace` version **1.63.1**, requiring Python >= 3.12, with many unpinned or version-range transitive dependencies. This does **not** constitute a locked, reproducible SDK installation or an SBOM.

## Actual result

`python -m ai_factory.openhands_upstream_preflight` performs bounded, no-follow file reads, verifies each Git blob SHA-1 object, checks MIT attribution, parses *without importing or executing* DockerWorkspace using Python AST and checks the upstream constructor/launch fields.

**Result: `BLOCKED_FOR_REAL_SESSION`** even if all pinned source files match. The inspected upstream DockerWorkspace's container run builder has no explicit values for:

- `--cpus` CPU cgroup limit;
- `--memory` memory cgroup limit;
- `--pids-limit` process count limit;
- `--cap-drop` Linux capability restrictions;
- `--read-only` immutable container root.

It does set parameters such as network, volumes and forwarded environment, but those do **not** prove complete isolation. The pinned source starts its Docker container during initialization and binds its agent-server host port to 127.0.0.1, so the operator needs network, localhost service, image and process supervision evidence as well. This report does not infer that a particular Docker daemon cannot independently supply effective limits through external policy; that policy has not been independently demonstrated for CODEN.

## Reproduce with no SDK/Docker/model

```bash
python -m unittest discover -s tests -p 'test_openhands_upstream_preflight.py' -v
python -m ai_factory.openhands_upstream_preflight
python -m ai_factory.openhands_upstream_preflight --receipt /tmp/coden-openhands-upstream.json
```

The receipt requires a **new absolute output path**, records `runtime_state=BLOCKED_FOR_REAL_SESSION`, `live_agent_execution_authorized=false`, `docker_container_started=false`, `release_authorized=false`, and `paid_calls=0`. It is **not** an approval token. The source inspector itself has no Docker, network, model, paid-API, install or GitHub write operations.

GitHub Actions workflow `openhands-source-preflight.yml` runs actual source-integrity and risk tests, then retains the sanitized receipt for human review. CI passing means **the safety risk has been detected correctly** and the source metadata matched; it does not mean a model completed a multi-file task.

## What is required for the first actual OpenHands session

1. Independently reviewed pinned OpenHands SDK, Tools, Agent Server and Workspace packages with complete dependency lock/SBOM/license/advisory results and a reproducible build; no unpinned `pip install -U`.
2. Audited, immutable agent-server image SHA-256, runtime isolation with independently enforced CPU/memory/PID/deadline limits, filesystem and capability restrictions, no outbound public network and an accessible **approved local** model endpoint.
3. Synthetic-only task and empty isolated export volume, explicit operator approval, no agent credentials or access to main, no model API spend and no auto retry.
4. Execute the official OpenHands `Conversation` once inside this approved environment. Retain a redacted audit trace.
5. Independently inspect **all actual output files** using existing PR #148 multi-file reviewer, the hidden tests, Ruff, bubblewrap and review hashes; record FAIL/BLOCKED if any gate fails.
6. Allow only human-reviewed artifact packaging; never automatically promote catalog status or deploy a generated result.

**Status:** This source-compatibility and risk gate is now testable. A complete real OpenHands agent conversation remains **not attempted** in this PR; the existing fake SDK contract in PR #149 must not be presented as a real provider/model demonstration. Catalog source-004 stays disabled/unapproved.
