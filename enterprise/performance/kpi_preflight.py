"""Read-only, fail-closed KPI registry preflight for issue #55.

Not a JSON Schema validator, migration, approval, or measurement engine.
"""
import math
import re
from datetime import datetime

REQUIRED_CANONICAL = (
    "kpi_id", "objective_id", "name", "unit", "baseline", "target",
    "direction", "measurement_frequency", "status", "created_at",
)
DIRECTIONS = frozenset(("increase", "decrease", "maintain"))
FREQUENCIES = frozenset(("daily", "weekly", "monthly", "quarterly", "annually", "ad_hoc"))
STATUSES = frozenset(("draft", "active", "paused", "retired"))
IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]*$")
ALLOWED_FIELDS = frozenset(REQUIRED_CANONICAL + ("definition", "owner_id"))
RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")


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
    for field in ("kpi_id", "objective_id", "owner_id"):
        if field in record and (not isinstance(record[field], str) or not 3 <= len(record[field]) <= 100 or IDENTIFIER_PATTERN.fullmatch(record[field]) is None):
            problems.append("invalid_canonical_" + field)
    for field, maximum, minimum in (("name", 160, 3), ("unit", 40, 1), ("definition", 2000, 0)):
        if field in record and (not isinstance(record[field], str) or not minimum <= len(record[field]) <= maximum):
            problems.append("invalid_canonical_" + field)
    for field, allowed in (("direction", DIRECTIONS), ("measurement_frequency", FREQUENCIES), ("status", STATUSES)):
        if field in record and (not isinstance(record[field], str) or record[field] not in allowed):
            problems.append("invalid_canonical_" + field)
    for field in ("baseline", "target"):
        if field in record:
            value = record[field]
            try:
                valid_number = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)
            except (OverflowError, ValueError):
                valid_number = False
            if not valid_number:
                problems.append("invalid_numeric_" + field)
    if "created_at" in record:
        stamp = record["created_at"]
        valid = isinstance(stamp, str) and RFC3339.fullmatch(stamp) is not None
        if valid:
            try:
                datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            except ValueError:
                valid = False
        if not valid:
            problems.append("invalid_canonical_created_at")
    # JSON object keys must be strings. Reject malformed Python/YAML mappings
    # without sorting mixed key types or raising TypeError.
    for field in record:
        if not isinstance(field, str):
            problems.append("non_string_canonical_field_key")
    for field in sorted(key for key in record if isinstance(key, str) and key not in ALLOWED_FIELDS):
        problems.append("unknown_canonical_field:" + field)
    if "observed_value" in record or "evidence_url" in record or "reviewed_at" in record:
        problems.append("measurement_provenance_requires_separate_review")
    return problems


def preflight_kpi_registry(registry):
    """Check structure, numeric integrity and unique IDs; never approve empty templates."""
    if not isinstance(registry, dict):
        return ["registry_not_object"]
    # Only the documented root key is accepted; do not silently ignore metadata.
    if any(not isinstance(key, str) for key in registry):
        return ["non_string_registry_root_key"]
    if "kpis" not in registry or not isinstance(registry["kpis"], list):
        return ["kpis_not_list"]
    # Historical draft templates may carry status=draft; this is not approval.
    # Any other root metadata, including an approval-looking status, fails closed.
    if set(registry) - {"kpis", "status"}:
        return ["unknown_registry_root_field"]
    if "status" in registry and registry["status"] != "draft":
        return ["unknown_registry_root_field"]
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
