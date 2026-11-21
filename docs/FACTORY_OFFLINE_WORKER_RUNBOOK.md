# CODEN AI Factory — operator-invoked offline worker

**Status:** narrow, tested experimental runner; **NOT** a running 24/7 factory, Codex resumer, autonomous model router, or production deployment.  
**Implementation:** `ai_factory/offline_worker.py`, `ai_factory/durable_queue.py`, `ai_factory/checkpoint.py`, existing `ai_factory/project.py`.  
**Scope:** synthetic `status-counts` JSON transform recipe only. Existing pilot has one code-generation stage with deterministic verification roles, not eight autonomous LLM agents.

## What the code does

An operator can **submit** a previously reviewed JSON task file to a persistent local SQLite queue. The queue stores **task ID, branch, full commit SHA, content SHA-256**, not the prompt, code or secrets. Submission separately creates a checkpoint journal in an operator-owned folder.

An operator can then run **one** pending item using the existing offline Python pilot. The worker:

1. Atomically claims one task with a time-limited lease and single-owner token.
2. Reopens the task JSON and verifies its SHA-256 and synthetic-only constraints.
3. Verifies the checkpoint's initial state, source branch and commit.
4. Extends its lease before calling the existing sandboxed project runner.
5. Records review-needed or blocked outcome to the checkpoint journal, then closes the queue lease.
6. Never merges code, deploys, authorizes a task, pays for tokens or invokes a cloud provider.

On interrupted execution, the lease is not automatically re-queued. An operator uses `inspect-expired` to move it to `needs_review`. This protects against unintentional repeated code changes or PR creation when eventual workers gain broader capabilities.

## Run a synthetic demo

Requirements are the **pinned Linux sandbox and Ruff dependencies** described in `FACTORY_PROJECT_RUNBOOK.md`. The commands below are examples, not server provisioning.

```bash
# Work on a trusted, private operator environment.
mkdir -p /tmp/coden-operator-demo/outputs

python -m ai_factory.offline_worker \
  --queue-db /tmp/coden-operator-demo/queue.sqlite3 \
  --journal /tmp/coden-operator-demo/journal \
  --task-dir ai_factory/examples \
  submit DEMO-STATUS-COUNTS \
  --branch feat/factory-checkpoint-recovery-foundation-20261121 \
  --commit "$(git rev-parse HEAD)"

python -m ai_factory.offline_worker \
  --queue-db /tmp/coden-operator-demo/queue.sqlite3 \
  --journal /tmp/coden-operator-demo/journal \
  --task-dir ai_factory/examples \
  work-once --output-root /tmp/coden-operator-demo/outputs

python -m ai_factory.checkpoint \
  --store /tmp/coden-operator-demo/journal show DEMO-STATUS-COUNTS
```

The successful result is `awaiting_human_review`, **not** an approval. Do not re-submit the same task ID. A new reviewed run must use a distinct task identifier, because even a failed prior run may have produced artifacts.

To inspect interrupted execution without automatically restarting:

```bash
python -m ai_factory.offline_worker \
  --queue-db /tmp/coden-operator-demo/queue.sqlite3 \
  --journal /tmp/coden-operator-demo/journal \
  --task-dir ai_factory/examples \
  inspect-expired
```

## Review and security limits

- The operator running `work-once` is explicitly initiating **only** the local synthetic test operation; queue records never grant future general authority.
- Task files and SQLite/checkpoint directories must be protected from untrusted agent writes. A SHA-256 checksum detects changes to task content between submission and loading, but an attacker with operator filesystem privileges can alter multiple stores.
- JSON input is bounded and rejects duplicate fields and symlinks at the leaf, plus synthetic/non-approval restrictions. Do not treat this as a full malicious-filesystem isolation boundary.
- Existing `project.run` is responsible for its **bubblewrap/prlimit** checks. Missing sandbox resources block execution; there is no unsafe host fallback.
- Journal and SQLite transitions are **separate** (no cross-store atomic transaction). After a process crash, an operator must reconcile evidence manually. Do not auto-run a task merely because SQLite says `queued` or `leased`.
- A lease is NOT a subprocess cancellation mechanism. Timeouts require explicit worker runtime controls before generalized or background operation.
- Do not use official-sector or citizen/financial/health data in this pilot.
- GitHub CI and local unit tests establish the limited synthetic path only, not multi-service software delivery or uninterrupted 24/7 availability.

## Test commands

```bash
python -m unittest discover -s tests -p 'test_offline_worker.py' -v
python -m unittest discover -s tests -v
```

## Next Codex milestones

1. Introduce operator-trusted, tamper-evident reconciliation between the journal, queue and artifacts, and test crash windows after each state transition.
2. Add a bounded worker process supervisor with cancellation and checkpointed restart, while **never** replaying non-idempotent side effects automatically.
3. Evolve from this synthetic `status-counts` recipe into a reviewed multi-file project acceptance fixture with independent tests.
4. Implement external LLM adapters only with authorized credentials and provider terms; compare OmniRoute, LiteLLM and Bifrost, and choose **one** model gateway if needed.
5. Pilot OpenHands and Hermes separately against synthetic tasks, then measure cost, quality and runtime before activation.
6. Maintain approval gates, security scans, sandboxing, and the unmerged PR dependency chain.
