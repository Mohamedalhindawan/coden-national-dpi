"""Strict review-only admission of a *real* rootless OpenHands↔Qwen link receipt.

A successful link proves model reachability from the original agent-server
container; it does NOT imply OpenHands tool-calling or SDK Conversation.
Records must be produced by real runner-side tests, not manual approvals.
"""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys

from .factory_real_qwen_server_admission import LLAMA_SHA, MODEL_SHA

UPSTREAM = "077f3fad6d31cd852be5c87176e0a93c3b446126"
BINARY_SHA = "5ad5fa2bb86256b510df3bfbbd9653fbc60a243ea744a579d3ca4c6fd9e91cf3"
HASH64 = re.compile(r"[0-9a-f]{64}\Z")
POSITIVE = (
    "rootless_podman",
    "cgroup_v2_cpu_memory_pids",
    "private_internal_bridge",
    "exactly_two_containers",
    "both_containers_nonroot_capless_readonly",
    "no_host_port_bindings_or_secrets",
    "openhands_server_health_http_200",
    "model_health_from_openhands_container",
    "real_qwen_completion_from_openhands_container",
    "outside_ip_http_denied_from_openhands",
    "outside_dns_http_denied_from_openhands",
    "temporary_storage_bytes_and_inodes_capped",
    "child_processes_cgroup_attested",
    "signed_binary_provenance_verified",
    "independent_high_critical_scan_gate_passed",
    "no_openhands_sdk_conversation",
    "no_agent_tool_calls",
    "no_three_file_candidate_generated",
)
NEGATIVE = (
    "openhands_live_execution_authorized",
    "factory_production_authorized",
    "automatic_merge",
    "release_authorized",
)
FIELDS = frozenset(POSITIVE + NEGATIVE + (
    "plan_version", "upstream_source_commit", "binary_sha256",
    "model_sha256", "llama_cpp_archive_sha256",
    "real_qwen_tokens_predicted", "real_qwen_response_sha256", "paid_calls",
))


def validate_receipt(data):
    if not isinstance(data, dict) or set(data) != FIELDS:
        raise ValueError("wrong rootless model-link evidence schema")
    if (
        data["plan_version"] != "v1.0" or
        data["upstream_source_commit"] != UPSTREAM or
        data["binary_sha256"] != BINARY_SHA or
        data["model_sha256"] != MODEL_SHA or
        data["llama_cpp_archive_sha256"] != LLAMA_SHA or
        not isinstance(data["real_qwen_response_sha256"], str) or
        HASH64.fullmatch(data["real_qwen_response_sha256"]) is None or
        type(data["real_qwen_tokens_predicted"]) is not int or
        not 1 <= data["real_qwen_tokens_predicted"] <= 32 or
        type(data["paid_calls"]) is not int or data["paid_calls"] != 0 or
        any(data.get(field) is not True for field in POSITIVE) or
        any(data.get(field) is not False for field in NEGATIVE)
    ):
        raise ValueError("OpenHands model-link isolation/readiness gate BLOCKED")
    return {**data, "stage": "REAL_ROOTLESS_MODEL_CONNECTIVITY_ONLY"}


def _load(path):
    path = Path(path)
    if path.is_symlink() or not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("untrusted evidence file")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size < 16_384:
            raise ValueError("evidence is absent or oversized")
        with os.fdopen(os.dup(fd), "rb") as stream:
            data = stream.read(16_384)
        if len(data) != info.st_size:
            raise ValueError("racing evidence file")
    finally:
        os.close(fd)
    return json.loads(data.decode("utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args(argv)
    try:
        report = validate_receipt(_load(args.input))
        output = args.output
        if (not output.is_absolute() or output.exists() or output.is_symlink()
                or not output.parent.is_dir() or output.parent.is_symlink()):
            raise ValueError("receipt must be a fresh absolute path")
        with output.open("x", encoding="utf-8") as f:
            json.dump(report, f, indent=2, sort_keys=True)
            f.write("\n")
    except (ValueError, OSError, TypeError, KeyError, UnicodeError, json.JSONDecodeError):
        ap.exit(2, "Rootless OpenHands real-Qwen link BLOCKED\n")
    print(json.dumps({
        "stage": report["stage"],
        "real_model_tokens": report["real_qwen_tokens_predicted"],
        "release_authorized": False,
        "openhands_live_execution_authorized": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
