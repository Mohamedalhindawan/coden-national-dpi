# CODEN Multi-Agent Operations & Evaluation Runbook 1.0

## Before a pilot
- Name a human task owner and independent reviewer.
- Pin repository commit, skill versions, provider/model versions, prompt versions, and tool adapters.
- Use a disposable isolated workspace and synthetic fixtures only.
- Disable production credentials and production network access.
- Set run deadline, concurrency, retry, and spend ceilings.
- Define acceptance criteria and stop conditions before execution.
- Ensure logs and artifacts cannot contain secrets or personal data.

## Pilot sequence
1. Validate contracts and schemas without invoking an agent.
2. Run one specialist in read-only mode on a synthetic case.
3. Inspect traces, artifact hashes, policy decisions, and cost records.
4. Repeat in a clean session to assess consistency.
5. Add one specialist and validate handoff contracts.
6. Inject timeout, malformed output, denied permission, and cancellation.
7. Have an independent human reviewer score the result.
8. Keep cases Not Run until actual evidence exists.

## Evaluation metrics
| Metric | Definition |
|---|---|
| Task success rate | Accepted tasks / completed attempts |
| First-pass acceptance | Tasks accepted without revision / completed tasks |
| Rework rate | Tasks requiring revision / completed tasks |
| Critical policy violations | Count; target zero |
| Unauthorized tool attempts | Count and disposition |
| Handoff validity | Valid child results / all child results |
| p50 / p95 latency | End-to-end and per-agent elapsed time |
| Cost per accepted task | Recorded usage cost / accepted tasks |
| Evidence completeness | Runs with required evidence / all runs |
| Human review time | Reviewer active time per deliverable |

Report denominators, case mix, provider/model versions, and sample size. Do not infer production reliability from a small synthetic pilot.

## Stop conditions
Stop and quarantine if real citizen/sensitive data appears, a secret is exposed, an agent exceeds tool/workspace scope, a policy gate is bypassed, state becomes inconsistent, unbounded delegation/retry/spend occurs, a critical security finding remains unresolved, or evidence is missing for a high-impact claim.

## Incident handling
1. Stop new task scheduling and revoke task-scoped grants.
2. Preserve minimal audit evidence and artifact hashes.
3. Quarantine affected workspaces and redact sensitive logs.
4. Notify named security and task owners through approved channels.
5. Record impact, timeline, root cause, containment and remediation.
6. Resume only after human authorization and a documented regression test.

## Run record
Use the existing skills/validation/RUN_RECORD_TEMPLATE.json and link each run to a pilot case. Never fabricate provider traces, costs, reviewers, or pass results.

## Release checklist
- [ ] Changes are in a reviewable branch.
- [ ] No secrets or real personal data are present.
- [ ] Contract and policy checks pass.
- [ ] Required tests were actually executed and evidence retained.
- [ ] Security findings are resolved or explicitly accepted by an authorized human.
- [ ] Human review is recorded against exact artifact hashes.
- [ ] Rollback/revert path is documented.
- [ ] No production action is performed without separate approval.
