"""Fail-closed preflight for #51 risk records before #46 schema migration.

No implicit field mapping or risk scoring; not a schema validator.
"""
REQUIRED_SOURCE_FIELDS = ("id", "title", "description")
UNRESOLVED_MAPPINGS = ("initiative_id", "likelihood", "impact", "identified_at", "status")


def preflight_risk_record(record):
    """Return diagnostic codes; never synthesize governance decisions."""
    if not isinstance(record, dict):
        return ["record_not_object"]
    errors = []
    for field in REQUIRED_SOURCE_FIELDS:
        if not isinstance(record.get(field), str) or not record[field].strip():
            errors.append("missing_source_" + field)
    for field in UNRESOLVED_MAPPINGS:
        errors.append("human_mapping_required_" + field)
    if record.get("owner") in (None, "", "unassigned"):
        errors.append("owner_unassigned")
    return errors
