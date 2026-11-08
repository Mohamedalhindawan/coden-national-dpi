"""Policy-first routing recommendations. This module never invokes providers or tools."""
from copy import deepcopy


class RoutingError(ValueError):
    pass


TASK_ROUTES = {
    "planning": ("PLN-01", "read_workspace", "reasoning"),
    "architecture": ("ARC-01", "read_workspace", "architecture"),
    "dpi_design": ("DPI-01", "read_workspace", "dpi_architecture"),
    "software_implementation": ("DEV-01", "write_task_branch", "coding"),
    "data_engineering": ("DATA-01", "read_synthetic_fixtures", "data_engineering"),
    "security_review": ("SEC-01", "run_security_scans", "security"),
    "quality_assurance": ("QA-01", "run_tests", "testing"),
    "documentation": ("DOC-01", "write_docs_branch", "technical_writing"),
    "cost_analysis": ("FIN-01", "read_cost_metadata", "finops"),
    "release_review": ("REL-01", "read_release_artifacts", "release"),
    "benefits_decision": ("DPI-01", "read_workspace", "policy_analysis"),
    "health_decision": ("DPI-01", "read_workspace", "policy_analysis"),
    "identity_decision": ("SEC-01", "read_workspace", "security"),
    "financial_transaction": ("FIN-01", "read_cost_metadata", "finops"),
}
ALLOWED_CLASSIFICATIONS = {"synthetic", "public", "sensitive"}
HIGH_IMPACT_TASKS = {
    "benefits_decision", "health_decision", "identity_decision",
    "financial_transaction",
}
VALID_RISKS = {"low", "medium", "high", "critical"}


def recommend_route(profile):
    if not isinstance(profile, dict):
        raise RoutingError("profile must be an object")
    required = {"task_type", "risk_level", "data_classification",
                "network_required", "requires_code_execution"}
    missing = required - set(profile)
    if missing:
        raise RoutingError("missing profile fields: " + ", ".join(sorted(missing)))
    task_type = profile["task_type"]
    if task_type not in TASK_ROUTES:
        raise RoutingError("unsupported task_type")
    if profile["risk_level"] not in VALID_RISKS:
        raise RoutingError("invalid risk_level")
    classification = profile["data_classification"]
    if classification not in ALLOWED_CLASSIFICATIONS:
        raise RoutingError("only synthetic, public, or explicitly reviewed sensitive metadata is allowed")
    if type(profile["network_required"]) is not bool or type(profile["requires_code_execution"]) is not bool:
        raise RoutingError("network_required and requires_code_execution must be booleans")
    if profile["network_required"]:
        raise RoutingError("network-enabled routes are disabled in this prototype")
    role, suggested_tool, capability = TASK_ROUTES[task_type]
    high_impact = task_type in HIGH_IMPACT_TASKS or profile["risk_level"] in {"high", "critical"}
    human_approval = True
    recommendation_only = high_impact or classification == "sensitive"
    provider = profile.get("provider")
    if provider is not None and (not isinstance(provider, str) or not provider.strip()):
        raise RoutingError("provider must be a non-empty string when supplied")
    route = {
        "routing_version": "1.0.0",
        "task_type": task_type,
        "agent_role": role,
        "capability": capability,
        "suggested_tool": suggested_tool,
        "provider": provider,
        "provider_selection_basis": "user_supplied" if provider else "not_selected",
        "provider_invoked": False,
        "execution_mode": "recommendation_only" if recommendation_only else "dry_run",
        "network": "disabled",
        "human_approval_required": human_approval,
        "high_impact": high_impact,
        "data_classification": classification,
        "requires_code_execution": profile["requires_code_execution"],
        "selection_basis": "task_capability_and_policy",
        "limitations": [
            "Routing is a recommendation, not an execution command.",
            "No provider is scored or ranked by this module.",
            "Human approval is required before any execution.",
            "Sensitive or high-impact work remains recommendation-only.",
        ],
    }
    return validate_route_policy(route)


def validate_route_policy(route):
    if not isinstance(route, dict):
        raise RoutingError("route must be an object")
    if route.get("provider_invoked") is not False:
        raise RoutingError("provider invocation is prohibited")
    if route.get("network") != "disabled":
        raise RoutingError("network must remain disabled")
    if route.get("execution_mode") not in {"dry_run", "recommendation_only"}:
        raise RoutingError("unsupported execution mode")
    if route.get("human_approval_required") is not True:
        raise RoutingError("human approval is mandatory")
    if route.get("data_classification") not in ALLOWED_CLASSIFICATIONS:
        raise RoutingError("unsupported data classification")
    if (route.get("high_impact") or route.get("data_classification") == "sensitive") and route.get("execution_mode") != "recommendation_only":
        raise RoutingError("high-impact or sensitive work must remain recommendation-only")
    if route.get("agent_role") not in {entry[0] for entry in TASK_ROUTES.values()}:
        raise RoutingError("unknown agent role")
    return deepcopy(route)
