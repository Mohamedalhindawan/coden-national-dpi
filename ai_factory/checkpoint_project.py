"""Opt-in checkpoint wrapper for the existing offline, synthetic-only project pilot.

This is not a background worker, approval service or model router. The operator
must invoke it explicitly. It refuses to re-run an already recorded task ID.
"""

import argparse
import json
from pathlib import Path
import sys

from . import checkpoint, project


def run_with_checkpoint(task, root, store, *, branch, commit, source_path=None, local_assets=None):
    """Persist the local pilot's start/end state without granting release approval."""
    if not project.valid(task):
        raise ValueError("invalid synthetic factory task")
    checkpoint.create(store, task["id"], branch=branch, commit=commit)
    checkpoint.record(store, task["id"], event="checkpoint", next_action="offline_project_run")
    try:
        directory, result = project.run(task, root, source_path, local_assets=local_assets)
    except Exception:
        checkpoint.record(store, task["id"], event="worker_failed", next_action="inspect_worker_failure")
        raise
    if result == "awaiting_human_review":
        event, next_action = "review_requested", "human_review"
    elif result in ("blocked", "failed"):
        event, next_action = "blocked", "inspect_offline_logs"
    else:
        checkpoint.record(store, task["id"], event="blocked", next_action="inspect_unknown_status")
        raise RuntimeError("unsupported project status")
    final_state = checkpoint.record(store, task["id"], event=event, next_action=next_action)
    return {"directory": directory, "status": result, "journal": final_state}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path, default=project.EXAMPLE)
    parser.add_argument("--output-root", type=Path, required=True, help="Existing offline output directory")
    parser.add_argument("--store", type=Path, required=True, help="Operator-owned checkpoint directory")
    parser.add_argument("--branch", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--source", type=Path, help="Optional reviewed local transform(value) source")
    args = parser.parse_args(argv)
    try:
        task = json.loads(args.task.read_text(encoding="utf-8"))
        result = run_with_checkpoint(task, args.output_root, args.store, branch=args.branch,
                                     commit=args.commit, source_path=args.source)
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        print(f"Offline factory wrapper error ({type(exc).__name__})", file=sys.stderr)
        return 2
    print(json.dumps({"directory": str(result["directory"]), "status": result["status"],
                      "journal": result["journal"]}, sort_keys=True))
    return 0 if result["status"] == "awaiting_human_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
