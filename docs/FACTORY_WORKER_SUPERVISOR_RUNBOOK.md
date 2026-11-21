# CODEN AI Factory — Bounded Offline Worker Supervisor

**State:** Experimental, operator invoked, one-shot only. Not a daemon, 24/7 platform, external model connector, quota bypass or permission system.

**Implementation:** `ai_factory/worker_supervisor.py`, `tests/test_worker_supervisor.py`. Layered on existing `ai_factory/offline_worker.py` and its metadata-only SQLite queue.

## Why this exists

Before this addition, the offline worker could run a synthetic project but had no parent watchdog to enforce a **whole-worker wall clock limit** or terminate a child process group on timeout. The supervisor deliberately spawns only the fixed `ai_factory.offline_worker ... work-once` module, never a caller-supplied shell string, as a **single isolated process session**.

It does not run indefinitely. The *underlying project runner* remains responsible for Linux bubblewrap / Python limit checks, and is not a substitute for complete host/container isolation.

## Dry run

Requirements: Linux/POSIX machine, existing operator-only queue + journal + task directory + output directory. See `docs/FACTORY_OFFLINE_WORKER_RUNBOOK.md` for synthetic task registration.

```bash
python -m ai_factory.worker_supervisor \
  --queue-db /tmp/coden-operator-demo/queue.sqlite3 \
  --journal /tmp/coden-operator-demo/journal \
  --task-dir ai_factory/examples \
  --output-root /tmp/coden-operator-demo/outputs \
  --worker-id offline_operator \
  --timeout-seconds 60 \
  --lease-seconds 120 \
  work-once
```

The `lease-seconds` setting must exceed the process timeout by at least 10 seconds and be no greater than 3600 seconds. The supervisor does **not** extend leases in a loop or auto-renew them for long runs. Use bounded synthetic jobs only.

## Exit semantics

| Case | Supervisor result | Effect |
|---|---|---|
| No queue items | `idle` / exit 0 | No work, no model usage |
| Completed synthetic demo | `awaiting_human_review` / exit 0 | Artifacts need independent human review |
| Worker blocked | `blocked` / exit 1 | Inspect journal and queue |
| Whole worker exceeds deadline | `timed_out_review_required` / exit 1 | Sends SIGKILL to child process group; no retry or automatic queue recovery |
| Child exits nonzero | `worker_failed_review_required` / exit 1 | Operator investigates without exposing stderr |
| Invalid child response | `untrusted_worker_result` / exit 1 | Rejects unexpected output |

After any timeout, consult the local checkpoint / queue evidence and run the **read-only** reconciliation scan before inspecting expired leases:

```bash
python -m ai_factory.reconcile \
  --queue-db /tmp/coden-operator-demo/queue.sqlite3 \
  --journal /tmp/coden-operator-demo/journal \
  --task-dir ai_factory/examples

python -m ai_factory.offline_worker \
  --queue-db /tmp/coden-operator-demo/queue.sqlite3 \
  --journal /tmp/coden-operator-demo/journal \
  --task-dir ai_factory/examples \
  inspect-expired
```

**Never auto-retry** an interrupted task: an interrupted worker may have already produced files or other effects. `inspect-expired` only quarantines expired leases and does not restart.

## Security boundaries

- Runs the **known, fixed local Python module** with a fixed argument schema and `shell=False`; rejects invalid worker IDs, missing/linked operator paths and invalid timeouts.
- Sends a minimal child environment that **excludes OPENAI_API_KEY, ANTHROPIC_API_KEY, subscription cookies, custom PYTHONPATH and other credentials**. Caller-controlled PATH is retained for the pinned Linux sandbox binaries; operator must trust their host.
- Child stdin is disabled, stderr discarded; only a bounded JSON result is inspected. Secrets and raw crash details are not reported in the supervisor output.
- The supervisor itself is **not a privilege boundary**: filesystem ownership, local Python, working copy, PATH, sandbox and all installed dependencies must be trusted.
- Killing a process group is not proof all external side effects were rolled back. A future production worker needs stronger container/cgroup cancellation and signed independent evidence.
- No model calls, network access, provider approvals, budgets, automatic fallback, merge or deployment in this module.

## Worker result integrity — new regression gate (2026-11-21)

The supervisor treats the child JSON stdout as **untrusted metadata**, not as
approval evidence. A non-idle response must be an exact object containing
`task_id`, a known `status` string, and `execution_authorized: false`,
with an optional `directory` confined to the operator-owned output root.
Missing or invalid task identifiers, unknown fields, duplicate JSON keys,
unexpected status types and out-of-root artifact paths return
`untrusted_worker_result` and do **not** initiate retries or approvals.

**TDD evidence:**
- [RED run #44855772322](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44855772322): four rejected-schema expectations failed and an unhashable status raised an error in the previous supervisor.
- [GREEN run #44855854602](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44855854602): 207 tests executed, 1 conditional skip, full test step and OpenAPI validation PASS.

**Limit:** exact JSON shape is not authenticated process identity or cross-store
transactional evidence. It does not prove that the reported task actually
completed correctly, that output bytes match a signed manifest, or that the
checkpoint and SQLite database are atomic. These require an independent
operator-owned evidence gate and security review before production use.

## Independent test gates

```bash
python -m unittest discover -s tests -p 'test_worker_supervisor.py' -v
python -m unittest discover -s tests -v
```

Ten new tests cover a real empty queue, deadline and path rejection, timeout kill semantics, no auto retry, failure isolation, environment secret filtering and the fixed CLI command.

## What Codex still needs to do

1. Add an operator-verified approval service for **bounded** workload types and a trusted artifact/manifest store.
2. Implement an actual persistent supervisor/worker with secure lifecycle management and crash-aware reconciliation. A one-shot CLI is **not** 24/7 autonomous execution.
3. Add trusted, rate/timeout-aware, official model APIs or local adapters. Evaluate OmniRoute / LiteLLM / Bifrost and select one gateway.
4. Validate Hermes / OpenHands agent runtimes separately with synthetic tasks and independent benchmarks before activation.
5. Test cancellation under adversarial multi-process workloads and demonstrate that work is not replayed without approval.
