# CODEN AI Factory — OpenHands SDK Operator-Gated Bridge (Draft)

**Branch:** `feat/factory-openhands-sdk-operator-bridge-20261121` / [PR #149](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/149). **Dependency:** [PR #148](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/148) multi-file acceptance gate.

**Observed status:** OpenHands SDK's documented `LLM`, `Agent`, `Tool`, `Conversation`, `DockerWorkspace`, `TerminalTool` and `FileEditorTool` APIs are now wired into an optional, operator-controlled bridge. **CI uses a fake SDK implementation; no OpenHands SDK/container, Ollama model, Docker network or cloud provider is installed or invoked.** No claim of real-agent success or production readiness.

## Why this is Adopt-First

CODEN does **not** reimplement the OpenHands agent, coding tools, conversation state or model server. It reuses upstream interfaces, and its existing *independent* `openhands_multifile_review.review`, `project.inspect_source`, Ruff, bubblewrap and hidden acceptance tests.

The `ai_factory/openhands_sdk_operator.py` bridge is intentionally narrow:

1. Validate a **synthetic-only** task with recipe `python-transform` and no paid/deploy instructions.
2. Require explicit `allow_agent=True`; default does not import the SDK or touch a workspace.
3. In the **managed operator path**, validate the local Docker context, immutable agent-server image, dedicated internal network and empty export directory **before** constructing upstream `DockerWorkspace`. The separately available expert `run_once` path accepts a pre-created workspace. Both require a single export mount, `forward_env=[]` and no GPU or extra ports. These are **configuration checks, not proof** of egress isolation, image provenance or resource enforcement.
4. Accept only a locally designated `ollama/*` model and exactly `http://ollama:11434` as the SDK model endpoint. Cloud-labeled models, common cloud API key environment variables and remote base URLs are refused. An Ollama server can still be configured to reach cloud providers; independently prohibit egress and validate the actual model's metadata.
5. Use upstream `LLM`, `Agent`, `Tool`, and `Conversation` with the supplied remote Docker workspace. The prompt restricts authoring to `/workspace/export/app/logic.py`, `/workspace/export/README.md` and `/workspace/export/tests/test_logic.py`; it shares **only visible test cases**.
6. Close the conversation after `run()`. On an exception, record `agent_failed_review_required` and **never automatically retry**. The agent may already have produced partial side effects.
7. Inspect the generated files through the previously tested independent multi-file reviewer, which executes only a bounded candidate zipapp in pinned Linux bubblewrap and runs withheld cases; generated tests are never run or shipped.

Passing this bridge's CI means the **SDK API binding contract and the independent synthetic acceptance path** work with test doubles. It does **not** demonstrate a real model call, secure image/network setup, process-group cancellation, budget enforcement, multi-provider failover, production readiness or permission to merge.

## Managed Docker preflight before container creation

OpenHands upstream `DockerWorkspace` **starts the Docker container during
object construction**, before the caller gets a chance to validate its
properties. Validating an already-created workspace alone is not a secure
launch strategy. The new **`launch_isolated`** entrypoint now checks trusted
operator task paths, image digest, network policy, credential environment,
pinned CODEN bubblewrap availability and locally cached Docker metadata
**before** calling `DockerWorkspace(...)`.

The read-only Docker preflight does:
- `docker context inspect` and checks that the active Docker endpoint is a
  known Unix socket (`/var/run/docker.sock`, `/run/docker.sock`, or the current
  user's rootless `/run/user/UID/docker.sock`). Explicit SSH/TCP contexts and
  unrecognized socket paths are rejected **before** workspace construction.
- `docker network inspect NETWORK` and requires the exact selected network's
  `Internal=true` and `Driver=bridge`.
- `docker image inspect IMAGE_DIGEST` and requires the exact source
  repository digest in `RepoDigests` plus a valid local image ID.
- Rejects missing metadata, erroring Docker inspect, default/host networks,
  `:latest` images, untrusted paths and cloud-provider credential variables.
- Only after all gates pass, instantiates upstream `DockerWorkspace` with
  one empty export mount, `forward_env=[]`, no GPU/extra port/log streaming
  and a named isolated network; then reuses `run_once` and the independent
  multi-file acceptance gate.

**Security limit:** this is metadata preflight, not a security attestation.
The active Docker context is now checked for an approved **local Unix socket**,
but a local socket may still point to a proxied or compromised daemon. The
operator must inspect socket ownership and the actual engine, not merely the
CLI output. An internal Docker network alone is not sufficient
against a compromised/multi-homed container, host proxy or local Ollama
server that may itself call cloud services. Enforce host egress rules,
trusted image/model provenance, read-only SDK dependency supply chain,
container cgroup budget and external watchdog before a real trial.
An image can disappear between inspection and `docker run`; disable
unapproved pulls at the host policy level.

### Operator-only command

```bash
# This no-op is safe by default even if the paths don't yet exist.
python -m ai_factory.openhands_sdk_operator \
  --task ai_factory/examples/openhands-multifile-task.json \
  --candidate-dir /tmp/coden-openhands-empty-export \
  --output-root /tmp/coden-openhands-reviewed \
  --model ollama/qwen2.5-coder:1.5b \
  --server-image 'ghcr.io/openhands/agent-server@sha256:REPLACE_WITH_ACTUAL_64_HEX_DIGEST' \
  --network coden_internal

# On an authorized operator-controlled machine, replace the placeholder
# with the actual audited local image's immutable 64-hex digest, then append:
#   --preflight-only
# This inspects the active Docker context, selected network, cached image and
# pinned CODEN sandbox. It MUST NOT start a container or contact a model.

# Only after verifying Docker socket/daemon ownership, real network egress,
# pinned SDK/model, available hardware and an external process watchdog:
#   --allow-agent
# This is a separate opt-in mode; never combine it with --preflight-only.
```

The default CLI returns `status=disabled`, without reading the task or
workspace, importing OpenHands, invoking Docker or contacting any model.
`--preflight-only` returns `preflight_passed` only when its **read-only
local Docker metadata / CODEN sandbox checks** succeed; that status does
NOT prove model availability, SDK installation, firewall isolation, image
supply-chain review, process watchdogs or an actual agent invocation.
With `--allow-agent`, it attempts one **real** SDK Conversation and
independent review if all preconditions are satisfied. It does not install
Docker/OpenHands/Ollama, create the Docker network, download a model, set
a watchdog, configure firewalls or silently retry. If construction fails
after the SDK has possibly started a container, the result is
`workspace_start_failed_review_required`; the operator must inspect and
clean up potential resources manually.

**TDD proof:** [RED #44858859764](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44858859764)
reproduced missing managed-launch behavior, followed by
[GREEN #44858942314](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44858942314):
217 tests run, 1 conditional skip, OpenAPI PASS. The inert-by-default
CLI has separate RED tests in
[run #44859110983](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44859110983).
Refer to the **latest PR head** CI for the completed CLI result.

**Docker context / preflight TDD:** [RED #44859513882](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44859513882)
caught unsafe Docker contexts and missing `--preflight-only`;
[GREEN #44859588580](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44859588580)
passed **224 tests, 1 conditional skip, OpenAPI PASS**. The new
tests simulate remote SSH/TCP Docker contexts and disallowed Unix sockets,
confirm the context command is read-only, and verify that an authorized
metadata check never instantiates the SDK or the Docker workspace.
**These are mocked Docker metadata tests, not actual Docker container tests.**


## Operator prerequisites for an eventual real trial

- Approve an immutable **OpenHands SDK** release and audited Agent Server image **by actual SHA256 digest**, not `:latest`. Validate dependencies, image SBOM/signatures and applicable licenses.
- Prepare an ephemeral isolated container, dedicated **empty scratch export** directory and a Docker network whose **real** firewall policy forbids internet access and unaudited hosts. Mount neither CODEN repositories nor credentials, SSH keys or citizen/government/customer data.
- Provide a verified local Ollama service on the isolated network at `http://ollama:11434` with a locally loaded, reviewed coding model. No cloud model aliases.
- Independently cap compute, model budget and wall-clock lifetime with a supervising container/cgroup watchdog: **this SDK adapter does not implement a real process kill deadline**, and `Conversation.run()` can block. Operator must verify termination and review potential partial output before retry.
- Ensure `candidate_root` is the exact host scratch mount attached as `/workspace/export:rw`, and `output_root` exists on a protected operator filesystem. Import the checked-in synthetic task from `ai_factory/examples/openhands-multifile-task.json`.
- For a single authorized call, use the managed `--allow-agent` CLI only after the `--preflight-only` and independent security gates. The managed entrypoint creates one upstream `DockerWorkspace` **after** validating metadata; the upstream SDK owns its actual Docker lifecycle. The bridge does not install the SDK, Docker, Ollama or model weights and it cannot prove host-level network policy. `run_once` also supports a separately pre-created workspace for authorized specialist use.

## Automated test evidence

**Test-first red:** [CI #44858457876](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44858457876) failed importing the absent SDK adapter. The next implementation run found an accidental duplicate keyword in the invalid-option **test case**, fixed in a subsequent test commit; not an SDK runtime defect.

The test suite mocks the official classes and asserts:
- Inert default and no SDK startup.
- Blocked host/bridge/default networks, unpinned image tags, excess mounts, inherited environment variables, GPU/extra ports and invalid local model/endpoint.
- No review-only hidden examples in OpenHands prompts.
- Upstream `Conversation.send_message`, `run`, `close` invocation and fail-closed error behavior.
- A synthetic fake SDK writing all three expected files, followed by **real pinned Linux bubblewrap acceptance** of the resulting multi-file Python zipapp.

**Status:** Code and tests are in Draft PR #149. Check **latest CI** on its head for validation. Human approval and an independently audited end-to-end real agent/model trial remain open.

## Relationship to other factory components

- [PR #140](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/140): offline worker, supervisor and crash recovery; this SDK adapter does **not** yet run under its watchdog.
- [PR #146](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/146): local Ollama model discovery.
- [PR #147](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/147): single-file official Ollama Python SDK generation pilot.
- [PR #148](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/148): independent multi-file acceptance, required by this PR.
- **OmniRoute and FreeLLMAPI:** optional competing API gateways for a *later* controlled A/B evaluation, not installed or stacked here. Neither bypasses provider terms or quotas.

**Next hard gate:** run a genuine pinned OpenHands SDK + DockerWorkspace + approved Ollama model in an operator-controlled isolated network under a tested watchdog, then reproduce the multi-file artifact and independent hidden-test result. Keep every PR Draft pending an independent security review.
