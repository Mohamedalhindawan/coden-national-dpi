# CODEN Agent Execution & Evaluation Framework 1.0

Status: Draft — execution requires an approved evaluator and isolated environment.

## Operating model
This framework defines how to run pilot cases; it does not itself invoke Factory AI, Codex, or any external agent. A run is valid only when an evaluator records the actual tool/model session and evidence.

### Run stages
1. Prepare: pin repository commit, skill version, case ID, synthetic fixture, agent/model version, system prompt version, and allowed tool list.
2. Isolate: use a disposable workspace with no production credentials, citizen data, unrestricted network, or write access to production.
3. Execute: give the agent the case and the skill; do not reveal hidden evaluator notes if blind evaluation is intended.
4. Capture: preserve raw output, tool trace, timestamps, cost, latency, errors, and environment metadata.
5. Score: two reviewers independently assess the eight dimensions and mandatory gates.
6. Adjudicate: resolve score differences greater than 10 points or any disagreement on a mandatory gate.
7. Remediate: create an issue for each material failure and rerun against the same case version.
8. Report: publish a summary with limitations; retain failed and superseded records.

## Run controls
- Run one case per clean session; do not reuse hidden state between agents.
- Same case, input, model settings, and tool permissions are required for fair comparisons.
- Fixed model versions are preferred; record unavoidable changes.
- Tool calls are evidence, not merely implementation details.
- An agent cannot approve its own benchmark or lifecycle transition.
- Never execute production actions during a benchmark.
- Redact secrets and personal data from logs before storing artifacts.

## Score calculation
Each dimension is scored from 0 to 5. Weighted score = sum((dimension score / 5) × dimension weight). Record raw dimension scores and reviewer rationale. A failed mandatory gate makes the overall disposition Fail, regardless of numeric score.

## Disposition
- Pass: score ≥ 90, every mandatory gate passes, and reviewers agree.
- Revise: score 70–89, or a non-critical gate needs remediation.
- Fail: score < 70 or any mandatory gate fails.
- Not Run: no verified execution evidence exists.

These dispositions apply to a specific case run, not automatically to the skill lifecycle status.

## Lifecycle protection
No automated run may change registry status. Reviewed or Tested requires documented human review and complete evidence. Approved and Published require designated organizational authority.

## Evidence package
For each run retain run-record.json, raw output, tool trace (if available), evaluator score sheets, and reviewer decision. Check artifacts for secrets and personal data before committing.
