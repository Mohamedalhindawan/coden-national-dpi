"""Opt-in, bounded Ollama model *discovery*; no inference or auto-adoption.

CODEN reuses Ollama's upstream GET /api/tags rather than building a model
server. By default this module makes no request. Its optional probe only
connects directly to numeric IPv4 loopback, never via a proxy, redirect,
credential, DNS alias, hosted provider or consumer subscription session.

Probe success is not approval to generate code, authorize a task or spend.
"""
import argparse
import http.client
import json
import re
import sys
from urllib.parse import urlsplit

MAX_RESPONSE_BYTES = 65536
MAX_MODELS = 256
MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")


def _port(endpoint):
    if not isinstance(endpoint, str):
        raise ValueError("Ollama endpoint must be numeric local loopback")
    try:
        u = urlsplit(endpoint)
        port = u.port
    except ValueError as exc:
        raise ValueError("malformed Ollama endpoint") from exc
    if (u.scheme != "http" or u.hostname != "127.0.0.1"
            or u.username is not None or u.password is not None
            or u.query or u.fragment or u.path not in ("", "/")
            or port is None or not 1 <= port <= 65535):
        raise ValueError("Ollama probe requires http://127.0.0.1:PORT")
    return port


def _unique_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate discovery response field")
        obj[key] = value
    return obj


def _status(probe_status, attempted=False, available=False):
    return {
        "provider": "ollama",
        "probe_status": probe_status,
        "probe_attempted": attempted,
        "model_available": available,
        "provider_approved": False,
        "execution_authorized": False,
    }


def probe(endpoint, model, *, allow_loopback=False):
    """Read-only model discovery, opt-in and restricted to local Ollama.

    No model prompts, model pulls, credential handling, cost/approval changes,
    auto-fallback or network requests unless allow_loopback is explicitly True.
    """
    port = _port(endpoint)
    if not isinstance(model, str) or not MODEL.fullmatch(model):
        raise ValueError("invalid Ollama model identifier")
    if type(allow_loopback) is not bool:
        raise ValueError("explicit boolean opt-in required")
    if not allow_loopback:
        return _status("disabled")

    connection = None
    try:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        connection.request("GET", "/api/tags", headers={"Accept": "application/json"})
        response = connection.getresponse()
        if response.status != 200:
            return _status("http_error", attempted=True)
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            return _status("oversized_response", attempted=True)
        try:
            data = json.loads(raw, object_pairs_hook=_unique_keys)
            if not isinstance(data, dict) or not isinstance(data.get("models"), list):
                raise ValueError("invalid model listing")
            models = data["models"]
            if len(models) > MAX_MODELS or not all(
                isinstance(item, dict)
                and isinstance(item.get("name"), str)
                and MODEL.fullmatch(item["name"])
                for item in models
            ):
                raise ValueError("invalid model entry")
        except (UnicodeError, ValueError, TypeError):
            return _status("invalid_response", attempted=True)
        available = any(item["name"] == model for item in models)
        return _status("available" if available else "model_absent",
                       attempted=True, available=available)
    except (OSError, TimeoutError, http.client.HTTPException):
        return _status("unreachable", attempted=True)
    finally:
        if connection is not None:
            connection.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--model", required=True)
    parser.add_argument("--probe-loopback", action="store_true",
                        help="Explicit permission for one GET /api/tags to 127.0.0.1")
    args = parser.parse_args(argv)
    try:
        result = probe(args.endpoint, args.model, allow_loopback=args.probe_loopback)
    except (ValueError, TypeError):
        result = _status("invalid_config")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["probe_status"] in ("disabled", "available") else 1


if __name__ == "__main__":
    sys.exit(main())
