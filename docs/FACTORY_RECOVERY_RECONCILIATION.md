# CODEN Factory — Crash Recovery Reconciliation (Read-only)

**Status:** implemented diagnostic; not an automatic restart mechanism or a production approval service.

**Implementation:** `ai_factory/reconcile.py` and `tests/test_factory_reconcile.py`.

## Why this matters

`ai_factory/offline_worker.py` writes to **two independent stores**:

1. `ai_factory/durable_queue.py` — SQLite metadata and exclusive worker lease.
2. `ai_factory/checkpoint.py` — append-only JSONL with branch/commit and state.

SQLite and the JSONL journal do **not** share an atomic transaction. A process kill may happen between their updates. Therefore a recovered worker must not assume that a leased, queued or partly completed task is safe to repeat. This diagnostic provides a bounded read-only snapshot of divergence.

## How to run

Run on a trusted operator machine, using the same private queue and journal paths as your local pilot:

```bash
python -m ai_factory.reconcile \
  --queue-db /tmp/coden-operator-demo/queue.sqlite3 \
  --journal /tmp/coden-operator-demo/journal \
  --task-dir ai_factory/examples
```

Omitting `--task-dir` skips checking the original JSON file fingerprint. The task payload is never printed, and the program never opens a network connection or launches coding tasks.

Return codes: **0** = report generated without detected anomalies; **1** = report generated with items requiring operator attention; **2** = report unavailable due to corrupted or missing input/schema. Even exit code 0 **does not authorize execution or restart**.

## Condition meanings

| Condition | Interpretation | Operator action |
|---|---|---|
| `consistent_queued` | Queue and checkpoint both at initial stage | May inspect next legitimate operator action; no automatic authorization |
| `active_unverified` | Worker lease and started journal, but may be currently running or dead | Check actual process, effects and lease; no retry |
| `claim_without_start_evidence` | Queue lease exists, but journal still initial | Investigate crash window before replay |
| `journal_ahead_of_queue` | Journal reached review/blocked while queue still leased | Inspect saved artifacts, decide manual reconciliation |
| `consistent_review` | Both stores indicate human review | Review evidence separately; no approval implied |
| `consistent_blocked` | Both stores indicate blocked/failed outcome | Follow error runbook |
| `manual_review_required` | Expired lease quarantined by queue | Inspect possible side effects, never requeue automatically |
| `missing_journal` / `invalid_journal` | Missing or corrupt/symlink journal | Stop, restore from trusted evidence only |
| `identity_mismatch` | Journal branch or commit differs from queued source | Stop and investigate identity integrity |
| `task_hash_mismatch` | Optional source task file changed or disappeared | Stop and compare trusted artifact SHA-256 |
| `orphan_journal` | Journal created without matching queue task | Investigate interruption during submission |
| `state_mismatch` | Other queue/journal state discrepancy | Human investigation |

## Acceptance evidence

- 12 tests added in `tests/test_factory_reconcile.py`; exercised successful snapshots, SQLite/journal divergence, orphan and corrupt records, leased-worker interruption, task hash change, and never-authorized output.
- CI [#44849279077](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44849279077) completed **134 unit tests** successfully, one conditional skip, with OpenAPI validation passing.

## Limitations to resolve before production

- The report is a **non-atomic snapshot**. If workers write concurrently, a false discrepancy may be seen. Freeze the worker first for a high-confidence incident audit.
- The tool only diagnoses; it cannot prove whether an external side effect completed.
- An attacker with filesystem privileges can alter multiple data stores and regenerate journal hashes. Operator-only permissions and independent signed evidence are needed.
- The scanner intentionally caps input size and number of entries to avoid excessive untrusted filesystem processing.
- A real recovery controller needs an operator-approved decision, verified artifact hashes, a durable outbox, safe idempotency keys and observable process cancellation. Those are **not yet built**.
- Do not feed citizen, beneficiary, financial, health, identity or governmental production data to this synthetic-only prototype.
