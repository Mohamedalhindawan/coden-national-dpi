# Local tooling benchmark · 2026-11-20

Reproduce from the PR with `python -m tools.bench.workflows` (Python 3.12, Git, sed and a local checkout containing the #117 base commit). The runner creates a disposable clone at `c49737b01ee679e95320fdb931fc807c7a05c963`. Both modes see identical files and the same synthetic log, with five alternating paired rounds per task on one machine. Executables: Python 3.12.14, Git 2.56.1. GitHub responses in the timed runs come from a local CLI fixture. No live network latency is represented.

The reference answers were fixed before the runs: locate the UI review operation and its specific contract test; locate the OpenAPI review operation and its specific contract test; identify the failing job, validation step and error. For source tasks the baseline runs Git grep and reads eight preceding lines to identify the test; the helper returns the enclosing test directly. For CI the baseline reads checks and a full log; the helper emits a bounded diagnostic. Other hand-tuned grep/log commands could perform differently. The scorer checks for the reference location and test or failure text. It does not grade a model response.

| Task | Mode | Five elapsed times (ms, run order) | Median [min–max] ms | Output bytes | Tool calls | Correct |
|---|---|---|---:|---:|---:|---:|
| markReviewed | before | 4.599, 4.27, 4.002, 4.833, 4.042 | 4.270 [4.002–4.833] | 698 | 2 | 5/5 |
| markReviewed | after | 43.474, 39.138, 40.624, 39.711, 50.405 | 40.624 [39.138–50.405] | 149 | 3 | 5/5 |
| recordReview | before | 4.876, 5.185, 3.862, 4.078, 3.717 | 4.078 [3.717–5.185] | 606 | 2 | 5/5 |
| recordReview | after | 42.452, 39.202, 39.355, 39.794, 38.059 | 39.355 [38.059–42.452] | 133 | 3 | 5/5 |
| CI | before | 41.619, 40.189, 40.127, 40.354, 39.871 | 40.189 [39.871–41.619] | 1100 | 2 | 5/5 |
| CI | after | 120.872, 118.959, 117.767, 122.494, 128.124 | 120.872 [117.767–128.124] | 431 | 6 | 5/5 |

Bytes cover stdout returned to the caller, including discovery output. Calls count executed git/gh commands including nested ones, plus top-level Python or sed when used. Timing includes process startup, shim instrumentation and local file reads. Bytes and calls were constant within each row. The runner prints each raw observation with its output digest. All six rows had a stable digest across five runs. Incorrect outputs: 0/30. Retry/rework attempts: 0 (single-pass tasks). All 30 measurements met their correctness oracle. Both context lookups and CI used fewer output bytes. All three took longer and invoked more processes. The adoption criterion was met; offer context lookup for tasks that need source and test together. No claim of an overall Codex speedup follows from these timings.

Base suite: 11/11 passed. Worktree suite and mutation evidence are in the PR and optimization plan. The initial pre-implementation suite intentionally failed with missing helpers; the old gh compatibility regression was reproduced separately. Model tokens, model reliability, independent model review, human rework time and estimated/actual account billing: **NOT MEASURED**. No model requests were made.
