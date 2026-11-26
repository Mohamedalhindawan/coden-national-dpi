"""Bounded synthetic model benchmark. No tools or SDK are executed."""
import hashlib
import hmac
import http.client
import io
import json
import re
import select
import socket
import struct
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


class _FixtureCancelled(Exception):
    pass


def _stream_io(channel, end, cancel_event):
    """Nonblocking transfers share one deadline for all writes and reads."""
    channel.setblocking(False)

    def check():
        if cancel_event is not None and cancel_event.is_set():
            raise _FixtureCancelled()
        remaining = end - time.monotonic()
        if remaining <= 0:
            raise TimeoutError()
        return remaining

    def ready(write):
        while True:
            interval = min(check(), .05)
            rd, wr, _ = select.select([] if write else [channel],
                                      [channel] if write else [], [], interval)
            check()
            if wr or rd:
                return

    def send_all(data):
        view = memoryview(data)
        while view:
            ready(True)
            try:
                n = channel.send(view)
            except BlockingIOError:
                continue
            if not n:
                raise ValueError("fixture stream closed")
            view = view[n:]

    def read_some(size):
        while True:
            ready(False)
            try:
                return channel.recv(size)
            except BlockingIOError:
                continue

    return send_all, read_some


class PreflightBroker:
    """One-shot authorization policy for a trusted synthetic transport fixture.

    The launcher supplies connected fixture streams. No DNS, outbound dial,
    listener, credential store or SDK is started here. The
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
            completed = time.monotonic()
            if completed - started >= route["timeout"]:
                return self._receipt("timeout")
            # A consumed grant never accepts a response arriving after expiry.
            if completed >= self._expires:
                return self._receipt("grant_expired")
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
        except _FixtureCancelled:
            return self._receipt("cancelled")
        except TimeoutError:
            return self._receipt("timeout")
        except Exception:
            # Never include provider/transport exception text or raw response.
            return self._receipt("fixture_transport_failed")


    def execute_ipc(self, *, token, channel, expected_peer, fixture_only=False,
                    deadline_seconds=35, cancel_event=None):
        """Own one preconnected trusted AF_UNIX fixture stream until close.

        Wire protocol: request uint32 length + generated JSON, response
        uint16 captured HTTP status + uint32 length + bytes, then EOF.
        No endpoint lookup, connect(), HTTP, listener, provider or SDK here.
        Peer tuple must come from a trusted launcher, not the remote data;
        SO_PEERCRED describes connection-time identity, not proof of a
        separate live service (socketpair can share a creator).
        """
        if type(channel) is not socket.socket:
            return self._receipt("invalid_fixture_transport")
        with channel:
            if fixture_only is not True:
                return self._receipt("blocked_runtime_admission")
            if (type(expected_peer) is not tuple or len(expected_peer) != 3
                    or any(type(n) is not int or n < 0 for n in expected_peer)
                    or expected_peer[0] == 0
                    or channel.family != socket.AF_UNIX
                    or channel.type != socket.SOCK_STREAM
                    or not hasattr(socket, "SO_PEERCRED")):
                return self._receipt("fixture_peer_rejected")
            try:
                channel.getpeername()
                peer = struct.unpack("3i", channel.getsockopt(socket.SOL_SOCKET,
                                                            socket.SO_PEERCRED, 12))
                if peer != expected_peer:
                    return self._receipt("fixture_peer_rejected")
            except (OSError, struct.error):
                return self._receipt("fixture_peer_rejected")
            if (type(deadline_seconds) not in (float, int)
                    or not 0 < deadline_seconds <= 35
                    or (cancel_event is not None and type(cancel_event) is not threading.Event)):
                return self._receipt("invalid_fixture_transport")
            send_all, read_some = _stream_io(channel, min(time.monotonic() + deadline_seconds,
                                                          self._expires), cancel_event)

            def receive(size):
                data = bytearray()
                while len(data) < size:
                    block = read_some(min(4096, size - len(data)))
                    if not block:
                        raise ValueError("truncated fixture frame")
                    data.extend(block)
                return bytes(data)

            def exchange(*, url, request, timeout_seconds, max_response_bytes):
                if (url != "http://qwen3:11434/v1/chat/completions"
                        or request != request_for(self._case_id)
                        or timeout_seconds != 35 or max_response_bytes != MAX_RESPONSE_BYTES):
                    raise ValueError("fixture request outside scope")
                raw = json.dumps(request, separators=(",", ":"), allow_nan=False).encode("utf-8")
                if not 0 < len(raw) <= 16 * 1024:
                    raise ValueError("fixture request too large")
                send_all(struct.pack("!I", len(raw)) + raw)
                channel.shutdown(socket.SHUT_WR)
                code, length = struct.unpack("!HI", receive(6))
                if length > MAX_RESPONSE_BYTES:
                    raise ValueError("fixture response too large")
                response = receive(length)
                # One frame only, no unsolicited bytes or second response.
                if read_some(1):
                    raise ValueError("trailing fixture data")
                return code, response

            return self.execute(token=token, transport=exchange, fixture_only=True,
                                cancelled=None if cancel_event is None else cancel_event.is_set)

    def execute_http_fixture(self, *, token, channel, expected_port, fixture_only=False,
                             deadline_seconds=35, cancel_event=None):
        """Own a TCP stream preconnected by the trusted launcher to its loopback fixture.

        The launcher owns the synthetic server and its port. Loopback is a route
        restriction, not server authentication. No dial, DNS, redirects, proxy,
        provider credentials, SDK or model fallback.
        """
        if type(channel) is not socket.socket:
            return self._receipt("invalid_fixture_transport")
        with channel:
            if fixture_only is not True:
                return self._receipt("blocked_runtime_admission")
            if (type(deadline_seconds) not in (float, int) or not 0 < deadline_seconds <= 35
                    or (cancel_event is not None and type(cancel_event) is not threading.Event)):
                return self._receipt("invalid_fixture_transport")
            try:
                if (type(expected_port) is not int or not 1024 <= expected_port <= 65535
                        or channel.family != socket.AF_INET or channel.type != socket.SOCK_STREAM
                        or channel.getsockname()[0] != "127.0.0.1"
                        or channel.getpeername() != ("127.0.0.1", expected_port)):
                    return self._receipt("fixture_peer_rejected")
            except OSError:
                return self._receipt("fixture_peer_rejected")

            def exchange(*, url, request, timeout_seconds, max_response_bytes):
                if url != "http://qwen3:11434/v1/chat/completions":
                    raise ValueError("unexpected route")
                end = min(time.monotonic() + min(deadline_seconds, timeout_seconds), self._expires)
                send_all, read_some = _stream_io(channel, end, cancel_event)
                body = json.dumps(request, separators=(",", ":"), allow_nan=False).encode()
                if len(body) > 16 * 1024:
                    raise ValueError("request too large")
                head = (f"POST /v1/chat/completions HTTP/1.1\r\nHost: 127.0.0.1:{expected_port}\r\n"
                        f"Content-Type: application/json\r\nConnection: close\r\nContent-Length: {len(body)}\r\n\r\n")
                send_all(head.encode("ascii") + body)
                return _read_fixture_http(read_some, max_response_bytes)

            return self.execute(token=token, fixture_only=True, transport=exchange,
                                cancelled=None if cancel_event is None else cancel_event.is_set)


def _read_fixture_http(read_some, max_body):
    # Deliberately narrow profile: one fixed-length, identity-encoded reply,
    # closed after its body. Bound headers before handing them to the parser.
    header_limit = 8192
    buf = bytearray()
    while b"\r\n\r\n" not in buf:
        if len(buf) >= header_limit:
            raise ValueError("response headers too large")
        block = read_some(min(4096, header_limit - len(buf)))
        if not block:
            raise ValueError("incomplete response headers")
        buf.extend(block)
    head, body = buf.split(b"\r\n\r\n", 1)
    lines = head.split(b"\r\n")
    status = re.fullmatch(rb"HTTP/1\.[01] ([2-5][0-9]{2})(?: [ -~]*)?", lines[0])
    if not status or any(not re.fullmatch(rb"[!#$%&'*+.^_`|~0-9a-zA-Z-]+:[\t -~]*", line)
                         for line in lines[1:]):
        raise ValueError("unsupported HTTP response")
    fields = http.client.parse_headers(io.BytesIO(b"\r\n".join(lines[1:]) + b"\r\n\r\n"))
    lengths = fields.get_all("Content-Length", [])
    if (len(lengths) != 1 or not re.fullmatch(r"[0-9]{1,8}", lengths[0])
            or "Transfer-Encoding" in fields or "Content-Encoding" in fields):
        raise ValueError("unsupported response framing")
    size = int(lengths[0])
    if len(body) > size or size > max_body:
        raise ValueError("invalid response size")
    while len(body) < size:
        block = read_some(min(4096, size - len(body)))
        if not block:
            raise ValueError("truncated response")
        body.extend(block)
    if read_some(1):
        raise ValueError("trailing response data")
    return int(status[1]), bytes(body)


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
