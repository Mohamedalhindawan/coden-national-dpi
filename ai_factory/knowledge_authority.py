"""Fail-closed synthetic metadata comparison for a declared RAG source of truth.

Does NOT authenticate the registry, authorize retrieval, access Notion/GitHub,
verify actual source file bytes, evaluate content or answer user questions.
The operator/IAM must supply an independently authenticated authority record.
"""

import hmac
import re

LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
REVISION = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z")
DIGEST = re.compile(r"[a-f0-9]{64}\Z")
AUTHORITY_KEYS = frozenset({
    "schema", "doc_id", "source_system", "source_revision", "source_sha256",
    "classification", "approved", "deleted", "authorized_principals",
})
RECORD_KEYS = frozenset({"doc_id", "source_system", "source_revision", "source_sha256"})
SYSTEMS = frozenset({"github", "notion"})


def _text(value, pattern):
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ValueError("invalid source metadata")
    return value


def _authority(metadata):
    if not isinstance(metadata, dict) or set(metadata) != AUTHORITY_KEYS:
        raise ValueError("invalid authority fields")
    if metadata["schema"] != "coden.knowledge.authority.v1":
        raise ValueError("unsupported authority schema")
    _text(metadata["doc_id"], LABEL)
    if metadata["source_system"] not in SYSTEMS:
        raise ValueError("unsupported source system")
    _text(metadata["source_revision"], REVISION)
    _text(metadata["source_sha256"], DIGEST)
    if metadata["classification"] != "synthetic":
        raise ValueError("sensitive source data not allowed in prototype")
    if type(metadata["approved"]) is not bool or type(metadata["deleted"]) is not bool:
        raise ValueError("approval/deletion must be boolean")
    principals = metadata["authorized_principals"]
    if not isinstance(principals, list) or not 1 <= len(principals) <= 16:
        raise ValueError("invalid principal allowlist")
    for p in principals:
        _text(p, LABEL)
    if len(principals) != len(set(principals)):
        raise ValueError("duplicate principal")


def _record(record):
    if not isinstance(record, dict) or set(record) != RECORD_KEYS:
        raise ValueError("unknown source record fields")
    _text(record["doc_id"], LABEL)
    if record["source_system"] not in SYSTEMS:
        raise ValueError("unknown source")
    _text(record["source_revision"], REVISION)
    _text(record["source_sha256"], DIGEST)


def resolve_candidate(authority, records, principal):
    """Select only exact canonical source metadata, never raw text or ACL approval."""
    _authority(authority)
    _text(principal, LABEL)
    if not isinstance(records, list) or len(records) > 32:
        raise ValueError("invalid records collection")
    for rec in records:
        _record(rec)
    denied = {"decision": "deny", "retrieval_authorized": False}
    blocked = {"decision": "blocked", "retrieval_authorized": False}
    if (not authority["approved"] or authority["deleted"] or
            principal not in authority["authorized_principals"]):
        return denied
    matching_id_and_system = [
        rec for rec in records if rec["doc_id"] == authority["doc_id"] and
        rec["source_system"] == authority["source_system"]
    ]
    if len(matching_id_and_system) != 1:
        return blocked
    selected = matching_id_and_system[0]
    if (selected["source_revision"] != authority["source_revision"] or
            not hmac.compare_digest(selected["source_sha256"], authority["source_sha256"])):
        return blocked
    return {
        "decision": "candidate",
        "source_system": selected["source_system"],
        "source_revision": selected["source_revision"],
        "source_sha256": selected["source_sha256"],
        "retrieval_authorized": False,
        "source_content_verified": False,
        "authority_authenticated": False,
    }
