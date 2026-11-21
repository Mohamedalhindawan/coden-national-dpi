# CODEN Factory Checkpoint & Recovery Foundation

**Status:** experimental, offline, operator-controlled; **not** a running orchestrator and not an approved agent fallback.  
**Parent implementation:** PR #126 (stacked on #124/#118/#116).  
**Adopt-First catalog:** PR #130, Issue #131.  
**Platform:** Linux/POSIX Python 3.12+ standard library (uses `fcntl` and `O_NOFOLLOW`).

## What is actually implemented

`ai_factory/checkpoint.py` is a standalone checkpoint **journal**, not a new worker, agent, provider, database service or runtime. It supports:

- A task ID and a source branch plus **40-character Git commit SHA**, with no task prompts or secrets stored.
- Append-only JSONL events: `checkpoint`, `quota_exceeded`, `context_exceeded`, `provider_unavailable`, `budget_exceeded`, `worker_failed`, `blocked`, `resume_requested`, `review_requested`.
- Last commit, last branch, next **action identifier** (not a shell command), status and pause reason.
- Sequence validation, per-event SHA-256 chain, exclusive local file locks, fsync, basic size limits, refusal of symlinked journal files, idempotency keys and fail-closed corrupted record detection.
- A `pending_human_resume` state that is *not* permission to run.

The opt-in `ai_factory/checkpoint_project.py` adapter now calls the existing synthetic-only offline project runner, records start/blocked/review/worker-failure states, and rejects duplicate task IDs. This does **not** detect a provider quota or resume a model session. It cannot launch OpenHands or Hermes or pay for a model.

## Operator commands (offline only)

Run from repository root, with a directory owned by the human operator and not writable by untrusted agent code.

```bash
# Do not put the journal inside a sandbox or AI-writable workspace.
STORE=/tmp/coden-checkpoints-demo
TASK=synthetic_factory_task_001
COMMIT=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa

python -m ai_factory.checkpoint --store "$STORE" create "$TASK" \
  --branch feat/factory-adopt-first --commit "$COMMIT"

python -m ai_factory.checkpoint --store "$STORE" record "$TASK" \
  --event checkpoint --next-action verify_candidate_tests --event-key milestone_01

python -m ai_factory.checkpoint --store "$STORE" record "$TASK" \
  --event quota_exceeded --next-action assess_authorized_fallback --event-key quota_01

python -m ai_factory.checkpoint --store "$STORE" show "$TASK"

# Only records an operator's intention, it does not approve or execute.
python -m ai_factory.checkpoint --store "$STORE" record "$TASK" \
  --event resume_requested --event-key human_requested_01
```

Use a real repository commit SHA for actual work. The all-`a` string above is an **illustrative syntactically valid** SHA for a local demo only.

Run the existing offline factory through the optional adapter (only in an environment meeting the existing sandbox requirements):

```bash
mkdir -p /tmp/coden-demo-output
python -m ai_factory.checkpoint_project \
  --task ai_factory/examples/status-counts.json \
  --output-root /tmp/coden-demo-output \
  --store /tmp/coden-demo-checkpoints \
  --branch feat/factory-adopt-first \
  --commit "$COMMIT"
```

Use a new, reviewed task ID for a new authorized run; the adapter never silently re-executes the same task.

Run focused tests:

```bash
python -m unittest discover -s tests -p 'test_factory_checkpoint.py' -v
python -m unittest discover -s tests -p 'test_checkpoint_project.py' -v
```

Run the repository test suite:

```bash
python -m unittest discover -s tests -v
```

Some earlier project tests require pinned Ruff, Linux bubblewrap and `prlimit`; see `docs/FACTORY_PROJECT_RUNBOOK.md`. This checkpoint-only test suite has no third-party Python dependencies.

## Crash recovery semantics

- The journal is the source of truth, not model context. Reading verifies all records and reconstructs the last known state.
- A task can be **paused** on quota/context/budget/provider/worker failure and can be **marked pending human resume**.
- A stopped Codex session, a branch, and a checkpoint are distinct things; no workflow runner is restored automatically in this release.
- A crash that truncates a record makes the journal unreadable **by design**. An operator must recover from a trusted backup or perform a reviewed repair; don't auto-discard or rewrite failed evidence.
- Records stay on the operator's disk. This is not replicated high availability or a database durable workflow system. Back up off-agent, enforce access controls and retention.
- The SHA-256 hash chain is **not a cryptographic authentication signature**: an attacker with filesystem write rights can rewrite and rehash. Protect permissions and retain off-host audit evidence before production use.

## Security invariants

- Never add prompts, secrets, private data, user data, personal records or provider cookies to journal events.
- The checkpoint module **never** grants approval; every returned state has `execution_authorized: false`.
- The module **never** switches model/provider, retries a paid call, alters GitHub, merges a PR, deploys or executes shell commands.
- Keep stores separate per environment and restrict filesystem permissions. No production claims from these tests.
- A gateway that consumes unofficial subscription/cookie endpoints must be rejected pending written provider authorization and security approval.

## Codex integration work still remaining

1. The opt-in `checkpoint_project.py` wrapper for the existing `project.py` pilot is implemented and tested; connect `phase_zero.py` only if justified, and preserve original evidence.
2. Design an authorized **durable queue and worker**; do not equate `resume_requested` with authorization.
3. Implement a provider-agnostic error classifier and test simulated `quota_exceeded`, `context_exceeded` and upstream failure without real paid accounts.
4. Compare OmniRoute/LiteLLM/Bifrost for approved API connectors; select **one primary gateway**. Local models remain bounded by compute.
5. Evaluate OpenHands Agent Canvas/SDK for runtime, Hermes for learning, and bounded Hermes Self-Evolution for CAIE.
6. Run integration, security and independent acceptance tests on a synthetic multi-file codebase; checkpoint, restart and test an end-to-end PR handoff.
7. Persist operational state in PostgreSQL or a tested durable workflow engine when required. Document migrations, cleanup, retention, backup/restore and RPO/RTO.

**The next Codex session should start here, not rebuild the existing PR chain.**
