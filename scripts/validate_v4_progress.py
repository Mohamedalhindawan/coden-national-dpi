"""Evidence-gated V4 progress scoring. Accepts a JSON baseline."""
import json
import sys

PHASES = {f"P{i}" for i in range(1, 9)}

def calculate_progress(b):
    if not all((b.get("full_master_text_committed"), b.get("requirements_decomposed_and_audited"), b.get("weights_approved"), b.get("baseline_approved_by"))):
        return {"status": "not_measurable", "completion_percent": None, "remaining_percent": None}
    phases, requirements = b.get("phases", []), b.get("requirements", [])
    if len(phases) != 8 or {p.get("id") for p in phases} != PHASES or not requirements:
        raise ValueError("Eight phases and requirements are mandatory")
    weights = {p["id"]: p.get("approved_weight") for p in phases}
    if any(type(w) not in (int, float) or w <= 0 for w in weights.values()) or abs(sum(weights.values()) - 1) > 1e-8:
        raise ValueError("Approved phase weights must sum to 1")
    groups, seen = {p: [] for p in PHASES}, set()
    for r in requirements:
        ident, phase, weight, score = (r.get(k) for k in ("id", "phase", "weight", "score"))
        if not isinstance(ident, str) or not ident or ident in seen:
            raise ValueError("Unique requirement ID required")
        seen.add(ident)
        if phase not in groups or type(weight) not in (int, float) or weight <= 0 or score not in (0, .25, .5, .75, 1):
            raise ValueError("Invalid phase, weight or score")
        if score > .25 and not r.get("evidence_url"):
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
