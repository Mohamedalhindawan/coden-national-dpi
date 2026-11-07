"""Fail-closed registry for local, dry-run-only tool adapters."""
from datetime import datetime, timezone
import hashlib
import json

class AdapterError(ValueError):
    """Raised when an adapter dispatch violates the execution boundary."""

class AdapterRegistry:
    def __init__(self):
        self._adapters = {}

    def register(self, tool_name, adapter):
        if not isinstance(tool_name, str) or not tool_name.strip():
            raise AdapterError("Tool name is required")
        if tool_name in self._adapters:
            raise AdapterError(f"Adapter already registered: {tool_name}")
        if not callable(getattr(adapter, "execute", None)):
            raise AdapterError("Adapter must implement execute(context)")
        self._adapters[tool_name] = adapter

    def dispatch(self, tool_name, task_id, run_id, payload, network, mode):
        if mode != "dry_run":
            raise AdapterError("Only dry_run mode is enabled; live execution is disabled")
        if network != "disabled":
            raise AdapterError("Network access must be disabled")
        if tool_name not in self._adapters:
            raise AdapterError(f"No adapter registered for tool: {tool_name}")
        if not task_id or not run_id or not isinstance(payload, dict):
            raise AdapterError("task_id, run_id and object payload are required")
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        context = {
            "task_id": task_id,
            "run_id": run_id,
            "tool_name": tool_name,
            "payload": payload,
            "network": "disabled",
            "mode": "dry_run",
            "payload_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        }
        try:
            receipt = self._adapters[tool_name].execute(context)
        except Exception as exc:
            raise AdapterError(f"Adapter failed safely: {type(exc).__name__}") from exc
        if not isinstance(receipt, dict):
            raise AdapterError("Adapter receipt must be an object")
        if receipt.get("executed") is not False or receipt.get("status") != "simulated":
            raise AdapterError("Adapter receipt must explicitly report simulated and executed=false")
        return {
            "receipt_version": "1.0.0",
            "receipt_id": hashlib.sha256(
                f"{run_id}:{task_id}:{tool_name}:{context['payload_sha256']}".encode()
            ).hexdigest()[:24],
            "run_id": run_id,
            "task_id": task_id,
            "tool_name": tool_name,
            "status": "simulated",
            "executed": False,
            "network": "disabled",
            "mode": "dry_run",
            "payload_sha256": context["payload_sha256"],
            "adapter_output": receipt.get("output", {}),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
