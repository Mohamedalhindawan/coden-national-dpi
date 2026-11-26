"""Static R2 import-contract preflight, not a runtime admission or SDK importer.

Adapted from Sprint 26's local review. The original review-only import routine
is deliberately not transferred: root artifacts and no-site startup remain
unadmitted. No third-party imports, subprocesses or network calls.
"""
import argparse
import hashlib
import json
import os
import re
import stat

EXPECTED_LOCK_SHA = "93447ba7c43d7c8bffe1bb66d99abad1eaffcbd0d11fe1ef5bb776c7155998a3"
EXPECTED_CONTRACT_SHA = "c22cbd20bf72167164dbfbb04a5912f42dbe849c6738d30899e2841911099157"
EXPECTED_MANIFEST_SHA = "35147ce68c413cae772c9afe3782e0f3e3e07c7e9e5ba12a8324b199c7fb98f2"
FORBIDDEN_DIST = frozenset({"browser-use","browser-use-sdk","lmnr","lmnr-claude-code-proxy",
                            "func-timeout","tom-swe","pyinstaller","pyinstaller-hooks-contrib","altgraph"})
ROOTS = {name: "1.63.1" for name in ("openhands-sdk","openhands-tools",
                                    "openhands-workspace","openhands-agent-server")}
MAX_CONTRACT = 256 * 1024
MAX_BUNDLE_METADATA = 4 * 1024 * 1024
EXPECTED_ROOT_BUILD_SHA = "f396d96fe5e8f3cf1f38c2c786f749929f4bc3cc40cd9470a590c43facb9d19b"


def _require(condition, code):
    if not condition:
        raise ValueError(code)


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate_contract_key")
        result[key] = value
    return result


def validate_r2_contract(closure):
    """Read bounded regular data and require the exact independent digest."""
    with os.fdopen(os.open(closure, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        info = os.fstat(stream.fileno())
        _require(stat.S_ISREG(info.st_mode) and info.st_size <= MAX_CONTRACT,
                 "invalid_contract_file")
        raw = stream.read(MAX_CONTRACT + 1)
    _require(len(raw) <= MAX_CONTRACT and hashlib.sha256(raw).hexdigest() == EXPECTED_CONTRACT_SHA,
             "r2_contract_digest_mismatch")
    data = json.loads(raw, object_pairs_hook=_unique_keys)
    _require(data["lock_sha256"] == EXPECTED_LOCK_SHA and
             data["wheel_manifest_sha256"] == EXPECTED_MANIFEST_SHA, "wrong_r2_identity")
    _require(data["workspace_roots"] == ROOTS, "wrong_r2_roots")
    records = data["dependency_records"]
    names = {re.sub(r"[-_.]+", "-", row["name"]).lower() for row in records}
    _require(data["runtime_external_records"] == len(records) == len(names) == 126,
             "wrong_r2_external_set")
    _require(not (names & (set(ROOTS) | FORBIDDEN_DIST)), "unexpected_runtime_distribution")
    _require(all(data[key] is False for key in ("adopted","security_approved","legal_approved",
               "installation_authorized","import_authorized","release_authorized")), "contract_is_not_admission")
    return {"status":"STATIC_R2_CONTRACT_MATCH_UNAPPROVED","runtime_external_records":126,
            "root_count":4,"sdk_imported":False,"installation_authorized":False,
            "import_authorized":False,"release_authorized":False}


def _check_metadata_digest(path, expected):
    # Metadata only: never open a wheel, execute a build or discover imports.
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        info = os.fstat(stream.fileno())
        _require(stat.S_ISREG(info.st_mode) and 0 < info.st_size <= MAX_BUNDLE_METADATA,
                 "invalid_bundle_metadata_file")
        raw = stream.read(MAX_BUNDLE_METADATA + 1)
    _require(0 < len(raw) <= MAX_BUNDLE_METADATA and hashlib.sha256(raw).hexdigest() == expected,
             "r2_bundle_metadata_digest_mismatch")


def validate_r2_bundle(*, closure, lock, manifest, root_build):
    """Verify the four retained, pinned metadata files for review only.

    A matching bundle is not an authenticated reviewer decision, proof of
    target artifacts, or authorization to install or import them.
    """
    for path, expected in ((lock, EXPECTED_LOCK_SHA),
                           (manifest, EXPECTED_MANIFEST_SHA),
                           (root_build, EXPECTED_ROOT_BUILD_SHA)):
        _check_metadata_digest(path, expected)
    result = validate_r2_contract(closure)
    return dict(result, status="STATIC_R2_BUNDLE_MATCH_UNAPPROVED",
                verified_metadata_files=4, installation_authorized=False)


def inspect(closure, closure_sha=None):
    # A caller-provided hash or flag is not independent runtime admission.
    raise ValueError("independent_r2_admission_required")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--closure", required=True)
    parser.add_argument("--closure-sha256")
    parser.add_argument("--validate-contract-only", action="store_true")
    parser.add_argument("--lock")
    parser.add_argument("--manifest")
    parser.add_argument("--root-build")
    parser.add_argument("--operator-approved-import-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        if not args.validate_contract_only or args.operator_approved_import_only:
            inspect(args.closure, args.closure_sha256)
        bundle = (args.lock, args.manifest, args.root_build)
        if any(bundle):
            _require(all(bundle), "complete_bundle_required")
            result = validate_r2_bundle(closure=args.closure, lock=args.lock,
                                        manifest=args.manifest, root_build=args.root_build)
        else:
            result = validate_r2_contract(args.closure)
    except (OSError, ValueError, KeyError, TypeError):
        print(json.dumps({"status":"BLOCKED","sdk_imported":False,"installation_authorized":False,
                          "import_authorized":False,"release_authorized":False}))
        return 1
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
