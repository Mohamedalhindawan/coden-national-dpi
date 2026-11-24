"""Fail-closed review-only real rootless OpenHands session API auth evidence.

The YAML fixture must actually run unauthenticated, incorrect-key, and
correct-key HTTP requests against the source-built server. This verifier
cannot run the SDK agent and does not approve tool calls or production.
"""
import argparse
import json
from pathlib import Path
import os
import stat
import sys

OPENHANDS_BINARY_SHA = "5ad5fa2bb86256b510df3bfbbd9653fbc60a243ea744a579d3ca4c6fd9e91cf3"
QWEN_SHA = "1d9614638d18024d0fbb36575a15f1302a3adf044df10345688ec4f6e1c4ff32"
TRUE = (
    "rootless_podman",
    "model_private_network_tested",
    "no_public_ports",
    "no_external_http_egress",
    "no_key_request_rejected",
    "incorrect_key_request_rejected",
    "valid_ephemeral_key_request_accepted",
    "openhands_health_200",
    "session_key_not_logged_or_exported",
    "session_key_unique_per_run",
    "startup_encryption_key_present",
)
FALSE = (
    "actual_sdk_conversation_run", "agent_tool_calls_authorized",
    "release_authorized", "production_authorized", "automatic_merge",
)
FIELDS = frozenset(TRUE + FALSE + (
    "plan_version", "signed_binary_sha256", "qwen_weights_sha256",
    "paid_calls",
))


def verify(data):
    if type(data) is not dict or set(data) != FIELDS:
        raise ValueError("incomplete or extra authenticated runtime proof")
    if (data["plan_version"] != "v1.0" or
        data["signed_binary_sha256"] != OPENHANDS_BINARY_SHA or
        data["qwen_weights_sha256"] != QWEN_SHA or
        any(data[k] is not True for k in TRUE) or
        any(data[k] is not False for k in FALSE) or
        type(data["paid_calls"]) is not int or data["paid_calls"] != 0):
        raise ValueError("OpenHands auth proof not admitted")
    return {**data, "stage": "REAL_AUTHENTICATED_ROOTLESS_SERVER_ONLY"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args(argv)
    try:
        source = args.input
        if source.is_symlink() or not hasattr(os, "O_NOFOLLOW"):
            raise ValueError("unsafe input")
        fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode) or not 0 < st.st_size < 8192:
                raise ValueError("oversize or invalid input")
            with os.fdopen(os.dup(fd), "rb") as stream:
                raw = stream.read(8192)
        finally:
            os.close(fd)
        report = verify(json.loads(raw.decode("utf-8")))
        out = args.output
        if not out.is_absolute() or out.is_symlink() or out.exists() or not out.parent.is_dir():
            raise ValueError("unsafe output")
        with out.open("x", encoding="utf-8") as f:
            json.dump(report, f, sort_keys=True, indent=2)
            f.write("\n")
    except (OSError, ValueError, TypeError, json.JSONDecodeError, UnicodeError):
        ap.exit(2, "OpenHands real rootless authentication BLOCKED\n")
    print(json.dumps({"stage": report["stage"], "release_authorized": False}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
