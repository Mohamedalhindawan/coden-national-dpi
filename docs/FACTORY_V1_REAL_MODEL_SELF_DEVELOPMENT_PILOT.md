# CODEN AI Factory v1.0 — supervised real-model help completing the implementation plan

**Execution scope:** an actual local-model, read-only self-development trial; **NOT** a production autonomous software factory, OpenHands multi-file session, live Worker or newly merged code.

- **Approved plan reference:** [CODEN AI FACTORY v1.0](https://github.com/Mohamedalhindawan/coden-national-dpi/blob/377d8756f0d62156def5de5f4c7bb64caac9bca8/docs/CODEN_AI_FACTORY_MASTER_PLAN_v1.0_APPROVED.md), approved by the founder internally in Draft PR #168; Git blob SHA-1 `3476b956555db136dbc4bc41b78d93ac881b10f1`. The canonical plan text and its 80 numbered sections are **not edited** by this engineering PR.
- **This Pilot Draft PR:** #169, stacked on #164 → #155 → #151; all unmerged; no changes to main.
- **Sections exercised:** 19 Task Management Engine, 22 sandbox isolation, 49 baseline, 51 Trusted Worker/control, 63 missing integration files, 66 Batch 03, 72 self-development acceptance and 80 production readiness.
- **Task ID:** `CODEN-V1-WORKER-RECOVERY-03`.

## What the actual model is asked to build

Qwen2.5-Coder-0.5B-Instruct-Q4_K_M via pinned, free CPU `llama.cpp b12600` is asked to generate an original single `transform(value)` function that **counts states** requiring recovery or cancellation review: exact `lease_expired` and `cancel_requested` values in a synthetic list. All other states are ignored; duplicate flags are counted individually.

This intentionally narrow capability can help estimate Worker's recovery backlog, but cannot cancel, recover, mutate, retry or execute any Worker task. It is **not** a real lease-manager implementation and does not prove idempotency or crash recovery.

The workflow uses the **existing** vetted free-Qwen generator (`ai_factory.local_coder`), existing `ai_factory.project` TDD/AST/Ruff/bubblewrap pipeline, existing model evidence inspector and independent held-out tests, rather than copying an entire new agent engine. It runs only on the first-party named Draft PR branch, with `contents: read`, no persisted GitHub credentials and **no paid providers**.

## New stage: factory-generated work order for the next implementation pass

The factory emits an additional `factory-v1-next-work-order.json` after verifying the real model receipt and independent test gates. The work order is bound to the frozen v1 plan blob, section numbers, model artifact SHA-256 and observed CI evidence.

It explicitly retains the next required dependent actions:
1. **BLOCKED** — OpenHands real container sandbox preconditions: CPU/memory/PID restrictions, trusted image and network egress from issue #162; do not circumvent them.
2. **REVIEW_REQUIRED** — Draft Worker PR #140: test real leases, cancellation, crash recovery and idempotency before approval.
3. **REVIEW_REQUIRED** — Draft Supabase PR #150: trusted worker authentication, RLS and replay-resistant control-plane integration.
4. **REVIEW_REQUIRED** — review this real-model-generated code, test independent acceptance, and decide whether a small integration PR is justified.

**Human review:** required for all changes. `release_authorized=false`, `automatic_merge=false`, `model_candidate_promoted=false`, `worker_mutated=false`, `factory_production_authorized=false`, `open_hands_live_runtime_verified=false`, `paid_calls=0`.

## Evidence and independent verification

- The real-model workflow `.github/workflows/factory-v1-worker-recovery-real-qwen.yml` downloads the pinned public GGUF and llama.cpp tarball and verifies both SHA-256 values **before** inference.
- Only limited, synthetic generated source is executable in the independent `bubblewrap 0.12.0` sandbox.
- 3 public cases, 3 independent held-out cases, strict single-function AST gate, Ruff checks, model-origin event, SHA-256 artifact/package receipt.
- A separate **80 synthetic Worker-state record scale test** exercises the actual generated zipapp. Independently expected recovery actions: 32. No real queue or Worker is accessed.
- On a pass, the verified candidate package, `model_receipt.json`, `review.json`, `worker-recovery-synthetic-scale.json`, and `factory-v1-next-work-order.json` are retained in a GitHub Actions artifact for operator inspection.
- **Source code promotion is denied:** output is a review-only candidate, not a CODEN production Worker or automatic improvement of its security policy.
- On failure, GitHub Actions must fail and only a redacted failure-stage diagnostic can appear. A canned fixture or mock cannot turn a failed model run into a pass.

## Reproduce non-inference contracts

```bash
python -m unittest discover -s tests -p 'test_factory_v1_worker_recovery_model.py' -v
python -m ai_factory.factory_v1_assisted_workorder \
  --task ai_factory/examples/factory-worker-recovery-v1.json \
  --order configs/factory_v1_worker_recovery_work_order.json \
  --output /tmp/coden-factory-v1-unapproved-work-order.json
```

The second command **never invokes a model** and emits an unverified review-only plan when used without `--model-receipt`. Only the separate real-model workflow establishes actual inference evidence and returns `candidate_verified_by_receipt=true` after the verified run.

The next true readiness milestone is **one real OpenHands-generated three-file project with independent acceptance, following proof of issue #162 isolation**. This trial does not change that goal.
