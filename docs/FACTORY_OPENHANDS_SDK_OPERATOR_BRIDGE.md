# CODEN AI Factory — OpenHands SDK Operator-Gated Bridge (Draft)

**Branch:** `feat/factory-openhands-sdk-operator-bridge-20261121` / [PR #149](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/149). **Dependency:** [PR #148](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/148) multi-file acceptance gate.

**Observed status:** OpenHands SDK's documented `LLM`, `Agent`, `Tool`, `Conversation`, `DockerWorkspace`, `TerminalTool` and `FileEditorTool` APIs are now wired into an optional, operator-controlled bridge. **CI uses a fake SDK implementation; no OpenHands SDK/container, Ollama model, Docker network or cloud provider is installed or invoked.** No claim of real-agent success or production readiness.

## Why this is Adopt-First

CODEN does **not** reimplement the OpenHands agent, coding tools, conversation state or model server. It reuses upstream interfaces, and its existing *independent* `openhands_multifile_review.review`, `project.inspect_source`, Ruff, bubblewrap and hidden acceptance tests.

The `ai_factory/openhands_sdk_operator.py` bridge is intentionally narrow:

1. Validate a **synthetic-only** task with recipe `python-transform` and no paid/deploy instructions.
2. Require explicit `allow_agent=True`; default does not import the SDK or touch a workspace.
3. Validate an **already-running, operator-provided** `DockerWorkspace`, not a local host workspace: official pinned agent-server image digest, a single dedicated empty export mount, `forward_env=[]`, no GPU or extra ports, and a named Docker network other than the default/host/bridge. This is a **configuration check, not proof** of network isolation, image provenance or resource enforcement.
4. Accept only a locally designated `ollama/*` model and exactly `http://ollama:11434` as the SDK model endpoint. Cloud-labeled models, common cloud API key environment variables and remote base URLs are refused. An Ollama server can still be configured to reach cloud providers; independently prohibit egress and validate the actual model's metadata.
5. Use upstream `LLM`, `Agent`, `Tool`, and `Conversation` with the supplied remote Docker workspace. The prompt restricts authoring to `/workspace/export/app/logic.py`, `/workspace/export/README.md` and `/workspace/export/tests/test_logic.py`; it shares **only visible test cases**.
6. Close the conversation after `run()`. On an exception, record `agent_failed_review_required` and **never automatically retry**. The agent may already have produced partial side effects.
7. Inspect the generated files through the previously tested independent multi-file reviewer, which executes only a bounded candidate zipapp in pinned Linux bubblewrap and runs withheld cases; generated tests are never run or shipped.

Passing this bridge's CI means the **SDK API binding contract and the independent synthetic acceptance path** work with test doubles. It does **not** demonstrate a real model call, secure image/network setup, process-group cancellation, budget enforcement, multi-provider failover, production readiness or permission to merge.

## Operator prerequisites for an eventual real trial

- Approve an immutable **OpenHands SDK** release and audited Agent Server image **by actual SHA256 digest**, not `:latest`. Validate dependencies, image SBOM/signatures and applicable licenses.
- Prepare an ephemeral isolated container, dedicated **empty scratch export** directory and a Docker network whose **real** firewall policy forbids internet access and unaudited hosts. Mount neither CODEN repositories nor credentials, SSH keys or citizen/government/customer data.
- Provide a verified local Ollama service on the isolated network at `http://ollama:11434` with a locally loaded, reviewed coding model. No cloud model aliases.
- Independently cap compute, model budget and wall-clock lifetime with a supervising container/cgroup watchdog: **this SDK adapter does not implement a real process kill deadline**, and `Conversation.run()` can block. Operator must verify termination and review potential partial output before retry.
- Ensure `candidate_root` is the exact host scratch mount attached as `/workspace/export:rw`, and `output_root` exists on a protected operator filesystem. Import the checked-in synthetic task from `ai_factory/examples/openhands-multifile-task.json`.
- For a single authorized call, pre-create and own a real `DockerWorkspace` using the upstream SDK; pass it as `workspace` and set `allow_agent=True`. The bridge never starts a Docker container itself, installs a model or handles API credentials. Code-managed workspace construction is intentionally deferred until isolation is independently proven.

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
