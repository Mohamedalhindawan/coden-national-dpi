"""Independent, bounded filesystem evidence for synthetic CODEN runtime results.

A provider-reported digest is an assertion, not proof. This verifier compares
a canonical manifest digest and each listed output file against bytes on an
operator-controlled local filesystem. It does not execute code, call models,
check software correctness, approve releases, sign evidence or scan secrets.

The artifact directory must be protected against concurrent/untrusted writes:
a post-run scan cannot provide a race-free snapshot of a hostile filesystem.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import stat

from . import runtime_contract

SCHEMA = "coden.artifact.bundle.v1"
SHA = re.compile(r"[a-f0-9]{64}\Z")
SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
MAX_FILES = 32
MAX_DIRS = 64
MAX_DEPTH = 6
MAX_FILE_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024


def _valid_path(name):
    if not isinstance(name, str) or not 1 <= len(name) <= 192:
        raise ValueError("invalid output path")
    parts = name.split("/")
    if len(parts) > MAX_DEPTH + 1 or any(
        part in (".", "..") or not SEGMENT.fullmatch(part) for part in parts
    ):
        raise ValueError("unsafe artifact path")
    return name


def _canonical(obj):
    return json.dumps(obj, allow_nan=False, ensure_ascii=True,
                      sort_keys=True, separators=(",", ":")).encode("utf-8")


def _verify_manifest_shape(manifest, task_id):
    if not isinstance(manifest, dict) or set(manifest) != {"schema", "task_id", "files"}:
        raise ValueError("invalid artifact manifest fields")
    if manifest["schema"] != SCHEMA or manifest["task_id"] != task_id:
        raise ValueError("artifact manifest identity mismatch")
    files = manifest["files"]
    if not isinstance(files, list) or not 1 <= len(files) <= MAX_FILES:
        raise ValueError("invalid artifact file list")
    checked = {}
    cumulative_size = 0
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "bytes"}:
            raise ValueError("invalid artifact file entry")
        name = _valid_path(item["path"])
        digest = item["sha256"]
        size = item["bytes"]
        if not isinstance(digest, str) or not SHA.fullmatch(digest):
            raise ValueError("invalid output digest")
        if type(size) is not int or not 0 <= size <= MAX_FILE_BYTES:
            raise ValueError("invalid output size")
        if name in checked:
            raise ValueError("duplicate artifact")
        checked[name] = (digest, size)
        cumulative_size += size
        if cumulative_size > MAX_TOTAL_BYTES:
            raise ValueError("artifact bundle exceeds size bound")
    if list(checked) != sorted(checked):
        raise ValueError("manifest files must be sorted by relative path")
    return checked


def _root(path):
    root = Path(path).absolute()
    if not root.is_dir() or any(part.is_symlink() for part in (root, *root.parents)):
        raise ValueError("trusted regular artifact root required")
    return root


def _hash_regular_file(file):
    fd = os.open(file, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE_BYTES:
            raise ValueError("invalid artifact file")
        hasher = hashlib.sha256()
        total = 0
        with os.fdopen(os.dup(fd), "rb") as stream:
            while True:
                chunk = stream.read(min(65536, MAX_FILE_BYTES + 1 - total))
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_FILE_BYTES:
                    raise ValueError("output file too large")
                hasher.update(chunk)
        if info.st_size != total:
            raise ValueError("artifact changed during verification")
        return hasher.hexdigest(), total
    finally:
        os.close(fd)


def _scan_files(root):
    paths = []
    dirs_seen = 0
    def failed(_):
        raise ValueError("unreadable artifact directory")
    for base, directories, files in os.walk(root, topdown=True, followlinks=False, onerror=failed):
        base_path = Path(base)
        relative = base_path.relative_to(root)
        if len(relative.parts) > MAX_DEPTH:
            raise ValueError("artifact nesting too deep")
        dirs_seen += 1
        if dirs_seen > MAX_DIRS:
            raise ValueError("too many artifact directories")
        for directory in directories:
            _valid_path((relative / directory).as_posix())
            if (base_path / directory).is_symlink():
                raise ValueError("artifact symlinked directory forbidden")
        for file in files:
            name = (relative / file).as_posix()
            _valid_path(name)
            if not stat.S_ISREG((base_path / file).lstat().st_mode):
                raise ValueError("nonregular artifact output")
            paths.append(name)
            if len(paths) > MAX_FILES:
                raise ValueError("too many artifact outputs")
    return sorted(paths)


def verify_bundle(request, report, manifest, artifact_root):
    """Verify declared bytes on disk. Always requires independent human review."""
    assessment = runtime_contract.assess(request, report)
    if assessment["status"] != "completed":
        raise ValueError("only completed runtime results may present an artifact bundle")
    entries = _verify_manifest_shape(manifest, assessment["task_id"])
    manifest_sha = hashlib.sha256(_canonical(manifest)).hexdigest()
    if manifest_sha != report["artifact_sha256"]:
        raise ValueError("runtime report does not match artifact manifest digest")
    root = _root(artifact_root)
    actual = _scan_files(root)
    if actual != list(entries):
        raise ValueError("artifact file list differs from manifest")
    verified_bytes = 0
    for name, (expected_sha, expected_size) in entries.items():
        actual_sha, size = _hash_regular_file(root / name)
        if actual_sha != expected_sha or size != expected_size:
            raise ValueError("artifact content differs from manifest")
        verified_bytes += size
    return {
        **assessment,
        "artifact_verified": True,
        "files_verified": len(entries),
        "total_verified_bytes": verified_bytes,
        "acceptance_tests_verified": False,
        "independent_security_review_passed": False,
        "cryptographically_signed": False,
        "release_approved": False,
    }
