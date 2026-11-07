"""Policy-first model gateway. Selection is simulated; no provider or network calls."""
from dataclasses import dataclass
import math
import re
from datetime import datetime, timezone


class GatewayError(ValueError):
    pass


ALLOWED_CAPABILITIES = {
    "reasoning", "architecture", "coding", "testing", "documentation",
    "security_review", "data_engineering", "dpi_architecture",
}
ALLOWED_CLASSIFICATIONS = {"synthetic", "public"}


@dataclass(frozen=True)
class ModelProfile:
    model_id: str
    provider_id: str
    capabilities: tuple
    context_window: int
    input_cost_per_1k: float
    output_cost_per_1k: float
    enabled: bool = True

    def __post_init__(self):
        if not re.fullmatch(r"[a-z][a-z0-9._-]{1,63}", self.model_id or ""):
            raise GatewayError("invalid model_id")
        if not re.fullmatch(r"[a-z][a-z0-9-]{1,31}", self.provider_id or ""):
            raise GatewayError("invalid provider_id")
        if not isinstance(self.capabilities, tuple) or not self.capabilities:
            raise GatewayError("capabilities must be a non-empty tuple")
        if any(cap not in ALLOWED_CAPABILITIES for cap in self.capabilities):
            raise GatewayError("unsupported model capability")
        if type(self.context_window) is not int or self.context_window <= 0:
            raise GatewayError("context_window must be a positive integer")
        for value in (self.input_cost_per_1k, self.output_cost_per_1k):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise GatewayError("token costs must be finite non-negative numbers")
        if type(self.enabled) is not bool:
            raise GatewayError("enabled must be boolean")


@dataclass(frozen=True)
class ModelRequest:
    request_id: str
    task_id: str
    capability: str
    estimated_input_tokens: int
    max_output_tokens: int
    max_cost_usd: float
    data_classification: str


@dataclass(frozen=True)
class GatewayPolicy:
    mode: str = "simulated"
    network: str = "disabled"
    human_approval: bool = True
    max_input_tokens: int = 100000
    max_output_tokens: int = 16000


class ModelGateway:
    def __init__(self):
        self._models = {}
        self._request_ids = set()

    def register_model(self, profile):
        if not isinstance(profile, ModelProfile):
            raise GatewayError("profile must be a ModelProfile")
        if profile.model_id in self._models:
            raise GatewayError("model already registered")
        self._models[profile.model_id] = profile

    def set_enabled(self, model_id, enabled):
        if type(enabled) is not bool:
            raise GatewayError("enabled must be boolean")
        profile = self._models.get(model_id)
        if profile is None:
            raise GatewayError("unknown model")
        self._models[model_id] = ModelProfile(
            profile.model_id, profile.provider_id, profile.capabilities,
            profile.context_window, profile.input_cost_per_1k,
            profile.output_cost_per_1k, enabled,
        )

    @staticmethod
    def _validate(request, policy):
        if not isinstance(request, ModelRequest) or not isinstance(policy, GatewayPolicy):
            raise GatewayError("request and policy types are required")
        if not request.request_id or not request.task_id:
            raise GatewayError("request_id and task_id are required")
        if request.capability not in ALLOWED_CAPABILITIES:
            raise GatewayError("unsupported capability")
        if request.data_classification not in ALLOWED_CLASSIFICATIONS:
            raise GatewayError("only synthetic or public data is allowed")
        for name, value in (("estimated_input_tokens", request.estimated_input_tokens),
                            ("max_output_tokens", request.max_output_tokens)):
            if type(value) is not int or value < 0:
                raise GatewayError(name + " must be a non-negative integer")
        if isinstance(request.max_cost_usd, bool) or not isinstance(request.max_cost_usd, (int, float)) or not math.isfinite(request.max_cost_usd) or request.max_cost_usd < 0:
            raise GatewayError("max_cost_usd must be finite and non-negative")
        if policy.mode != "simulated" or policy.network != "disabled":
            raise GatewayError("live mode and network access are disabled")
        if policy.human_approval is not True:
            raise GatewayError("human approval is mandatory")
        if request.estimated_input_tokens > policy.max_input_tokens or request.max_output_tokens > policy.max_output_tokens:
            raise GatewayError("request exceeds gateway token policy")

    def route(self, request, policy):
        self._validate(request, policy)
        if request.request_id in self._request_ids:
            raise GatewayError("duplicate request_id")
        total_tokens = request.estimated_input_tokens + request.max_output_tokens
        eligible = []
        for model in self._models.values():
            if not model.enabled or request.capability not in model.capabilities:
                continue
            if total_tokens > model.context_window:
                continue
            estimated_cost = (
                request.estimated_input_tokens * model.input_cost_per_1k
                + request.max_output_tokens * model.output_cost_per_1k
            ) / 1000
            if estimated_cost <= request.max_cost_usd:
                eligible.append((estimated_cost, model.model_id, model))
        if not eligible:
            raise GatewayError("no enabled model satisfies capability, context, and request budget")
        estimated_cost, _, selected = min(eligible, key=lambda item: (item[0], item[1]))
        self._request_ids.add(request.request_id)
        return {
            "gateway_version": "1.0.0",
            "request_id": request.request_id,
            "task_id": request.task_id,
            "provider_id": selected.provider_id,
            "model_id": selected.model_id,
            "capability": request.capability,
            "selection_basis": "capability_context_and_estimated_request_cost",
            "estimated_cost_usd": round(estimated_cost, 10),
            "max_cost_usd": request.max_cost_usd,
            "estimated_input_tokens": request.estimated_input_tokens,
            "max_output_tokens": request.max_output_tokens,
            "mode": "simulated",
            "provider_invoked": False,
            "network_used": False,
            "human_approval_required": True,
            "data_classification": request.data_classification,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
