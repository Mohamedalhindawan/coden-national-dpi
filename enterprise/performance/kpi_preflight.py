"""Read-only, fail-closed KPI registry preflight for issue #55.

Not a JSON Schema validator, migration, approval, or measurement engine.
"""
import math

REQUIRED_CANONICAL = (
    "kpi_id", "objective_id", "name", "unit", "baseline", "target",
    "direction", "measurement_frequency", "status", "created_at",
)
DIRECTIONS = frozenset(("increase", "decrease", "maintain"))
FREQUENCIES = frozenset(("daily", "weekly", "monthly", "quarterly", "annually", "ad_hoc"))
STATUSES = frozenset(("draft", "active", "paused", "retired"))


def preflight_kpi_record(record):
    """Return deterministic diagnostics without synthesizing missing values."""
    if not isinstance(record, dict):
        return ["record_not_object"]
    problems = []
    if "id" in record and "kpi_id" not in record:
        problems.append("human_mapping_required_id_to_kpi_id")
    for field in REQUIRED_CANONICAL:
        if field not in record or record[field] is None or (isinstance(record[field], str) and not record[field].strip()):
            problems.append("missing_canonical_" + field)
    for field, allowed in (("direction", DIRECTIONS), ("measurement_frequency", FREQUENCIES), ("status", STATUSES)):
        if field in record and (not isinstance(record[field], str) or record[field] not in allowed):
            problems.append("invalid_canonical_" + field)
    for field in ("baseline", "target"):
        if field in record and (isinstance(record[field], bool) or not isinstance(record[field], (int, float)) or not math.isfinite(record[field])):
            problems.append("invalid_numeric_" + field)
    if "observed_value" in record or "evidence_url" in record or "reviewed_at" in record:
        problems.append("measurement_provenance_requires_separate_review")
    return problems


def preflight_kpi_registry(registry):
    """Check structure, numeric integrity and unique IDs; never approve empty templates."""
    if not isinstance(registry, dict):
        return ["registry_not_object"]
    if not isinstance(registry.get("kpis"), list):
        return ["kpis_not_list"]
    if not registry["kpis"]:
        return ["empty_template_not_approved"]
    errors = []
    seen = set()
    for index, record in enumerate(registry["kpis"]):
        errors.extend("kpis[%d]:%s" % (index, error) for error in preflight_kpi_record(record))
        if isinstance(record, dict):
            identifier = record.get("kpi_id")
            if not isinstance(identifier, str) or not identifier.strip():
                errors.append("kpis[%d]:invalid_kpi_id" % index)
            elif identifier in seen:
                errors.append("kpis[%d]:duplicate_kpi_id" % index)
            else:
                seen.add(identifier)
    return errors
