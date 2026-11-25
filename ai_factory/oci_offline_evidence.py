"""Offline OCI byte evidence. Never fetches, extracts, imports or executes an image.

Use only in a separately approved, immutable inspection store. A successful
receipt is not a merged filesystem inventory, signature, license or admission.
"""
import argparse
from contextlib import contextmanager
import gzip
import hashlib
import json
import os
from pathlib import PurePosixPath
import re
import stat
import tarfile

PINNED_MANIFEST = "sha256:9a36355fa2baacaae1c6dd5a1a80492bba89d1dec5a536af572ba5fb3e96e22f"
MANIFEST_TYPE = "application/vnd.oci.image.manifest.v1+json"
CONFIG_TYPE = "application/vnd.oci.image.config.v1+json"
LAYER_TYPE = "application/vnd.oci.image.layer.v1.tar+gzip"
CHUNK = 1024 * 1024
MAX_METADATA = 2 * CHUNK
MAX_MEMBERS = 200000
MAX_MARKERS = 4096


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _hex(digest):
    _require(isinstance(digest, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", digest),
             "invalid digest")
    return digest[7:]


@contextmanager
def _store(root):
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fds = []
    try:
        fds.append(os.open(root, flags))
        for name in ("blobs", "sha256"):
            fds.append(os.open(name, flags, dir_fd=fds[-1]))
        yield fds[-1]
    finally:
        for fd in reversed(fds):
            os.close(fd)


@contextmanager
def _blob(store, digest, size=None):
    fd = os.open(_hex(digest), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=store)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        _require(stat.S_ISREG(before.st_mode), "blob is not a regular file")
        if size is not None:
            _require(type(size) is int and size >= 0 and before.st_size == size,
                     "descriptor size mismatch")
        yield stream, before.st_size
        after = os.fstat(stream.fileno())
        _require((before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                 (after.st_size, after.st_mtime_ns, after.st_ctime_ns),
                 "blob changed during review")


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def _no_constant(_):
    raise ValueError("invalid JSON constant")


def _json_blob(store, digest, size=None):
    with _blob(store, digest, size) as (stream, n):
        _require(n <= MAX_METADATA, "metadata exceeds bound")
        raw = stream.read(MAX_METADATA + 1)
        _require(hashlib.sha256(raw).hexdigest() == _hex(digest), "metadata digest mismatch")
        obj = json.loads(raw, object_pairs_hook=_unique_pairs, parse_constant=_no_constant)
        _require(isinstance(obj, dict), "invalid metadata")
        return obj


class _BoundedReader:
    def __init__(self, stream, limit):
        self.stream = stream
        self.limit = limit
        self.count = 0
        self.digest = hashlib.sha256()

    def read(self, size):
        _require(0 <= size <= 8 * CHUNK, "archive read exceeds bound")
        data = self.stream.read(min(size, self.limit - self.count + 1))
        self.count += len(data)
        _require(self.count <= self.limit, "expanded byte budget exceeded")
        self.digest.update(data)
        return data


def _safe_path(name):
    _require(isinstance(name, str) and 0 < len(name) <= 4096 and
             not name.startswith("/") and "\\" not in name and
             not any(ord(c) < 32 or ord(c) == 127 for c in name),
             "unsafe archive member path")
    path = PurePosixPath(name)
    _require(".." not in path.parts, "unsafe archive member path")
    return path


def _scan_layer(store, desc, expected_diff, remaining, member_budget):
    _require(desc["mediaType"] == LAYER_TYPE, "unsupported layer media type")
    digest, size = desc["digest"], desc["size"]
    _hex(expected_diff)
    with _blob(store, digest, size) as (stream, _):
        h = hashlib.sha256()
        for chunk in iter(lambda: stream.read(CHUNK), b""):
            h.update(chunk)
        _require(h.hexdigest() == _hex(digest), "compressed blob digest mismatch")
        stream.seek(0)
        with gzip.GzipFile(fileobj=stream) as gz:
            reader = _BoundedReader(gz, remaining)
            whiteouts, markers = [], []
            members = links = special = setid = 0
            with tarfile.open(fileobj=reader, mode="r|", bufsize=512) as archive:
                for entry in archive:
                    members += 1
                    _require(members <= member_budget, "member budget exceeded")
                    path = _safe_path(entry.name)
                    _require(not entry.sparse, "sparse members require separate review")
                    if path.name.startswith(".wh."):
                        _require(entry.isreg() and entry.size == 0 and
                                 path.name[4:] not in ("", ".", ".."), "invalid whiteout")
                        whiteouts.append(str(path))
                        _require(len(whiteouts) <= MAX_MARKERS, "whiteout budget exceeded")
                    if entry.islnk():
                        _safe_path(entry.linkname)
                    if entry.issym() or entry.islnk():
                        links += 1
                    elif not (entry.isreg() or entry.isdir()):
                        special += 1
                    if entry.mode & 0o6000:
                        setid += 1
                    normalized = str(path).lower().replace("_", "-")
                    if any(x in normalized for x in (
                        "browser-use", "lmnr", "func-timeout", "tom-swe",
                        "openhands-agent-server", "var/lib/dpkg/status"
                    )):
                        markers.append(str(path))
                        _require(len(markers) <= MAX_MARKERS, "marker budget exceeded")
            # Hash the entire decompressed blob, including tar end padding.
            # Never treat the tar metadata scan as a full OCI unpacker.
            while True:
                data = reader.read(CHUNK)
                if not data:
                    break
                _require(not any(data), "nonzero data after tar end")
            _require(reader.digest.hexdigest() == _hex(expected_diff), "diff ID mismatch")
            return {"digest": digest, "diff_id": expected_diff, "compressed_bytes": size,
                    "expanded_bytes": reader.count, "members": members, "whiteouts": whiteouts,
                    "link_count": links, "special_count": special, "setid_count": setid,
                    "candidate_paths": markers}


def verify(root, manifest_digest, *, max_expanded_bytes):
    """Return review-only evidence from local blobs; fail closed on malformed inputs."""
    _require(type(max_expanded_bytes) is int and max_expanded_bytes > 0,
             "explicit positive inspection budget required")
    try:
        with _store(root) as store:
            manifest = _json_blob(store, manifest_digest)
            _require(manifest["schemaVersion"] == 2 and manifest["mediaType"] == MANIFEST_TYPE,
                     "invalid image manifest")
            config_desc = manifest["config"]
            _require(config_desc["mediaType"] == CONFIG_TYPE, "invalid config media type")
            config = _json_blob(store, config_desc["digest"], config_desc["size"])
            _require(config["os"] == "linux" and config["architecture"] == "amd64",
                     "unexpected image platform")
            rootfs = config["rootfs"]
            descs, diffs = manifest["layers"], rootfs["diff_ids"]
            _require(rootfs["type"] == "layers" and isinstance(descs, list) and
                     isinstance(diffs, list) and 0 < len(descs) == len(diffs) <= 128,
                     "layer count mismatch")
            layers = []
            expanded = members = 0
            unique = {}
            for desc, diff in zip(descs, diffs):
                row = _scan_layer(store, desc, diff, max_expanded_bytes - expanded,
                                  MAX_MEMBERS - members)
                expanded += row["expanded_bytes"]
                members += row["members"]
                unique[row["digest"]] = row["compressed_bytes"]
                layers.append(row)
            return {"status": "layer_bytes_verified_review_only", "manifest_digest": manifest_digest,
                    "config_digest": config_desc["digest"], "layer_count": len(layers),
                    "unique_layer_count": len(unique), "unique_compressed_bytes": sum(unique.values()),
                    "logical_compressed_bytes": sum(x["compressed_bytes"] for x in layers),
                    "expanded_bytes": expanded, "layers": layers,
                    "whiteout_semantics_applied": False, "final_inventory_verified": False,
                    "embedded_inventory_verified": False, "signature_verified": False,
                    "license_approved": False, "security_approved": False,
                    "execution_authorized": False, "release_authorized": False}
    except (OSError, EOFError, tarfile.TarError, KeyError, TypeError, OverflowError,
            UnicodeError, RecursionError) as exc:
        raise ValueError("offline image evidence rejected") from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("oci_store")
    parser.add_argument("--max-expanded-bytes", required=True, type=int)
    args = parser.parse_args()
    try:
        result = verify(args.oci_store, PINNED_MANIFEST,
                        max_expanded_bytes=args.max_expanded_bytes)
    except ValueError:
        parser.exit(1, "Offline review rejected; no admission granted.\n")
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
