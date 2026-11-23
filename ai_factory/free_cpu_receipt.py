"""Verify a CODEN offline CPU model pilot without trusting generated code.

The receipt authenticates the factory's output structure and reviewed hashes;
it cannot, by itself, prove model execution. The live CI workflow proves model
invocation by executing pinned llama.cpp and hash-verified Qwen weights.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ORIGIN = "local Qwen2.5-Coder / llama.cpp b12600"
MODEL = "Qwen2.5-Coder-0.5B-Instruct-Q4_K_M"


def _read_json(path, limit=16384):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError("missing, oversized, or symlinked receipt")
    return json.loads(path.read_text(encoding="utf-8"))


def _exact_event(events, *, role, state):
    matches = [
        event for event in events
        if event.get("role") == role and event.get("state") == state
    ]
    if len(matches) != 1:
        raise ValueError("missing or ambiguous factory event")
    return matches[0]


def inspect(result_file, output_root):
    """Return a sanitized model receipt or raise ValueError, without executing."""
    root = Path(output_root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("trusted output directory missing")
    root = root.resolve(strict=True)
    result = _read_json(Path(result_file), 4096)
    if not isinstance(result, dict) or result.get("status") != "awaiting_human_review":
        raise ValueError("factory did not pass independent review")
    work_name = result.get("directory")
    if not isinstance(work_name, str) or not work_name.startswith(str(root) + "/"):
        raise ValueError("factory directory outside trusted output root")
    work = Path(work_name)
    if (work.is_symlink() or not work.is_dir() or work.parent.resolve() != root
            or not work.name.startswith("coden-project-")):
        raise ValueError("unexpected output directory")

    receipt = _read_json(work / "review.json")
    artifact = work / "candidate.pyz"
    if artifact.is_symlink() or not artifact.is_file() or artifact.stat().st_size > 2_000_000:
        raise ValueError("reviewed package missing or too large")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    if (
        not isinstance(receipt, dict)
        or receipt.get("status") != "awaiting_human_review"
        or receipt.get("release_authorized") is not False
        or receipt.get("sha256") != digest
        or type(receipt.get("review_cases")) is not int
        or not 1 <= receipt["review_cases"] <= 8
    ):
        raise ValueError("review receipt does not bind exact unapproved artifact")

    events_path = work / "events.jsonl"
    if (events_path.is_symlink() or not events_path.is_file()
            or events_path.stat().st_size > 65536):
        raise ValueError("untrusted or missing event history")
    lines = events_path.read_text(encoding="utf-8").splitlines()
    if not 5 <= len(lines) <= 32:
        raise ValueError("unexpected factory event count")
    try:
        events = [json.loads(line) for line in lines]
    except json.JSONDecodeError as exc:
        raise ValueError("malformed event history") from exc
    if any(not isinstance(event, dict) for event in events):
        raise ValueError("invalid event object")
    planned = _exact_event(events, role="orchestrator", state="planned")
    coding = _exact_event(events, role="coding", state="complete")
    testing = _exact_event(events, role="testing", state="passed")
    review = _exact_event(events, role="review", state="passed")
    _exact_event(events, role="orchestrator", state="awaiting_human_review")
    if (planned.get("paid_calls") != 0 or planned.get("budget_usd") != 0
            or not isinstance(planned.get("task_id"), str)
            or not 1 <= len(planned["task_id"]) <= 64):
        raise ValueError("invalid task or nonzero model spend")
    if coding.get("input") != ORIGIN:
        raise ValueError("model-origin event absent")
    if type(testing.get("verified_cases")) is not int or testing["verified_cases"] < 1:
        raise ValueError("missing implementation acceptance test")
    if (review.get("release_authorized") is not False
            or review.get("sha256") != digest
            or review.get("review_cases") != receipt["review_cases"]):
        raise ValueError("review event does not bind the tested package")

    return {
        "status": "awaiting_human_review",
        "model": MODEL,
        "task_id": planned["task_id"],
        "verified_cases": testing["verified_cases"],
        "independent_review_cases": receipt["review_cases"],
        "artifact_sha256": digest,
        "paid_calls": 0,
        "budget_usd": 0,
        "release_authorized": False,
        "evidence_kind": "local_cpu_model_workflow_event_and_independent_acceptance",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        summary = inspect(args.result, args.root)
        if args.summary.is_symlink() or not args.summary.parent.is_dir():
            raise ValueError("invalid evidence target")
        args.summary.write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Model evidence BLOCKED ({type(exc).__name__})\n")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
