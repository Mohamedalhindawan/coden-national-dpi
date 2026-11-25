"""Bounded synthetic model benchmark. No tools or SDK are executed."""
import json
from pathlib import Path
import sys
from ai_factory.factory_qwen_tool_schema import evaluate_response, MAX_RESPONSE_BYTES

CASES = {
    "count": {"prompt": "Use a tool to count these flags: queued, ready, done. Preserve their order.", "expected_tool": "count_flags", "expected_args": {"flags": ["queued", "ready", "done"]}},
    "summary": {"prompt": "Use a tool to describe these flags in prose: ready, queued. Preserve their order.", "expected_tool": "summarize_flags", "expected_args": {"flags": ["ready", "queued"]}},
    "limit": {"prompt": "Use a tool to set the maximum number of synthetic records to 3.", "expected_tool": "set_limit", "expected_args": {"limit": 3}},
    "empty": {"prompt": "Use a tool to count flags in an empty array.", "expected_tool": "count_flags", "expected_args": {"flags": []}},
}
TOOLS = (
    ("count_flags", "Count the number of flags in an input array", "flags", {"type": "array", "items": {"type": "string"}}),
    ("summarize_flags", "Describe flags in prose", "flags", {"type": "array", "items": {"type": "string"}}),
    ("set_limit", "Prepare a proposed maximum record count in a synthetic test. Accept the requested whole number as a numeric argument. This tool only describes a proposed limit.", "limit", {"type": "integer", "description": "The maximum number of synthetic records requested, as a whole number, not text."}),
)


def request_for(case_id):
    case = CASES[case_id]
    return {"model": "local-qwen", "messages": [{"role": "user", "content": case["prompt"] + " Call the tool; do not answer in text."}],
            "tools": [{"type": "function", "function": {"name": name, "description": desc,
                      "parameters": {"type": "object", "properties": {key: schema},
                                     "required": [key], "additionalProperties": False}}}
                      for name, desc, key, schema in TOOLS],
            "tool_choice": "auto", "stream": False, "max_tokens": 128, "temperature": 0, "seed": 7}


def audit_case(case_id, raw):
    case = CASES[case_id]
    return evaluate_response(raw, expected_tool=case["expected_tool"], expected_args=case["expected_args"])


def _reject_capture(reason):
    return {"status": "schema_rejected", "reason_code": reason,
            "tool_executed": False, "sdk_conversation_ran": False,
            "release_authorized": False, "production_authorized": False,
            "automatic_retry_allowed": False}


def _audit_local_case(case_id, raw):
    """Validate captured response content, without claiming a transport status."""
    if type(case_id) is not str or case_id not in CASES or type(raw) is not bytes:
        return _reject_capture("invalid_transport_outcome")
    verdict = audit_case(case_id, raw)
    if verdict["status"] == "schema_match":
        # The schema audit rejects oversized, duplicate-key or malformed JSON.
        if json.loads(raw).get("model") != "local-qwen":
            return _reject_capture("model_identity_mismatch")
    return {**verdict, "automatic_retry_allowed": False}


def audit_http_case(case_id, *, status_code=None, raw=b"", failure=None):
    """Review a captured synthetic HTTP outcome; never perform a request.

    The caller must obtain transport status from an independently confined
    probe, not from model text. This classifier does not prove cancellation,
    authentication, DNS isolation or SDK compatibility at runtime.
    """
    if failure is not None:
        if type(failure) is str and failure in ("timeout", "cancelled"):
            return _reject_capture(failure)
        return _reject_capture("invalid_transport_outcome")
    if type(status_code) is not int:
        return _reject_capture("invalid_transport_outcome")
    if status_code in (401, 403):
        return _reject_capture("authentication_failed")
    if status_code != 200:
        return _reject_capture("http_status_rejected")
    return _audit_local_case(case_id, raw)


def summarize(results):
    passed = sum(i in results and results[i].get("status") == "schema_match" for i in CASES)
    complete = set(results) == set(CASES) and passed == len(CASES)
    return {"status": "benchmark_match" if complete else "benchmark_rejected",
            "passed": passed, "total": len(CASES), "cases": results,
            "tool_executed": False, "sdk_conversation_ran": False,
            "release_authorized": False, "production_authorized": False}


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "request":
        print(json.dumps(request_for(sys.argv[2]), separators=(",", ":")))
    elif len(sys.argv) == 4 and sys.argv[1] == "review":
        folder, receipt = map(Path, sys.argv[2:])
        results = {}
        for case_id in CASES:
            path = folder / (case_id + ".json")
            if path.is_file():
                with path.open("rb") as stream:
                    results[case_id] = _audit_local_case(case_id, stream.read(MAX_RESPONSE_BYTES + 1))
        result = summarize(results)
        receipt.write_text(json.dumps(result, indent=2) + "\n")
        print("Benchmark:", result["status"], result["passed"], "/", result["total"])
        if result["status"] != "benchmark_match":
            raise SystemExit(1)
    else:
        raise SystemExit("request CASE or review DIRECTORY RECEIPT")


if __name__ == "__main__":
    main()
