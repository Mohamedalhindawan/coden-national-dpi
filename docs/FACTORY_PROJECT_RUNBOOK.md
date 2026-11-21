# Run the eight-role factory offline

This pilot builds a command-line Python application that reads one JSON value and emits one JSON result. The coding step can generate the implementation on CPU from a synthetic task and visible examples, accept a locally reviewed module, or use a fixed demo. Seven other roles are deterministic engineering stages. The supported project interface is a single pure `transform(value)` function with basic loops, dictionaries and selected builtins. Web services, arbitrary repositories, external dependencies, private data, release and production execution require separate approval and engineering.

## Reproduce

Use Linux x86_64 with usable unprivileged user namespaces, bubblewrap 0.12.0, /usr/bin/prlimit, the distro /usr/bin/python3 and standard /usr/lib and /usr/lib64 layout. Controller Python 3.12 or newer. Missing capabilities stop a run. No fallback executes candidate code on the host. The source and artifact each receive a new read-only root, isolated network, cleared environment, 128 MiB address limit, two CPU seconds and five seconds wall time per case.

```sh
python3 -m venv /tmp/coden-factory-env
. /tmp/coden-factory-env/bin/activate
python -m pip install --only-binary=:all: --no-deps --require-hashes -r ai_factory/locks/review-linux-x86_64.txt
python -m ai_factory.project
CODEN_REQUIRE_SANDBOX=1 python -m unittest discover -s tests -v
```

For real local generation obtain the two public artifacts below on a trusted machine. The CLI verifies both SHA-256 digests before extracting/loading them. Only this exact CPU release and model are accepted. The download transfers public assets into the machine; inference sends no task data out. Allow about 0.5 GB for weights plus temporary extracted binaries.

- [llama.cpp b12600 CPU archive](https://github.com/ggml-org/llama.cpp/releases/download/b12600/llama-b12600-bin-ubuntu-x64.tar.gz) · SHA-256 `da524c71f9dd09913df29264bb7229b99a2de82d8a26e6902e6921d413560d6d`
- [Qwen GGUF at the verified model revision](https://huggingface.co/Qwen/Qwen2.5-Coder-0.5B-Instruct-GGUF/resolve/ebb2015119c907b064c512bf053e945850b5875f/qwen2.5-coder-0.5b-instruct-q4_k_m.gguf) · SHA-256 `1d9614638d18024d0fbb36575a15f1302a3adf044df10345688ec4f6e1c4ff32`

```sh
python -m ai_factory.project --task ai_factory/examples/status-counts.json \
  --local-model /path/to/llama-b12600-bin-ubuntu-x64.tar.gz /path/to/qwen2.5-coder-0.5b-instruct-q4_k_m.gguf
python -m ai_factory.project --task ai_factory/examples/sum-durations.json \
  --local-model /path/to/llama-b12600-bin-ubuntu-x64.tar.gz /path/to/qwen2.5-coder-0.5b-instruct-q4_k_m.gguf
```

For a Codex-authored local candidate, supply `--source ./transform.py` in place of the model options. The existing Phase 0 CLI still handles the previously authorized read-only Agents API SQL artifact adapter. The Python runner has no hosted model, Git credential, provider fallback or deployment action. Model assets must be trusted, read-only operator files for the duration of the run.

## Human review and acceptance

A successful CLI invocation prints the private directory and `awaiting_human_review`. Inspect contract.json, program.py, events.jsonl, README.md and review.json. Verify the candidate.pyz hash against the receipt. Keep synthetic review cases separate from visible examples and derive them from the requirement. The orchestrator accepts at most eight cases of each kind and one coding attempt. Rejections leave evidence and no success receipt. A successful test does not authorize execution against real data, merge, release or deployment. The repo PR is the human review channel. Protect approvals and retain receipts outside the writable local workspace before treating this as organizational approval evidence.

| Executed check | Observed result |
|---|---|
| Real offline generation: status-counts | Two public cases and one withheld Arabic case passed. Archive `fbf373e585f057313b3fba7a32fd3cadb2051c6322a48d6d113adfe7d66251c6`. Repeated final prompt produced the same hash locally. |
| Real offline generation: sum-durations | Two public cases and one different withheld input passed. Archive `27798d4f7420c0fb6d0ccb86f8708436479964f7c26f6793304845f39fcbf0ce`. |
| Earlier coding trials | The first candidate imported json and failed security; the second misinterpreted the input and failed testing. Expressing examples as Python assertions clarified the interface. Each was an explicitly separate run. |
| Governance and operational checks | Positive budget, deployment action and non-synthetic classification blocked; missing dependency, altered asset and incorrect packaged output stopped the pipeline. A host probe observed cleared environment, absent workspace and read-only root. Tests exercised reproducible packaging and a second source-based project. |

CI runs the mandatory sandbox integration tests and OpenAPI validation. The heavyweight real-model experiment is opt-in locally. Hardware or runtime changes can alter model outputs. These two cases establish feasibility, not reliability on unrestricted projects. Remaining organizational gates include independent human sign-off, approved project scope, trusted artifact retention, and readiness evidence for the actual project class. [Adoption decisions and sources](FACTORY_ADOPTION_REGISTRY.md)
