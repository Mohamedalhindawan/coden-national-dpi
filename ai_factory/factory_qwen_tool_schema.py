"""Strict review-only audit of one genuine synthetic tool-call response.

This module never dispatches tools, imports the SDK or authorizes execution.
"""
import hashlib
import json
from pathlib import Path
import re
import sys

MAX_RESPONSE_BYTES = 256 * 1024


def _unique_pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate JSON key")
        obj[key] = value
    return obj


def audit_response(body):
    try:
        choices = body["choices"]
        count = body["usage"]["completion_tokens"]
        if not isinstance(choices, list) or len(choices) != 1:
            raise ValueError("one response required")
        if type(count) is not int or not 1 <= count <= 128:
            raise ValueError("invalid completion token count")
        choice = choices[0]
        message = choice["message"]
        if choice["finish_reason"] != "tool_calls" or message["role"] != "assistant":
            raise ValueError("not a structured tool call")
        if message.get("content") not in (None, ""):
            raise ValueError("unexpected extra content")
        calls = message["tool_calls"]
        if not isinstance(calls, list) or len(calls) != 1:
            raise ValueError("exactly one call required")
        call = calls[0]
        if (call["type"] != "function" or not isinstance(call["id"], str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", call["id"])):
            raise ValueError("invalid tool call envelope")
        fn = call["function"]
        if fn["name"] != "count_flags":
            raise ValueError("unexpected tool choice")
        raw = fn["arguments"]
        if not isinstance(raw, str) or len(raw) > 4096:
            raise ValueError("invalid argument representation")
        args = json.loads(raw, object_pairs_hook=_unique_pairs)
        if args != {"flags": ["pending", "approved"]}:
            raise ValueError("unexpected arguments")
    except (KeyError, TypeError, IndexError, AttributeError, OverflowError) as exc:
        raise ValueError("invalid response schema") from exc
    return {"status": "schema_match", "completion_tokens": count,
            "tool_executed": False, "sdk_conversation_ran": False,
            "release_authorized": False, "production_authorized": False}


def main():
    if len(sys.argv) != 3:
        raise SystemExit("provide response and receipt paths")
    source, receipt = map(Path, sys.argv[1:])
    with source.open("rb") as stream:
        raw = stream.read(MAX_RESPONSE_BYTES + 1)
    result = {"status": "schema_rejected", "tool_executed": False,
              "sdk_conversation_ran": False, "release_authorized": False,
              "production_authorized": False}
    try:
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("oversized response")
        result = audit_response(json.loads(raw, object_pairs_hook=_unique_pairs))
        result["response_sha256"] = hashlib.sha256(raw).hexdigest()
    except (ValueError, RecursionError, UnicodeError):
        pass
    receipt.write_text(json.dumps(result, indent=2) + "\n")
    print("Tool schema preflight:", result["status"])
    if result["status"] != "schema_match":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
