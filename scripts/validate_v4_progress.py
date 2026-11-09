"""Evidence-gated V4 progress scoring. Accepts a JSON baseline."""
import json
import sys
import math
from urllib.parse import urlparse

PHASES = {f"P{i}" for i in range(1, 9)}

def calculate_progress(b):
    if not all((b.get("full_master_text_committed"), b.get("requirements_decomposed_and_audited"), b.get("weights_approved"), b.get("baseline_approved_by"))):
        return {"status": "not_measurable", "completion_percent": None, "remaining_percent": None}
    phases, requirements = b.get("phases", []), b.get("requirements", [])
    if not isinstance(phases, list) or not isinstance(requirements, list) or any(not isinstance(p, dict) for p in phases) or any(not isinstance(r, dict) for r in requirements):
        raise ValueError("Phases and requirements must be lists of objects")
    if any(not isinstance(p.get("id"), str) for p in phases):
        raise ValueError("Phase IDs must be strings")
    if len(phases) != 8 or {p.get("id") for p in phases} != PHASES or not requirements:
        raise ValueError("Eight phases and requirements are mandatory")
    weights = {p["id"]: p.get("approved_weight") for p in phases}
    if any(type(w) not in (int, float) or not math.isfinite(w) or w <= 0 for w in weights.values()) or abs(sum(weights.values()) - 1) > 1e-8:
        raise ValueError("Approved phase weights must sum to 1")
    groups, seen = {p: [] for p in PHASES}, set()
    for r in requirements:
        ident, phase, weight, score = (r.get(k) for k in ("id", "phase", "weight", "score"))
        if not isinstance(ident, str) or not ident or ident in seen:
            raise ValueError("Unique requirement ID required")
        seen.add(ident)
        if not isinstance(phase, str) or phase not in groups or type(weight) not in (int, float) or weight <= 0 or type(score) not in (int, float) or score not in (0, .25, .5, .75, 1) or not math.isfinite(weight):
            raise ValueError("Invalid phase, weight or score")
        if score > .25 and (not isinstance(r.get("evidence_url"), str) or not r["evidence_url"].startswith("https://") or any(c.isspace() for c in r["evidence_url"]) or urlparse(r["evidence_url"]).scheme != "https" or not urlparse(r["evidence_url"]).hostname or urlparse(r["evidence_url"]).username is not None or urlparse(r["evidence_url"]).password is not None):
            raise ValueError("Evidence required for score above 0.25")
        if score > .25 and r.get("critical_blocker"):
            raise ValueError("Critical blocker caps score at 0.25")
        groups[phase].append((weight, score))
    if any(not rows for rows in groups.values()):
        raise ValueError("Every phase needs at least one requirement")
    value = sum(weights[p] * sum(w * s for w, s in rows) / sum(w for w, _ in rows) for p, rows in groups.items())
    completed = round(100 * value, 1)
    return {"status": "measured", "completion_percent": completed, "remaining_percent": round(100 - completed, 1)}

if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        print(json.dumps(calculate_progress(json.load(f))))
