# Offline review queue

Use `python -m ai_factory.review_queue path/to/synthetic-tasks.json` to validate a JSON **array** of tasks and produce approval-gated plans. A batch is rejected in full if any task is invalid or has a duplicate ID.

Example task:

```json
[{"id":"DEMO-1","title":"Synthetic demo","description":"Build a synthetic-only test","data_classification":"synthetic","requested_actions":["run_tests"]}]
```

This command **does not run Codex, invoke tools, create branches, write output files, grant approval, or call a model**. It prints JSON to standard output. Nonzero exit status means rejection. All accepted plans still have `execution_authorized: false` and `awaiting_human_approval`.

Run tests: `python -m unittest discover -s tests -v`. This is a stacked change on draft PR #116, not a competing intake implementation.
