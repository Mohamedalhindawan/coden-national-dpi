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
    ("set_limit", "Set the maximum number of synthetic records", "limit", {"type": "integer"}),
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
                    results[case_id] = audit_case(case_id, stream.read(MAX_RESPONSE_BYTES + 1))
        result = summarize(results)
        receipt.write_text(json.dumps(result, indent=2) + "\n")
        print("Benchmark:", result["status"], result["passed"], "/", result["total"])
        if result["status"] != "benchmark_match":
            raise SystemExit(1)
    else:
        raise SystemExit("request CASE or review DIRECTORY RECEIPT")


if __name__ == "__main__":
    main()
