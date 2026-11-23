"""Review-only Factory self-development work order bound to approved Plan v1.0.

An actual Qwen program is executed only by the separate, existing project
bubblewrap sandbox. This report consumes its verified receipt, not its code.
Never imports generated code, performs worker mutations or authorizes release.
"""
import argparse
import json
from pathlib import Path
import re
import sys

from . import project

ROOT = Path(__file__).resolve().parents[1]
PLAN_BLOB = "3476b956555db136dbc4bc41b78d93ac881b10f1"
PLAN_COMMIT = "377d8756f0d62156def5de5f4c7bb64caac9bca8"
TASK_FILE = ROOT / "ai_factory/examples/factory-worker-recovery-v1.json"
ORDER_FILE = ROOT / "configs/factory_v1_worker_recovery_work_order.json"
SECTIONS = [19, 22, 49, 51, 63, 66, 72, 80]
ALLOWED_REFS = {
    "worker_draft_pr": 140,
    "runtime_isolation_issue": 162,
    "supabase_draft_pr": 150,
    "founder_plan_draft_pr": 168,
    "real_model_precedent_draft_pr": 164,
}
NEXT = (
    ("ISOLATE_OPENHANDS", "BLOCKED"),
    ("REVIEW_WORKER", "REVIEW_REQUIRED"),
    ("REVIEW_SUPABASE", "REVIEW_REQUIRED"),
    ("EVALUATE_MODEL_CANDIDATE", "REVIEW_REQUIRED"),
)
LABELS = frozenset(("lease_expired", "cancel_requested"))


def _json(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 32768:
        raise ValueError("untrusted task/approval file")
    return json.loads(path.read_text(encoding="utf-8"))


def _check_cases(task):
    for kind in ("cases", "review_cases"):
        for row in task[kind]:
            if not isinstance(row["input"], list) or any(
                not isinstance(x, str) or len(x) > 80 for x in row["input"]
            ):
                raise ValueError("untrusted synthetic state")
            expected = sum(1 for x in row["input"] if x in LABELS)
            if type(row["expected"]) is not int or row["expected"] != expected:
                raise ValueError("task has invalid acceptance oracle")


def build_work_order(order, task, receipt=None):
    """Strictly validate the frozen plan and separate generated-code receipt."""
    if not isinstance(order, dict) or not project.valid(task):
        raise ValueError("invalid factory work order or task")
    if any((
        order.get("schema_version") != "0.1.0",
        order.get("plan_version") != "v1.0",
        order.get("plan_git_blob_sha1") != PLAN_BLOB,
        order.get("plan_source_commit") != PLAN_COMMIT,
        order.get("plan_path") != "docs/CODEN_AI_FACTORY_MASTER_PLAN_v1.0_APPROVED.md",
        order.get("plan_section_ids") != SECTIONS,
        order.get("task_id") != "CODEN-V1-WORKER-RECOVERY-03",
        task.get("id") != order.get("task_id"),
        task.get("recipe") != "python-transform",
        task.get("requested_actions") != ["run_tests"],
        task.get("estimated_cost_usd") != 0,
        task.get("data_classification") != "synthetic",
        task.get("description") != order.get("task_description"),
        order.get("task_file") != "ai_factory/examples/factory-worker-recovery-v1.json",
        order.get("stage") != "CANDIDATE_CODE_REVIEW_ONLY",
        order.get("factory_production_authorized") is not False,
        order.get("model_candidate_promoted") is not False,
        order.get("open_hands_live_runtime_verified") is not False,
        order.get("automatic_merge") is not False,
        order.get("paid_calls") != 0,
        order.get("references") != ALLOWED_REFS,
        not isinstance(order.get("next_steps"), list),
        len(order["next_steps"]) != len(NEXT),
    )):
        raise ValueError("plan scope changed or runtime permission escalation")
    if (not isinstance(task["description"], str)
            or "lease_expired" not in task["description"]
            or "cancel_requested" not in task["description"]
            or "not permission" not in task["description"].lower()
            or len(task["cases"]) != 3 or len(task["review_cases"]) != 3):
        raise ValueError("unsafe work order prompt")
    _check_cases(task)
    for step, (expected_id, expected_status) in zip(order["next_steps"], NEXT):
        if (not isinstance(step, dict) or step.get("id") != expected_id
                or step.get("status") != expected_status
                or not isinstance(step.get("action"), str)
                or not isinstance(step.get("owner"), str)
                or len(step["action"]) < 12):
            raise ValueError("unexpected work order dependencies")
    result = dict(order)
    result["next_steps"] = [x.copy() for x in order["next_steps"]]
    result["candidate_verified_by_receipt"] = False
    result["model_artifact_sha256"] = None
    result["release_authorized"] = False
    result["source_catalog_modified"] = False
    result["worker_mutated"] = False
    if receipt is not None:
        if (not isinstance(receipt, dict)
                or receipt.get("task_id") != task["id"]
                or receipt.get("status") != "awaiting_human_review"
                or type(receipt.get("verified_cases")) is not int
                or receipt["verified_cases"] != 3
                or type(receipt.get("independent_review_cases")) is not int
                or receipt["independent_review_cases"] != 3
                or receipt.get("release_authorized") is not False
                or receipt.get("paid_calls") != 0
                or receipt.get("budget_usd") != 0
                or not isinstance(receipt.get("artifact_sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", receipt["artifact_sha256"])):
            raise ValueError("model receipt failed independent acceptance")
        result["candidate_verified_by_receipt"] = True
        result["model_artifact_sha256"] = receipt["artifact_sha256"]
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path, default=TASK_FILE)
    parser.add_argument("--order", type=Path, default=ORDER_FILE)
    parser.add_argument("--model-receipt", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        receipt = _json(args.model_receipt) if args.model_receipt else None
        result = build_work_order(_json(args.order), _json(args.task), receipt)
        target = args.output
        if target.is_symlink() or target.exists() or not target.parent.is_dir():
            raise ValueError("work order output must be fresh and local")
        target.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (ValueError, OSError, TypeError, KeyError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Factory v1 work order BLOCKED ({type(exc).__name__})\n")
    print(json.dumps({
        "task_id": result["task_id"],
        "candidate_verified_by_receipt": result["candidate_verified_by_receipt"],
        "release_authorized": False,
        "worker_mutated": False,
        "next_step_status": result["next_steps"][0]["status"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
