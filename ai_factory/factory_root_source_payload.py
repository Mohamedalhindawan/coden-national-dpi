"""Review root package bytes against a pinned source-derived inventory.

This is not build provenance or authorization. The inventory covers tracked
package payloads, not generated dist-info, the build backend or installed paths.
"""
import hashlib
import json

EXPECTED_SHA256 = "18969fca5913ace8706d9eb549493dd42d29707e36c5bbba66f4a21ead9e648a"
ROOTS = frozenset(("openhands-sdk", "openhands-tools", "openhands-workspace", "openhands-agent-server"))


def compare_root_source_payloads(receipt, expectations_bytes):
    """Compare a scanner receipt; its origin is not authenticated by this API."""
    if (type(expectations_bytes) is not bytes or len(expectations_bytes) > 256 * 1024
            or hashlib.sha256(expectations_bytes).hexdigest() != EXPECTED_SHA256):
        raise ValueError("root source expectation digest mismatch")
    expected = json.loads(expectations_bytes)["roots"]
    if set(expected) != ROOTS:
        raise ValueError("unexpected source root set")
    if (type(receipt) is not dict or receipt.get("release_authorized") is not False
            or any(receipt.get(key) is not True for key in ("record_verified", "root_install_paths_disjoint", "metadata_dependencies_verified"))):
        raise ValueError("root wheel review prerequisites missing")
    wheels = receipt.get("wheels")
    if type(wheels) is not list or len(wheels) != len(ROOTS):
        raise ValueError("unexpected root wheel receipt set")
    seen = set()
    counts = {}
    for wheel in wheels:
        if type(wheel) is not dict or type(wheel.get("distribution")) is not dict:
            raise ValueError("invalid root wheel receipt")
        name = wheel["distribution"].get("name")
        if type(name) is not str or name not in ROOTS or name in seen or wheel["distribution"].get("version") != "1.63.1":
            raise ValueError("unexpected root distribution")
        seen.add(name)
        prefix = name.replace("-", "_") + "-1.63.1.dist-info/"
        files = wheel.get("files")
        if type(files) is not dict or len(files) > 5000 or any(type(p) is not str for p in files):
            raise ValueError("invalid root file receipt")
        payload = {path: row for path, row in files.items() if not path.startswith(prefix)}
        target = expected[name]
        required = {path for path, row in target.items() if row["required"]}
        if not required <= set(payload) <= set(target):
            raise ValueError("root payload missing or unexpected member")
        for path, row in payload.items():
            pin = target[path]
            if (type(row) is not dict or row.get("record_hash_verified") is not True
                    or row.get("sha256") != pin["sha256"] or type(row.get("bytes")) is not int
                    or row["bytes"] != pin["bytes"]):
                raise ValueError("root payload byte mismatch")
        counts[name] = len(payload)
    return {"status": "ROOT_SOURCE_PAYLOAD_MATCH_REVIEW_ONLY", "source_payload_match": True,
            "matched_payload_files": sum(counts.values()), "root_payload_counts": counts,
            "receipt_origin_verified": False, "source_to_wheel_verified": False,
            "build_authorized": False, "installation_authorized": False, "release_authorized": False}


def review_root_source_payloads(candidates, *, lock_bytes, expectations_bytes):
    """Review actual wheel bytes with the strict scanner, then compare payloads.

    No install, import of candidate packages, build or network operation.
    The source comparison cannot establish the identity of the builder.
    """
    from ai_factory.factory_wheel_notice_audit import inspect_root_wheel_outputs
    if type(lock_bytes) is not bytes:
        raise ValueError("exact R2 lock required")
    receipt = inspect_root_wheel_outputs(candidates, lock_bytes=lock_bytes)
    return {"wheel_review": receipt, "payload_review": compare_root_source_payloads(receipt, expectations_bytes),
            "installation_authorized": False, "release_authorized": False}
