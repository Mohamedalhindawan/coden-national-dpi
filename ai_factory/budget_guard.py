"""Pure, fail-closed preflight. Does not spend money or execute agents."""
import math


def authorize_run(request):
    if not isinstance(request, dict):
        return {"allowed": False, "reason": "invalid_request"}
    if request.get("approved") is not True:
        return {"allowed": False, "reason": "human_approval_required"}
    estimate = request.get("estimated_usd")
    ceiling = request.get("max_usd")
    if (type(estimate) not in (int, float) or type(ceiling) not in (int, float)
            or not math.isfinite(estimate) or not math.isfinite(ceiling)
            or estimate < 0 or ceiling <= 0):
        return {"allowed": False, "reason": "invalid_budget"}
    if estimate > ceiling:
        return {"allowed": False, "reason": "budget_exceeded"}
    return {"allowed": True, "reason": "preflight_only"}
