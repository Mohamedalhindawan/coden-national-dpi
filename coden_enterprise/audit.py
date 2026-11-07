"""Local hash-chained audit event integrity helpers.

This is an integrity primitive, not durable or independently tamper-proof storage.
"""
from __future__ import annotations

import hashlib
import json


class AuditIntegrityError(ValueError):
    """Raised when an audit event or chain fails integrity validation."""


_GENESIS_HASH = "0" * 64
_RESERVED_FIELDS = {"sequence", "previous_hash", "event_hash"}
_REQUIRED_FIELDS = {"event_id", "action", "actor_id", "subject_id"}


def _digest(event: dict) -> str:
    try:
        encoded = json.dumps(
            event, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AuditIntegrityError("Audit event must contain canonical JSON values") from exc
    return hashlib.sha256(encoded).hexdigest()


def verify_chain(events: list[dict]) -> bool:
    """Verify sequence, linkage, unique IDs, and each event digest."""
    previous = _GENESIS_HASH
    seen_ids = set()
    for expected_sequence, event in enumerate(events, start=1):
        if not isinstance(event, dict):
            raise AuditIntegrityError("Each audit event must be an object")
        if event.get("sequence") != expected_sequence:
            raise AuditIntegrityError("Audit sequence is missing, reordered, or discontinuous")
        if event.get("previous_hash") != previous:
            raise AuditIntegrityError("Audit previous_hash linkage is invalid")
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not event_id or event_id in seen_ids:
            raise AuditIntegrityError("Audit event_id is missing or duplicated")
        supplied_hash = event.get("event_hash")
        if not isinstance(supplied_hash, str) or supplied_hash != _digest(
            {key: value for key, value in event.items() if key != "event_hash"}
        ):
            raise AuditIntegrityError("Audit event digest does not match its contents")
        seen_ids.add(event_id)
        previous = supplied_hash
    return True


def append_event(events: list[dict], payload: dict) -> dict:
    """Append one event to a mutable in-memory chain after validating its inputs."""
    if not isinstance(events, list):
        raise AuditIntegrityError("events must be a list")
    verify_chain(events)
    if not isinstance(payload, dict):
        raise AuditIntegrityError("Audit payload must be an object")
    if _RESERVED_FIELDS.intersection(payload):
        raise AuditIntegrityError("Payload cannot set chain-managed fields")
    missing = _REQUIRED_FIELDS.difference(payload)
    if missing:
        raise AuditIntegrityError(f"Audit payload missing fields: {sorted(missing)}")
    if any(event["event_id"] == payload["event_id"] for event in events):
        raise AuditIntegrityError("Audit event_id must be unique")
    event = dict(payload)
    event["sequence"] = len(events) + 1
    event["previous_hash"] = events[-1]["event_hash"] if events else _GENESIS_HASH
    event["event_hash"] = _digest(event)
    events.append(event)
    return event
