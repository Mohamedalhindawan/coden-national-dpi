# Single-host factory operations
The queue, worker admission, scheduler, DAG, model selection and control facade plus seven relevant test modules are taken at their original paths from #26 commit 2c775421baa89a5dc89d34a2777d90dad4690a8f. Other enterprise proposal modules retain their existing review scope. The controller persists one project and eight dependent tasks per private operator-owned directory. SQLite serializes claims and reservations, fences leases, records audit events and binds the project to its initial specification. A pause blocks new reservations and lets an in-flight call finish. Each role has one bounded attempt. A worker crash after reserving a call consumes its slot; a later dispatch reconciles expired leases. Inspect failures before submitting a corrected project in a fresh directory.

Use `python -m ai_factory.operations submit DIRECTORY --task SPEC.json`. Use `status`, `audit`, `pause` or `resume` with the same directory. Restrict filesystem access to the operator. The gateway makes a simulated selection before execution, permits only the pinned local CPU model, reserves at most eight calls and budgets zero paid API dollars. Host electricity and hardware costs are unmetered. There is no hosted endpoint, automatic release, multi-tenant authentication, or remote dashboard. Archive the review artifact and receipts before treating them as organizational records.

## Run the eight local model specialists

Use the verified Linux runtime, wheel and model assets described in [the project runbook](FACTORY_PROJECT_RUNBOOK.md). Supply a fresh private directory. All eight roles use separate, role-scoped local Qwen completions. Orchestrator chooses test order; architecture chooses the module boundary/name within the supported layout; coding implements the business function; security independently inspects the source and can veto; testing completes a literal assertion; documentation writes the purpose; DevOps chooses serialization and packages a constrained CLI; review evaluates the implementation and can veto after withheld tests. Host code owns policy, dependencies, formatting, packaging and execution. No specialist can authorize release.

```sh
python -m ai_factory.operations submit "$RUN_DIR" --task ai_factory/examples/sum-durations.json
python -m ai_factory.specialists "$RUN_DIR" --local-model "$CPU_ARCHIVE" "$GGUF" --steps 3
python -m ai_factory.operations status "$RUN_DIR"
python -m ai_factory.specialists "$RUN_DIR" --local-model "$CPU_ARCHIVE" "$GGUF"
python -m ai_factory.operations audit "$RUN_DIR"
```

The bounded worker drains ready stages and exits. Starting it again resumes the durable DAG. A successful final review returns the archive location and SHA-256. Status reports the per-stage attempts, failure type, duration, queue totals, model reservations and paid API cost. The 240-second lease exceeds the 90-second model deadline plus bounded test time for the demonstrated workload. A blocked or expired stage cannot publish downstream success. A process death requires a subsequent dispatch to reconcile leases. Operators must manage service startup and private storage themselves.

## Verification and limits

The [captured real run](evidence/local-specialists.json) contains the eight receipts, state after the first worker exited, timings and all five UTF-8 files from the reviewed archive. A second process completed the remaining five stages without repeating a completion. Three unit cases executed inside a separate test bundle; a withheld case ran against the final archive, and a fresh input of [3,7,11] returned 21. The first experiment exposed a repeated model-proposed test, and a subsequent proposal used a scalar for a list interface. The final implementation checks novelty and input type and supplies a new list permutation when available.

CI exercises checkpoint/resume, model veto and packaging using fixed model responses. Real inference was executed locally. CPU cost and actual token usage were not measured. A single host and a single pinned provider were exercised. No multi-tenant IAM, production SLO, cross-host failover, indefinite worker service or general unattended repository editing is claimed. Human approval still occurs in GitHub. There is no deployment or TAMAM execution action.

Validation commands: `python -m unittest discover -s tests -v`, `python -m unittest discover -s skills/tests -v`, and `python -m openapi_spec_validator api/openapi.yaml`.
