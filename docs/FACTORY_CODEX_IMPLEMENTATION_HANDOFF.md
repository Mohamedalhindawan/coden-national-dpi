# CODEN AI Factory — constrained Adopt-First implementation handoff

**Research inputs:** [105-candidate catalog PR #130](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/130) and [implementation Issue #131](https://github.com/Mohamedalhindawan/coden-national-dpi/issues/131). The catalog resides on a separate **draft** branch, not in this PR. Nothing below is marked installed or approved.

## Verified implementation baseline (before this PR)

| Existing artifact | State / limitation |
|---|---|
| `ai_factory/intake.py` | Restrictive synthetic intake; no executor |
| `ai_factory/review_queue.py` | Offline, zero-budget fail-closed review queue |
| `ai_factory/phase_zero.py` | Small SQL coding/QA prototype |
| `ai_factory/project.py` | Bounded single-function JSON-transform apps; deterministic engineering stages; not full-stack |
| `ai_factory/local_coder.py` | Pinned, offline llama.cpp + Qwen sample generation; host-specific |
| `ai_factory/router_preflight.py` and `router_smoke.py` | Experiments, not production multi-provider routing |
| `docs/FACTORY_ADOPTION_REGISTRY.md` | Existing narrower pilot adoption evidence |
| `ai_factory/checkpoint.py` | **New:** offline journal foundation; no worker or gateway |
| `ai_factory/checkpoint_project.py` | **New:** opt-in wrapper for offline project runner, records results and refuses duplicate task IDs |

**Do not** recreate these modules or claim eight actual independent model-operated teams from deterministic workflow stages.

## Candidate triage for the next session

| Function | Trial first | Alternative / reserve | Decision gate |
|---|---|---|---|
| Coding runtime | OpenHands SDK + Agent Canvas | OpenCode, Hermes Agent | Authorized API, sandbox integration, checkpoint recovery, no duplication |
| CAIE and skills | Hermes Agent (isolated), then Self-Evolution as an experiment | DSPy/GEPA components | Held-out evaluation, permission isolation, manual approval |
| Model gateway | Compare OmniRoute, LiteLLM, Bifrost *on identical tasks* | Portkey, New API | Auth terms, license, latency, costs, failover, safety; select one primary |
| Long-running jobs | Existing journal + minimal worker | Hatchet, Temporal | Crash replay, at-least-once effects, idempotency, maintenance cost |
| Code navigation | Serena + ast-grep | CodeGraphContext | Quality on repo navigation with token/time benchmarks |
| Independent evaluator | unittest + existing CI + Harbor sandbox pilot | SWE-bench Pro later | Held-out tests and comparable resource budgets |
| Observability | Existing logs + Langfuse trial | Phoenix, OpenTelemetry | Private-by-default tracing and request redaction |
| Untrusted execution | Existing pinned bubblewrap for scoped workloads | Daytona, E2B, gVisor later | Isolation and threat-model evidence |

### New: Offline provider recovery planning (implemented; not a live router)

- `ai_factory/recovery_policy.py` validates authorized route metadata, synthetic-only data rules, capabilities, limits and model costs; proposes fallback only on selected failure kinds.
- `ai_factory/recovery_checkpoint.py` records typed errors to the existing checkpoint journal; no execution or human-approval changes.
- `ai_factory/recovery_cli.py` supports a bounded offline JSON dry-run and optional journal update.
- `configs/model_recovery.example.json` is intentionally disabled/unapproved; see `docs/FACTORY_OFFLINE_RECOVERY_POLICY.md`.
- 27 deterministic tests cover this new stage. **No real model gateway, automatic Codex continuation, Hermes integration or paid provider usage is implied.**

### New: Durable SQLite queue foundation (implemented; no live worker)

- `ai_factory/durable_queue.py`: persists synthetic task identifiers, branch/commit and task spec hash in SQLite, with exclusive claims, time-bounded leases, heartbeats, final review gate, and crash quarantine instead of auto-replay.
- `tests/test_durable_queue.py`: 10 new deterministic tests, including two concurrent workers and expiry.
- `docs/FACTORY_DURABLE_QUEUE.md`: operator example and limitations; queue does NOT execute tasks or grant authorization.
- Codex still needs trusted worker integration, checkpoint reconciliation, backup, real error adapters and independently approved retry behavior.

### New: Operator-invoked offline queue worker (implemented and tested)

- `ai_factory/offline_worker.py`: **submit** pre-reviewed synthetic `status-counts` JSON tasks, hash and queue them, then **work-once** executes at most one item through the existing sandboxed `project.run()` pilot. No hosted LLM or background daemon.
- `tests/test_offline_worker.py`: 11 additional checks including an actual sandbox pilot, changed task payload refusal, corrupted journal, duplicate task ID, failed run, concurrent queue semantics inherited from earlier tests, and crash-to-human-review quarantine.
- `docs/FACTORY_OFFLINE_WORKER_RUNBOOK.md`: end-to-end operator commands and boundaries. PR #132 has now 66 added tests on top of existing factory tests.
- [CI run #44848783608](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44848783608): **122 tests PASS; OpenAPI PASS**.
- Remaining *real* work: broaden task classes beyond the synthetic demo, secure operator authorization and artifact storage, transactional queue/journal reconciliation, leased-worker supervision, approved cloud/local model adapters, cross-provider error mapping and evaluation of Hermes/OpenHands/OmniRoute.
### New: Reconciliation and component admission (implemented diagnostics and research-only registry)

- `ai_factory/reconcile.py`: read-only SQLite/Checkpoint audit. Detects mismatches, unfinished worker claims, orphan/corrupt journals, conflicting branch/commit, task file SHA drift; **never retries, approves or writes state**.
- `tests/test_factory_reconcile.py`: 12 targeted recovery diagnostic checks. `docs/FACTORY_RECOVERY_RECONCILIATION.md` documents CLI use and conditions.
- `configs/factory_components_proposed.json`: 16 candidate components, including Hermes / Self-Evolution / OpenHands / OmniRoute / LiteLLM / Bifrost / Serena / Harbor etc.; **research only, enabled=false and approved=false**.
- `tests/test_factory_component_catalog.py`: four checks keep proposed upstreams uniquely identified and unapproved. `docs/FACTORY_COMPONENT_ADMISSION_MATRIX.md` documents role separation and evidence gates.
- **Next Codex task:** start with divergence reporting and approval-safe recovery; do not blindly replay leased tasks; evaluate candidate tools only after comparing existing code and independent quality benchmarks.

## Exact remaining implementation order

### Stage A — align the branches and verify the baseline
- Inventory open PR chain: #116 → #118 → #124 → #126, plus #125 on its own stack, and catalog #130.
- Run the CI and tests for current factory branch. Report failures accurately.
- Confirm checkpoint tests on this PR pass in Linux.
- Do not merge one stacked PR to `main` without reviewing base dependencies and combined impact.

### Stage B — minimal reliable recovery
- The opt-in `checkpoint_project.py` project journal adapter is present; review its tests, then add real provider/worker errors and long-run durability without changing existing safety gates.
- Simulate quota/context failure, worker restart, and retry idempotency.
- Keep any external model fallback **off** by default.
- Implement minimal operator-owned state and backup/restore procedures.

### Stage C — multi-runtime trial
- Pilot OpenHands SDK or a simpler code agent against one synthetic multi-file task.
- Do not install all 105 candidates. Assess license, pinned upstream commit, transitive deps, secrets/network exposure.
- Compare OmniRoute/LiteLLM/Bifrost with **official authorized** API/test providers. No consumer-session-token workarounds.
- Store evaluation evidence and a single adoption decision per capability.

### Stage D — end-to-end operational gate
- Execute a synthetic, multi-file project from task intake through isolated coding, independent tests, review and draft PR.
- Kill/restart a worker mid-run and verify no duplicate irreversible actions.
- Show measured quality, time and compute/token cost before/after.
- Demonstrate budget stop, emergency cancel, permissions and code review.
- Report `PASS/FAIL/BLOCKED`. Never claim 24/7 operation from a local CLI run.

## Non-goals and governance
- No government/citizen data, automatic deployments, auto-merge, credential transfer or paid calls.
- Do not mutate Playbook section numbers (230), CODEN/TAMAM identities or security baseline.
- Keep the resulting additions as **draft**, with each capability marked `proposed / implemented / tested / reviewed / operational` separately.
