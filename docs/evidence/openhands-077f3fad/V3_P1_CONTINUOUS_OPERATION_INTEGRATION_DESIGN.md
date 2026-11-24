# v3.0 P1 continuous operation — integration design checkpoint
2026-11-24 | proposed; no deployment, execution or new approvals.
Scope: sections 21–30, 123, 145, 151 of v3.0. P0 #162 remains the critical path.

## Verified reuse
Compared exact blobs in #140 a05708cf8cdd0a17eb610d7d413ee2b2c28eeb49 and #191 e72c83d1f3bc2ce1abc00c1993144a6edba9112d: identical durable_queue.py 128cfc7dd10a28867be54fa0b1e7f33a2868a0db, checkpoint.py 8a03aafff5d5a85dbc80454f8c2c92da42ed2e27, project.py 3e4c22f37d57ce25acd792bf87c1108ea1b55ffb. Do not recreate these modules. Reviewed #140 offline_worker.py ba6fb4297e4cda8be038990b87804f0e908de773 and worker_supervisor.py 3bb97578d7893ec2c82d38728c00f2053288e87c; fixed one-task synthetic recipe, no daemon, no retry, one heartbeat before execution, checkpoint-before-enqueue, process-group termination best effort (not a sandbox). Reviewed #150 exact migration blob 6ac82e7f33ba168ea835ad39c0eb1c306cbdb72f: private coden_factory jobs/events metadata only; synthetic data, zero spend, provider_approved=false and execution_authorized=false enforced by SQL constraints. No runnable queue, lease or scheduler. No live database inspected or changed.

## Proposed integration boundary
Use the existing SQLite queue as sole authoritative execution lease store for first single-host synthetic pilot; Supabase remains optional operator-facing metadata only. Do not create a second execution authority or forward service-role keys to workers. No schema migration or provider routing before review. Adopt #140 exact worker/supervisor and tests into a reviewable branch only after comparing dependency and test compatibility; avoid parallel replacement modules. Existing lease expires into needs_review, never queued. Preserve this behavior. Queue worker_id is returned but not persisted, lease token is the current fencing credential; never publish it in telemetry. Durable supervisor and trusted artifact verifier remain separate from untrusted code.

## Acceptance matrix (planned tests, not executed)
| ID | Injection / condition | Required outcome |
|---|---|---|
| P1-01 | Same task ID and digest submitted twice | One admission; safe idempotent receipt only after checking immutable identity; conflicting digest rejected |
| P1-02 | Crash after checkpoint creation, before enqueue | Orphan detected and quarantined, no silent execution |
| P1-03 | Two workers attempt to claim one job | At most one valid lease; stale token cannot finish |
| P1-04 | Crash after artifact write before queue finish | Verify artifact and journal, quarantine; no repeat external effects |
| P1-05 | Timeout with child process | Independent process-tree cleanup under cgroup boundary, not merely leader exit |
| P1-06 | Cancellation during leased work | Fence further effects, terminate process tree, retain evidence; do not treat as completed |
| P1-07 | Worker restart and lease expiry | needs_review with evidence, no unattended replay |
| P1-08 | Supabase metadata unavailable | Local lease authority remains consistent; bounded sync and no duplicate events once approved |
| P1-09 | Invalid artifact or mismatched task digest | Fail closed and human review |
| P1-10 | Restore from backup / restart | Verify state and artifact checksums; no duplicate work or lost review |
| P1-11 | Repeated transient safe failures | Bounded retries only for explicitly classified idempotent operations; no auto replay of ambiguous executions |
| P1-12 | Health check and missed heartbeat | Alert and recorded escalation without exposing secrets |

## Pilot exit
Independent integrated tests; persisted worker ownership/fencing and heartbeat semantics, cancellation/reconciliation reviewed, bounded disk/process/network and operator permissions, evidence redaction, restart/restore drill, durable host and alerts demonstrated before any 24/7 assertion. No auto-merge, paid API or release. Scope does not authorize live OpenHands Conversation or change #162. Proposed design is not an implementation; P1 may be reviewed in parallel, admission remains after P0.
