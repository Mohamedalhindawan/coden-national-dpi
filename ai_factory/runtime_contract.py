"""Provider-neutral runtime *evidence metadata* contract.

This module does not call providers, route traffic, execute tools or authorize
tasks. It validates short, credential-free, synthetic-only task references and
returned evidence descriptions to prepare future official SDK integrations.
Even validated artifact SHA-256 values are NOT file-content verification.
"""

from decimal import Decimal, InvalidOperation
import re

from . import recovery_policy

REQ_SCHEMA = "coden.runtime.request.v1"
REPORT_SCHEMA = "coden.runtime.report.v1"
TASK_ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z")
REQ_KEYS = frozenset({
    "schema", "task_id", "task_sha256", "classification",
    "required_capabilities", "allowed_providers", "allow_external_api",
    "max_tokens_total", "max_duration_seconds", "max_cost_usd",
})
REPORT_KEYS = frozenset({
    "schema", "task_id", "provider_id", "model_id", "transport",
    "status", "error_code", "artifact_sha256", "input_tokens",
    "output_tokens", "duration_ms", "cost_usd",
})
STATUSES = frozenset({"completed", "failed", "blocked", "paused"})


def _label(value, *, task=False):
    pattern = TASK_ID if task else LABEL
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ValueError("invalid contract identifier")
    return value


def _tags(value):
    if not isinstance(value, list) or not 1 <= len(value) <= 16:
        raise ValueError("invalid tag list")
    tags = [_label(item) for item in value]
    if len(tags) != len(set(tags)):
        raise ValueError("duplicate tag")
    return frozenset(tags)


def _positive_int(value, bound):
    if type(value) is not int or not 1 <= value <= bound:
        raise ValueError("invalid positive integer budget")
    return value


def _nonnegative_int(value):
    if type(value) is not int or not 0 <= value <= 10**9:
        raise ValueError("invalid nonnegative usage")
    return value


def _money(value):
    if type(value) not in (int, str, Decimal):
        raise ValueError("invalid financial limit")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("invalid financial limit") from exc
    if not number.is_finite() or number < 0:
        raise ValueError("invalid financial limit")
    return number


def _digest(value, *, required):
    if value is None and not required:
        return None
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise ValueError("invalid artifact SHA-256")
    return value


def assess(request, report):
    """Validate provider result metadata; never verify or execute actual artifacts."""
    if not isinstance(request, dict) or set(request) != REQ_KEYS:
        raise ValueError("invalid request fields")
    if not isinstance(report, dict) or set(report) != REPORT_KEYS:
        raise ValueError("invalid report fields")
    if request["schema"] != REQ_SCHEMA or report["schema"] != REPORT_SCHEMA:
        raise ValueError("unsupported contract schema")
    task_id = _label(request["task_id"], task=True)
    _digest(request["task_sha256"], required=True)
    if request["classification"] != "synthetic":
        raise ValueError("only synthetic tasks supported")
    _tags(request["required_capabilities"])
    allowed = _tags(request["allowed_providers"])
    if type(request["allow_external_api"]) is not bool:
        raise ValueError("invalid external transport flag")
    token_budget = _positive_int(request["max_tokens_total"], 1000000)
    seconds_budget = _positive_int(request["max_duration_seconds"], 3600)
    cost_budget = _money(request["max_cost_usd"])

    if _label(report["task_id"], task=True) != task_id:
        raise ValueError("report task identity mismatch")
    provider_id = _label(report["provider_id"])
    model_id = _label(report["model_id"])
    if provider_id not in allowed:
        raise ValueError("provider is not on task allowlist")
    transport = report["transport"]
    if transport not in ("local", "official_api_key"):
        raise ValueError("unsupported authentication transport")
    if transport != "local" and not request["allow_external_api"]:
        raise ValueError("external transport is not enabled")
    status = report["status"]
    if not isinstance(status, str) or status not in STATUSES:
        raise ValueError("unsupported status")
    error = report["error_code"]
    if status == "completed":
        if error is not None:
            raise ValueError("completed report cannot include an error")
        _digest(report["artifact_sha256"], required=True)
    else:
        if not isinstance(error, str) or error not in recovery_policy.FAILURES:
            raise ValueError("error result must contain a sanitized error code")
        if report["artifact_sha256"] is not None:
            raise ValueError("failed report cannot claim successful artifact")
    in_tokens = _nonnegative_int(report["input_tokens"])
    out_tokens = _nonnegative_int(report["output_tokens"])
    duration = _nonnegative_int(report["duration_ms"])
    cost = _money(report["cost_usd"])
    if in_tokens + out_tokens > token_budget:
        raise ValueError("token budget exceeded")
    if duration > seconds_budget * 1000:
        raise ValueError("duration budget exceeded")
    if cost > cost_budget:
        raise ValueError("cost budget exceeded")
    return {
        "schema": "coden.runtime.assessment.v1",
        "task_id": task_id,
        "provider_id": provider_id,
        "model_id": model_id,
        "status": status,
        "error_code": error,
        "input_tokens": in_tokens,
        "output_tokens": out_tokens,
        "duration_ms": duration,
        "cost_usd": str(cost),
        "artifact_hash_recorded": status == "completed",
        "artifact_verified": False,
        "contract_valid": True,
        "provider_approved": False,
        "execution_authorized": False,
    }
