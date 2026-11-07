"""Pure resource allocation policy helpers."""
from __future__ import annotations

from datetime import date


class ResourceAllocationError(ValueError):
    """Raised when a resource allocation violates date policy."""


def validate_resource_allocation(allocation: dict) -> None:
    """Reject allocations whose date range is missing, malformed, or reversed.

    Schema validation, identity checks, capacity aggregation, authorization,
    and persistence remain responsibilities of the trusted service layer.
    """
    if not isinstance(allocation, dict):
        raise ResourceAllocationError("Resource allocation must be an object")

    start_value = allocation.get("start_date")
    end_value = allocation.get("end_date")
    if not isinstance(start_value, str) or not isinstance(end_value, str):
        raise ResourceAllocationError("start_date and end_date are required ISO dates")

    try:
        start = date.fromisoformat(start_value)
        end = date.fromisoformat(end_value)
    except ValueError as exc:
        raise ResourceAllocationError("Allocation dates must be valid ISO calendar dates") from exc

    if end < start:
        raise ResourceAllocationError("end_date cannot be earlier than start_date")
