"""Fail-closed CODEN V4 progress calculation. Never infer requirements from PR counts."""
from decimal import Decimal, InvalidOperation

REQUIRED = {"id", "phase", "domain", "weight", "accepted", "evidence", "tests", "human_approval"}
DOMAINS = {"governance_docs", "ai_factory", "tamam_dpi", "security_ops"}

def calculate(rows):
    """Return percentages only for a complete, approved eight-phase baseline."""
    if not rows:
        return None
    seen = set()
    phases = set()
    total = Decimal(0)
    done = Decimal(0)
    domains = {name: [Decimal(0), Decimal(0)] for name in DOMAINS}
    for row in rows:
        if not isinstance(row, dict) or set(row) != REQUIRED:
            return None
        ident = row["id"]
        if not isinstance(ident, str) or not ident or ident in seen:
            return None
        seen.add(ident)
        phase = row["phase"]
        if type(phase) is not int or not 1 <= phase <= 8:
            return None
        phases.add(phase)
        domain = row["domain"]
        if domain not in DOMAINS:
            return None
        try:
            weight = Decimal(str(row["weight"]))
        except (InvalidOperation, ValueError, TypeError):
            return None
        if not weight.is_finite() or weight <= 0:
            return None
        if type(row["accepted"]) is not bool or type(row["human_approval"]) is not bool:
            return None
        if not isinstance(row["evidence"], list) or not isinstance(row["tests"], list):
            return None
        if row["accepted"] and (not row["evidence"] or not row["tests"] or not row["human_approval"]):
            return None
        total += weight
        domains[domain][0] += weight
        if row["accepted"]:
            done += weight
            domains[domain][1] += weight
    if phases != set(range(1, 9)) or any(v[0] == 0 for v in domains.values()):
        return None
    pct = lambda n, d: (n * 100 / d).quantize(Decimal("0.01"))
    progress = pct(done, total)
    return {"completed": str(progress), "remaining": str(Decimal("100.00") - progress),
            "domains": {k: str(pct(v[1], v[0])) for k, v in sorted(domains.items())},
            "denominator": str(total), "accepted_weight": str(done)}
