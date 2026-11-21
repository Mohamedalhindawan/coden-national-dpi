# CODEN AI Factory — OpenHands Adopt-First Multi-file Acceptance Gate

**Status:** Draft / independent review required / no production readiness.
**Source:** [OpenHands/software-agent-sdk](https://github.com/OpenHands/software-agent-sdk), using upstream documented `Agent`, `Conversation`, `Tool`, `DockerWorkspace`, `TerminalTool` and `FileEditorTool` interfaces.
**Scope delivered in PR #148:** an offline **reviewer of a sandbox-exported three-file project**, not an OpenHands model invocation, service installation or new agent framework.

## What we adopt vs what we keep

- Adopt **OpenHands SDK** for actual agent/tool loops once approved; never implement a replacement coding-agent engine. Its official examples use `Conversation(agent=..., workspace=DockerWorkspace(...))`, `send_message`, `run` and `close`.
- Keep CODEN's existing `project.inspect_source` (restricted Python AST), Ruff `project.lint`, pinned Linux `project.execute` (bubblewrap 0.12.0 + resource limits) and `project.verify` visible/hidden tests. These independent acceptance gates must not be controlled by the agent.
- The new `ai_factory/openhands_multifile_review.py` only validates a **three-file sandbox export**, builds a deterministic Python zipapp from the permitted function and runs existing verification. It cannot run OpenHands itself, authorize a task, merge, deploy, spend or replay operations.

## First accepted multi-file fixture

The incoming `candidate-dir` must contain **exactly**:

```text
candidate-dir/
├── app/
│   └── logic.py           # only def transform(value); strict CODEN AST + Ruff
├── README.md              # untrusted documentation
└── tests/
    └── test_logic.py      # untrusted tests: syntax check only, NEVER executed
```

Any symlink, missing/extra file, invalid directory, oversized file, unsafe Python function, non-synthetic task, unverified Linux sandbox or failing hidden case is rejected. The output directory must already exist in an operator-controlled path. Generated tests are deliberately **excluded** from the executable archive; CODEN uses its own withheld acceptance tests.

The provided `ai_factory/examples/openhands-multifile` directory is a **manually checked-in synthetic fixture**, not a real OpenHands generation. Its matching request is `ai_factory/examples/openhands-multifile-task.json`. The separate review cases are never inserted into agent prompts.

## Reproduce the result with no provider or SDK calls

```bash
# Static no-op mode (no filesystem reads, sandbox or agent execution):
python -m ai_factory.openhands_multifile_review \
  --task ai_factory/examples/openhands-multifile-task.json \
  --candidate-dir ai_factory/examples/openhands-multifile \
  --output-root /tmp/coden-openhands-reviewed

# On a trusted Linux test host with pinned bubblewrap + Ruff dependencies:
mkdir -p /tmp/coden-openhands-reviewed
python -m ai_factory.openhands_multifile_review \
  --task ai_factory/examples/openhands-multifile-task.json \
  --candidate-dir ai_factory/examples/openhands-multifile \
  --output-root /tmp/coden-openhands-reviewed \
  --evaluate-isolated
```

The explicit `--evaluate-isolated` permits **only the local synthetic zipapp acceptance test**, not a new LLM invocation. A passing result is `status=awaiting_human_review`, with `candidate.pyz` and `review.json` under an operator-owned output directory. The verified code can be executed independently in the existing sandbox. It remains `execution_authorized=false`, `release_authorized=false`, `agent_execution_performed=false`.

## Evidence and limitations

- RED test-first CI: [run #44858065947](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44858065947) failed importing the not-yet-implemented `openhands_multifile_review` module.
- GREEN CI: [run #44858144843](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44858144843) passed 192 tests with one conditional skip; OpenAPI validation passed. The Linux test ran a **real multi-file zipapp** inside pinned bubblewrap and verified its output.
- Further tracked fixture/CLI tests were added afterward: check the **latest PR commit's CI** for their results.

The resulting zipapp contains a fixed operator-owned bootstrap, `app/__init__.py` and the reviewed `app/logic.py` only. The agent's untrusted tests are neither executed nor shipped as executable tests. Hash evidence is for local integrity comparison, **not an authenticated signature** or a release approval. This verifier is for **restricted synthetic Python status-count tasks**, not arbitrary full-stack user code or a complete software supply-chain security audit.

## Real OpenHands SDK pilot — next strictly gated step

1. Install and pin an audited **OpenHands SDK** release and Docker Agent Server image by immutable digest in a trusted private machine. The public GitHub repository top-level LICENSE is MIT; dependency/image/model licenses still require separate review.
2. Use an **isolated ephemeral container workspace**, not `Conversation(..., workspace=os.getcwd())` or a host-mounted company repository. Give it access only to an otherwise empty scratch export directory and a deliberately restricted network. Review the SDK's default volume/env forwarding and disable unsafe defaults. Do not mount SSH keys, cloud credentials, CODEN repositories or production secrets.
3. Select an operator-authorized LLM/model (e.g. a verified local Ollama deployment reached on an explicitly restricted container network). A model name being listed by `ollama_probe` is not sufficient proof of locally isolated inference. Model weights, model routing, API terms and egress policy need actual verification.
4. Have OpenHands create the three fixture files **in that sandbox**, then freeze/export the directory into the operator-controlled review area; never trust a generated claim of test success.
5. Call `openhands_multifile_review` on the exported bytes and compare the candidate zipapp against withheld tests. Retain artifacts, hashes, rootless isolation evidence, logs with secrets redacted, elapsed time and actual cost.
6. Repeat with a held-out *new* fixture, assess reliability and complexity, then decide if OpenHands SDK replaces the prior one-function synthetic coder. Do not deploy a daemon, bypass provider quotas, allow self-approval or merge main automatically.

**PR dependencies:** this PR is independent of Draft PR #146 (Ollama discovery), Draft PR #147 (Ollama SDK pilot) and Draft PR #140 (offline worker/supervisor). They remain separate review gates; no merge/production claims.
