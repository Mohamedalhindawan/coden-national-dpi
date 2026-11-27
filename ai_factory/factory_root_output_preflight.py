"""Review exactly four root wheel files from a dedicated directory; never install.

No output digest or matching source contract constitutes builder provenance,
immutable staging, independent approval or permission to execute the wheels.
"""
import argparse
import hashlib
import json
import os
import stat
import tarfile

from .factory_build_materials import PINS, _open_directory, _stamp
from .factory_r2_build_preflight import _inventory_from_source
from .factory_root_source_payload import review_root_source_payloads, ROOTS

MAX_OUTPUT_BYTES = 8 * 1024**2
FILENAMES = {name.replace("-", "_") + "-1.63.1-py3-none-any.whl": name
             for name in ROOTS}


def _read_file(directory, name, remaining):
    with os.fdopen(os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                           dir_fd=directory), "rb") as stream:
        before = os.fstat(stream.fileno())
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                or not 0 < before.st_size <= remaining):
            raise ValueError("unsafe or oversized staged file")
        raw = stream.read(before.st_size + 1)
        if (len(raw) != before.st_size or _stamp(before) != _stamp(os.fstat(stream.fileno()))
                or _stamp(before) != _stamp(os.stat(name, dir_fd=directory, follow_symlinks=False))):
            raise ValueError("staged file changed during read")
    return raw


def _require_exact_directory(fd):
    seen = set()
    with os.scandir(fd) as entries:
        for entry in entries:
            if entry.name not in FILENAMES:
                raise ValueError("unexpected root output entry")
            seen.add(entry.name)
    if seen != set(FILENAMES):
        raise ValueError("missing root output file")


def review_output_directory(directory, *, lock_bytes, expectations_bytes):
    fd = _open_directory(directory)
    try:
        _require_exact_directory(fd)
        remaining = MAX_OUTPUT_BYTES
        candidates = []
        by_digest = {}
        for filename, expected_name in sorted(FILENAMES.items()):
            raw = _read_file(fd, filename, remaining)
            remaining -= len(raw)
            digest = hashlib.sha256(raw).hexdigest()
            if digest in by_digest:
                raise ValueError("duplicate root wheel bytes")
            by_digest[digest] = (filename, expected_name)
            candidates.append((raw, digest))
        _require_exact_directory(fd)
    finally:
        os.close(fd)
    result = review_root_source_payloads(candidates, lock_bytes=lock_bytes,
                                         expectations_bytes=expectations_bytes)
    scan, payload = result["wheel_review"], result["payload_review"]
    reviewed = []
    for item in scan["wheels"]:
        digest = item["wheel_sha256"]
        filename, expected_name = by_digest[digest]
        if item["distribution"]["name"] != expected_name:
            raise ValueError("root wheel filename identity mismatch")
        reviewed.append({"filename": filename, "sha256": digest,
                         "bytes": item["compressed_bytes"]})
    return {"status": "ROOT_OUTPUT_DIRECTORY_REVIEW_ONLY", "wheel_count": len(reviewed),
            "wheels": sorted(reviewed, key=lambda row: row["filename"]),
            "total_compressed_bytes": MAX_OUTPUT_BYTES - remaining,
            "matched_payload_files": payload["matched_payload_files"],
            "console_script_count": scan["console_script_count"],
            "filename_identity_match": True, "record_verified": True,
            "source_payload_match": True, "metadata_dependencies_verified": True,
            "root_generated_metadata_verified": True,
            "builder_provenance_verified": False, "immutable_snapshot_verified": False,
            "external_install_paths_verified": False, "source_to_wheel_verified": False,
            "independent_review": False, "build_authorized": False,
            "installation_authorized": False, "release_authorized": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("outputs_directory")
    parser.add_argument("materials_directory")
    parser.add_argument("source_directory")
    args = parser.parse_args(argv)
    try:
        fd = _open_directory(args.materials_directory)
        try:
            size, digest = PINS["pyo3-candidate.lock"]
            lock = _read_file(fd, "pyo3-candidate.lock", size)
            if len(lock) != size or hashlib.sha256(lock).hexdigest() != digest:
                raise ValueError("lock digest mismatch")
        finally:
            os.close(fd)
        fd = _open_directory(args.source_directory)
        try:
            expectations = _inventory_from_source(fd)
        finally:
            os.close(fd)
        result = review_output_directory(args.outputs_directory, lock_bytes=lock,
                                         expectations_bytes=expectations)
    except (OSError, ValueError, tarfile.TarError, EOFError):
        print(json.dumps({"status": "ROOT_OUTPUT_DIRECTORY_BLOCKED",
                          "build_authorized": False, "installation_authorized": False,
                          "release_authorized": False}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
