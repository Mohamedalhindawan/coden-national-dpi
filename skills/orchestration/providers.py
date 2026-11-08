"""Fail-closed provider contracts. No credentials, network, or live model calls."""
from dataclasses import dataclass
import hashlib
import json
import re
from datetime import datetime, timezone


class ProviderError(ValueError):
    pass


ALLOWED_CAPABILITIES = {
    "reasoning", "architecture", "coding", "testing", "documentation",
    "security_review", "data_engineering", "dpi_architecture",
}
ALLOWED_CLASSIFICATIONS = {"synthetic", "public"}
_SECRET_REF = re.compile(r"^secret://[A-Za-z0-9._/-]+$")


@dataclass(frozen=True)
class ProviderProfile:
    provider_id: str
    display_name: str
    capabilities: tuple
    secret_ref: str
    enabled: bool = True
    mode: str = "simulated"

    def __post_init__(self):
        if not re.fullmatch(r"[a-z][a-z0-9-]{1,31}", self.provider_id or ""):
            raise ProviderError("invalid provider_id")
        if not isinstance(self.display_name, str) or not self.display_name.strip():
            raise ProviderError("display_name is required")
        if not isinstance(self.capabilities, tuple) or not self.capabilities:
            raise ProviderError("capabilities must be a non-empty tuple")
        if any(item not in ALLOWED_CAPABILITIES for item in self.capabilities):
            raise ProviderError("unsupported provider capability")
        if not isinstance(self.secret_ref, str) or not _SECRET_REF.fullmatch(self.secret_ref):
            raise ProviderError("secret_ref must be a secret:// reference, never a credential value")
        if type(self.enabled) is not bool or self.mode != "simulated":
            raise ProviderError("only enabled/disabled simulated profiles are supported")


@dataclass(frozen=True)
class ProviderRequest:
    request_id: str
    provider_id: str
    capability: str
    task_id: str
    data_classification: str
    payload: dict


@dataclass(frozen=True)
class ProviderPolicy:
    mode: str = "simulated"
    network: str = "disabled"
    human_approval: bool = True


class SimulatedProviderAdapter:
    """Returns deterministic metadata; it does not contact a provider."""
    def invoke(self, request, payload_sha256):
        return {
            "status": "simulated",
            "provider_invoked": False,
            "network_used": False,
            "output": {
                "message": "Provider invocation was not performed.",
                "payload_sha256": payload_sha256,
            },
        }


class ProviderCatalog:
    def __init__(self):
        self._profiles = {}
        self._adapters = {}
        self._request_ids = set()

    def register(self, profile):
        if not isinstance(profile, ProviderProfile):
            raise ProviderError("profile must be a ProviderProfile")
        if profile.provider_id in self._profiles:
            raise ProviderError("provider already registered")
        self._profiles[profile.provider_id] = profile

    def register_adapter(self, provider_id, adapter):
        if provider_id not in self._profiles:
            raise ProviderError("provider profile must be registered first")
        if provider_id in self._adapters:
            raise ProviderError("provider adapter already registered")
        if not callable(getattr(adapter, "invoke", None)):
            raise ProviderError("adapter must implement invoke(request, payload_sha256)")
        self._adapters[provider_id] = adapter

    def list_profiles(self):
        return [self.get(provider_id) for provider_id in sorted(self._profiles)]

    def get(self, provider_id):
        profile = self._profiles.get(provider_id)
        if profile is None:
            raise ProviderError("unknown provider")
        return {
            "provider_id": profile.provider_id,
            "display_name": profile.display_name,
            "capabilities": list(profile.capabilities),
            "secret_ref": profile.secret_ref,
            "enabled": profile.enabled,
            "mode": profile.mode,
        }

    def dispatch(self, request, policy):
        if not isinstance(request, ProviderRequest) or not isinstance(policy, ProviderPolicy):
            raise ProviderError("request and policy types are required")
        if not request.request_id or not request.task_id:
            raise ProviderError("request_id and task_id are required")
        if request.request_id in self._request_ids:
            raise ProviderError("duplicate request_id")
        if policy.mode != "simulated" or policy.network != "disabled":
            raise ProviderError("live mode and network access are disabled")
        if policy.human_approval is not True:
            raise ProviderError("human approval is mandatory")
        if request.data_classification not in ALLOWED_CLASSIFICATIONS:
            raise ProviderError("only synthetic or public data is allowed")
        if not isinstance(request.payload, dict):
            raise ProviderError("payload must be an object")
        profile = self._profiles.get(request.provider_id)
        if profile is None or not profile.enabled:
            raise ProviderError("provider is unknown or disabled")
        if request.capability not in ALLOWED_CAPABILITIES or request.capability not in profile.capabilities:
            raise ProviderError("provider capability is not permitted")
        adapter = self._adapters.get(request.provider_id)
        if adapter is None:
            raise ProviderError("no simulated adapter registered")
        canonical = json.dumps(request.payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        payload_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        self._request_ids.add(request.request_id)
        try:
            result = adapter.invoke(request, payload_hash)
        except Exception as exc:
            raise ProviderError("provider adapter failed safely: " + type(exc).__name__) from exc
        if not isinstance(result, dict) or result.get("provider_invoked") is not False or result.get("network_used") is not False or result.get("status") != "simulated":
            raise ProviderError("adapter must explicitly prove no invocation and no network use")
        return {
            "receipt_version": "1.0.0",
            "request_id": request.request_id,
            "task_id": request.task_id,
            "provider_id": request.provider_id,
            "capability": request.capability,
            "status": "simulated",
            "provider_invoked": False,
            "network_used": False,
            "mode": "simulated",
            "data_classification": request.data_classification,
            "payload_sha256": payload_hash,
            "output": result.get("output", {}),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
