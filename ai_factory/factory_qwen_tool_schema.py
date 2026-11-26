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


def _reject_constant(_value):
    # Python's JSON decoder otherwise accepts NaN and infinities (not JSON).
    raise json.JSONDecodeError("nonstandard JSON constant", "", 0)


def audit_response(body, *, expected_tool='count_flags', expected_args=None):
    if expected_args is None:
        expected_args = {'flags': ['pending', 'approved']}
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
        if fn["name"] != expected_tool:
            raise ValueError("unexpected tool choice")
        raw = fn["arguments"]
        if not isinstance(raw, str) or len(raw) > 4096:
            raise ValueError("invalid argument representation")
        args = json.loads(raw, object_pairs_hook=_unique_pairs, parse_constant=_reject_constant)
        if json.dumps(args, sort_keys=True) != json.dumps(expected_args, sort_keys=True):
            raise ValueError("unexpected arguments")
    except (KeyError, TypeError, IndexError, AttributeError, OverflowError) as exc:
        raise ValueError("invalid response schema") from exc
    return {"status": "schema_match", "completion_tokens": count,
            "tool_executed": False, "sdk_conversation_ran": False,
            "release_authorized": False, "production_authorized": False}


# Only these fixed, first-party labels can leave the validator on failure.
# JSON parser exception text, generated arguments and model text never do.
_REJECTION_CODES = {
    "duplicate JSON key": "duplicate_key",
    "one response required": "choice_count",
    "invalid completion token count": "completion_count",
    "not a structured tool call": "finish_reason_or_role",
    "unexpected extra content": "extra_content",
    "exactly one call required": "call_count",
    "invalid tool call envelope": "call_envelope",
    "unexpected tool choice": "tool_choice",
    "invalid argument representation": "argument_representation",
    "unexpected arguments": "argument_mismatch",
    "invalid response schema": "response_shape",
}


def evaluate_response(raw, **expectations):
    result = {"status": "schema_rejected", "tool_executed": False,
              "sdk_conversation_ran": False, "release_authorized": False,
              "production_authorized": False}
    if len(raw) > MAX_RESPONSE_BYTES:
        return {**result, "reason_code": "oversized_response"}
    try:
        body = json.loads(raw, object_pairs_hook=_unique_pairs, parse_constant=_reject_constant)
    except (json.JSONDecodeError, UnicodeError, RecursionError):
        return {**result, "reason_code": "invalid_json"}
    except ValueError as exc:
        return {**result, "reason_code": _REJECTION_CODES.get(str(exc), "invalid_json")}
    try:
        return {**audit_response(body, **expectations),
                "response_sha256": hashlib.sha256(raw).hexdigest()}
    except json.JSONDecodeError:
        return {**result, "reason_code": "invalid_arguments_json"}
    except (RecursionError, UnicodeError):
        return {**result, "reason_code": "invalid_arguments_json"}
    except ValueError as exc:
        return {**result, "reason_code": _REJECTION_CODES.get(str(exc), "response_rejected")}


def main():
    if len(sys.argv) != 3:
        raise SystemExit("provide response and receipt paths")
    source, receipt = map(Path, sys.argv[1:])
    with source.open("rb") as stream:
        raw = stream.read(MAX_RESPONSE_BYTES + 1)
    result = evaluate_response(raw)
    receipt.write_text(json.dumps(result, indent=2) + "\n")
    print("Tool schema preflight:", result["status"], result.get("reason_code", "accepted"))
    if result["status"] != "schema_match":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
