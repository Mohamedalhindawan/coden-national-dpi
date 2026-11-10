"""Evidence-gated V4 phase/domain scoring; no invented completion values."""
import math

DOMAINS = ('governance_documentation', 'ai_engineering_factory', 'tamam_dpi', 'security_testing_operations')

def calculate_domain_progress(data):
    """Return overall and per-domain (done, remaining) percentages or None.

    A phase's weight is distributed equally among its requirements. A domain's
    denominator is the sum of those allocations assigned to that domain.
    """
    if not isinstance(data, dict) or data.get('source_verified') is not True:
        return None
    phases = data.get('phases')
    domains = data.get('domains')
    if not isinstance(phases, list) or len(phases) != 8 or not isinstance(domains, list) or len(domains) != 4 or set(domains) != set(DOMAINS):
        return None
    totals = {d: 0.0 for d in DOMAINS}
    done = {d: 0.0 for d in DOMAINS}
    seen = set()
    for i, phase in enumerate(phases, 1):
        if not isinstance(phase, dict) or phase.get('id') != f'V4-P{i}' or phase.get('verified') is not True or not isinstance(phase.get('title'), str) or not phase['title'].strip():
            return None
        weight, requirements = phase.get('weight'), phase.get('requirements')
        if type(weight) not in (int, float) or not math.isfinite(weight) or weight <= 0 or not isinstance(requirements, list) or not requirements:
            return None
        allocation = weight / len(requirements)
        for req in requirements:
            if not isinstance(req, dict):
                return None
            rid, domain, completed = req.get('id'), req.get('domain'), req.get('completed')
            if not isinstance(rid, str) or not rid.strip() or rid != rid.strip() or rid.casefold() in seen or domain not in totals or type(completed) is not bool:
                return None
            seen.add(rid.casefold())
            if completed and (req.get('human_accepted') is not True or any(not isinstance(req.get(k), str) or not req[k].strip() for k in ('reviewed_evidence', 'executed_tests', 'acceptance_reference'))):
                return None
            totals[domain] += allocation
            if completed:
                done[domain] += allocation
    if any(not math.isfinite(v) or v <= 0 for v in totals.values()):
        return None
    def rates(n, d):
        pct = round(100 * n / d, 2)
        return pct, round(100 - pct, 2)
    return {'overall': rates(sum(done.values()), sum(totals.values())), 'domains': {d: rates(done[d], totals[d]) for d in DOMAINS}, 'denominators': totals}
