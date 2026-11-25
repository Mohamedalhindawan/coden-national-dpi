"""Bounded synthetic model benchmark. No tools or SDK are executed."""
import hashlib
import hmac
import json
import re
import threading
import time
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


class PreflightBroker:
    """One-shot authorization policy for a trusted synthetic transport fixture.

    No HTTP client, listener, credential store or SDK is started here. The
    token is a test grant, never an upstream provider credential. This is
    process-local replay protection, not a durable or cross-UID auth boundary.
    The future admitted transport must independently enforce connection and
    read limits, network isolation, interruptible deadlines and cleanup.
    """

    def __init__(self, *, token_sha256, case_id, ttl_seconds=30):
        if (type(token_sha256) is not str or not re.fullmatch(r"[0-9a-f]{64}", token_sha256)
                or type(case_id) is not str or case_id not in CASES
                or type(ttl_seconds) is not int or not 1 <= ttl_seconds <= 60):
            raise ValueError("invalid preflight grant scope")
        self._token_sha256 = token_sha256
        self._case_id = case_id
        self._expires = time.monotonic() + ttl_seconds
        self._lock = threading.Lock()
        self._consumed = False

    @staticmethod
    def _receipt(status, **extra):
        return {"status": status, "qwen_connected": False,
                "fixture_only": True, "tool_executed": False,
                "sdk_conversation_ran": False, "execution_authorized": False,
                "release_authorized": False, "production_authorized": False,
                "automatic_retry_allowed": False, **extra}

    def execute(self, *, token, transport=None, fixture_only=False, cancelled=None):
        if fixture_only is not True:
            return self._receipt("blocked_runtime_admission")
        if not callable(transport):
            return self._receipt("invalid_fixture_transport")
        if (type(token) is not bytes or not 1 <= len(token) <= 128
                or not hmac.compare_digest(hashlib.sha256(token).hexdigest(), self._token_sha256)):
            return self._receipt("authentication_failed")
        with self._lock:
            if self._consumed:
                return self._receipt("grant_consumed")
            if time.monotonic() >= self._expires:
                return self._receipt("grant_expired")
            self._consumed = True

        # Never send the grant token or its digest to the transport.
        # No caller-selected endpoint, payload, model, redirects or fallback.
        from ai_factory.openhands_sdk_operator import review_qwen_route
        route = review_qwen_route(model="openai/local-qwen",
                                  base_url="http://qwen3:11434/v1")["llm_options"]
        try:
            if cancelled is not None and cancelled():
                return self._receipt("cancelled")
            if time.monotonic() >= self._expires:
                return self._receipt("grant_expired")
            started = time.monotonic()
            outcome = transport(url=route["base_url"] + "/chat/completions",
                                request=request_for(self._case_id),
                                timeout_seconds=route["timeout"],
                                max_response_bytes=MAX_RESPONSE_BYTES)
            if cancelled is not None and cancelled():
                return self._receipt("cancelled")
            if time.monotonic() - started >= route["timeout"]:
                return self._receipt("timeout")
            if type(outcome) is not tuple or len(outcome) != 2:
                return self._receipt("invalid_fixture_transport")
            code, raw = outcome
            if type(raw) is not bytes or len(raw) > MAX_RESPONSE_BYTES:
                return self._receipt("fixture_response_rejected", reason_code="oversized_or_invalid_response")
            verdict = audit_http_case(self._case_id, status_code=code, raw=raw)
            if verdict["status"] != "schema_match":
                return self._receipt("fixture_response_rejected", reason_code=verdict["reason_code"])
            return self._receipt("fixture_preflight_match",
                                 response_sha256=verdict["response_sha256"],
                                 completion_tokens=verdict["completion_tokens"])
        except Exception:
            # Never include provider/transport exception text or raw response.
            return self._receipt("fixture_transport_failed")


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
