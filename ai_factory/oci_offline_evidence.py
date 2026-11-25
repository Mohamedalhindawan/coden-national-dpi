"""Offline OCI byte evidence. Never fetches, extracts, imports or executes an image.

Use only in a separately approved, immutable inspection store. A successful
receipt is not a merged filesystem inventory, signature, license or admission.
"""
import argparse
from contextlib import contextmanager
import gzip
from email.parser import BytesHeaderParser
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


def _json_blob(store, digest, size=None, *, budget):
    with _blob(store, digest, size) as (stream, n):
        _require(n <= budget, "compressed metadata budget exceeded")
        _require(n <= MAX_METADATA, "metadata exceeds bound")
        raw = stream.read(MAX_METADATA + 1)
        _require(hashlib.sha256(raw).hexdigest() == _hex(digest), "metadata digest mismatch")
        obj = json.loads(raw, object_pairs_hook=_unique_pairs, parse_constant=_no_constant)
        _require(isinstance(obj, dict), "invalid metadata")
        return obj, n


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


def _link_target(path, value):
    # Absolute symlinks refer to the image root, never the host root.
    _require(isinstance(value, str) and 0 < len(value) <= 4096 and
             "\\" not in value and not any(ord(ch) < 32 or ord(ch) == 127 for ch in value),
             "unsafe link target")
    parts = [] if value.startswith("/") else list(PurePosixPath(path).parent.parts)
    for part in PurePosixPath(value).parts:
        if part in ("/", "."):
            continue
        if part == "..":
            _require(bool(parts), "link target leaves image root")
            parts.pop()
        else:
            parts.append(part)
    return "/".join(parts) or "."


def _metadata_kind(name):
    path = PurePosixPath(name)
    if str(path) == "var/lib/dpkg/status":
        return "deb"
    if path.name == "METADATA" and path.parent.name.endswith(".dist-info"):
        return "pypi"
    return None


def _package_metadata(path, raw):
    if path == "var/lib/dpkg/status":
        rows = []
        for block in raw.decode("utf-8").split("\n\n"):
            fields = {}
            for line in block.splitlines():
                if line and not line[0].isspace() and ":" in line:
                    key, val = line.split(":", 1)
                    if key in ("Package", "Version", "Status", "Architecture", "Source"):
                        _require(key not in fields, "duplicate dpkg metadata field")
                        fields[key] = val.strip()
            if fields.get("Status") == "install ok installed":
                _require(all(fields.get(k) for k in ("Package", "Version", "Architecture")),
                         "incomplete installed dpkg record")
                rows.append({"ecosystem":"deb", "name":fields["Package"], "version":fields["Version"],
                             "architecture":fields["Architecture"], "source":fields.get("Source")})
        return rows
    headers = BytesHeaderParser().parsebytes(raw)
    for key in ("Name", "Version", "License-Expression"):
        _require(len(headers.get_all(key, [])) <= 1, "ambiguous Python metadata")
    _require(bool(headers.get("Name")) and bool(headers.get("Version")), "incomplete Python metadata")
    return [{"ecosystem":"pypi", "name":headers["Name"], "version":headers["Version"],
             "declared_license_expression":headers.get("License-Expression")}]


def _entry_record(archive, entry, path):
    name = str(path)
    row = {"path":name,"mode":entry.mode,"uid":entry.uid,"gid":entry.gid,
           "size":entry.size, "xattr_names":sorted(k for k in entry.pax_headers if
                                                  k.startswith(("SCHILY.xattr.","LIBARCHIVE.xattr.")))}
    if entry.isdir():
        row["kind"] = "directory"
    elif entry.issym():
        row.update(kind="symlink", target=entry.linkname,
                   lexical_target=_link_target(name, entry.linkname))
    elif entry.islnk():
        row.update(kind="hardlink", target=str(_safe_path(entry.linkname)))
    elif entry.isreg():
        row["kind"] = "regular"
        source = archive.extractfile(entry)
        _require(source is not None, "regular member has no data")
        h = hashlib.sha256()
        first = b""
        capture = _metadata_kind(name)
        if capture:
            _require(entry.size <= MAX_METADATA, "package metadata exceeds bound")
        raw = bytearray()
        count = 0
        with source:
            for data in iter(lambda: source.read(CHUNK), b""):
                if count == 0:
                    first = data[:4]
                h.update(data)
                count += len(data)
                if capture:
                    raw.extend(data)
        _require(count == entry.size, "truncated member")
        row.update(sha256=h.hexdigest(), elf=first==b"\x7fELF")
        if capture:
            row["package_metadata"] = _package_metadata(name, bytes(raw))
            row["package_metadata_kind"] = capture
    else:
        raise ValueError("unsupported filesystem member; independent unpacker review required")
    return row


def _apply_inventory(tree, changes, whiteouts, layer):
    """Conservative logical model, no host path traversal or extraction."""
    def remove(target, children_only=False):
        prefix = "" if target == "." else target + "/"
        for key in list(tree):
            if (key != target and key.startswith(prefix)) or (not children_only and key == target):
                del tree[key]

    def parents(path, create):
        for ancestor in reversed(PurePosixPath(path).parents):
            parent = str(ancestor)
            if parent == ".":
                continue
            if parent not in tree and create:
                tree[parent] = {"path":parent,"kind":"directory","layer":layer,"implicit":True}
            if parent in tree:
                _require(tree[parent]["kind"] == "directory",
                         "non-directory or symlink ancestor requires independent review")

    # OCI whiteouts apply only to lower-layer resources, regardless of tar order.
    for marker in whiteouts:
        path = PurePosixPath(marker)
        parents(marker, False)
        if path.name == ".wh..wh..opq":
            remove(str(path.parent), children_only=True)
        else:
            remove(str(path.parent / path.name[4:]))
    for row in changes:
        path = row["path"]
        parents(path, True)
        old = tree.get(path)
        if old and old["kind"] == "directory" and row["kind"] != "directory":
            remove(path)
        if row["kind"] == "hardlink":
            target = row["target"]
            parents(target, False)
            linked = tree.get(target)
            _require(target != path and linked and linked["kind"] in ("regular","hardlink"),
                     "unresolved or unsupported hardlink")
            # Retain content identity even if a later layer removes the original path.
            row = {**linked, "path":path,"kind":"hardlink","target":target}
        _require(path != "." or row["kind"] == "directory", "invalid root entry")
        tree[path] = {**row,"layer":layer}
        _require(len(tree) <= MAX_MEMBERS, "inventory entry budget exceeded")


def _inventory_report(tree):
    entries = []
    packages = []
    for path,row in sorted(tree.items()):
        entries.append({k:v for k,v in row.items() if k != "package_metadata"})
        kind = _metadata_kind(path)
        if kind and row["kind"] in ("regular", "hardlink"):
            # A hardlink inherits bytes, not the semantic role of its old path.
            # Do not silently omit a package database whose source was not parsed.
            _require(row.get("package_metadata_kind") == kind,
                     "unparsed or mismatched package metadata hardlink")
            packages.extend({**pkg,"metadata_path":path,"metadata_sha256":row["sha256"]}
                            for pkg in row["package_metadata"])
    packages.sort(key=lambda x:(x["name"],x["version"],x["metadata_path"]))
    return {"status":"logical_inventory_candidate_review_required",
            "entries":entries,"entry_count":len(entries),
            "regular_file_count":sum(x["kind"] in ("regular","hardlink") for x in entries),
            "elf_count":sum(bool(x.get("elf")) for x in entries),
            "executable_count":sum(x["kind"] in ("regular","hardlink") and bool(x.get("mode",0)&0o111) for x in entries),
            "setid_count":sum(bool(x.get("mode",0)&0o6000) for x in entries),
            "package_metadata":packages,"package_metadata_count":len(packages),
            "symlinks_followed":False,"independent_unpacker_crosscheck":False,
            "embedded_archive_inventory_verified":False,"complete_sbom":False}


def _scan_layer(store, desc, expected_diff, remaining, member_budget, *, inventory=None, layer=0):
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
            changes, seen = [], set()
            with tarfile.open(fileobj=reader, mode="r|", bufsize=512) as archive:
                for entry in archive:
                    members += 1
                    _require(members <= member_budget, "member budget exceeded")
                    path = _safe_path(entry.name)
                    _require(not entry.sparse, "sparse members require separate review")
                    if inventory is not None:
                        name = str(path)
                        _require(name not in seen, "duplicate normalized member path")
                        seen.add(name)
                        _require(not any(part.startswith(".wh.") for part in path.parts[:-1]),
                                 "whiteout ancestor is invalid")
                        if not path.name.startswith(".wh."):
                            changes.append(_entry_record(archive, entry, path))
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
            if inventory is not None:
                _apply_inventory(inventory, changes, whiteouts, layer)
            return {"digest": digest, "diff_id": expected_diff, "compressed_bytes": size,
                    "expanded_bytes": reader.count, "members": members, "whiteouts": whiteouts,
                    "link_count": links, "special_count": special, "setid_count": setid,
                    "candidate_paths": markers}


def verify(root, manifest_digest, *, max_expanded_bytes, max_compressed_bytes, logical_inventory=False):
    """Return review-only evidence from local blobs; fail closed on malformed inputs."""
    _require(type(max_expanded_bytes) is int and max_expanded_bytes > 0,
             "explicit positive inspection budget required")
    _require(type(max_compressed_bytes) is int and max_compressed_bytes > 0,
             "explicit positive compressed budget required")
    _require(type(logical_inventory) is bool, "explicit inventory mode required")
    try:
        with _store(root) as store:
            manifest, manifest_bytes = _json_blob(store, manifest_digest, budget=max_compressed_bytes)
            _require(manifest["schemaVersion"] == 2 and manifest["mediaType"] == MANIFEST_TYPE,
                     "invalid image manifest")
            config_desc = manifest["config"]
            _require(config_desc["mediaType"] == CONFIG_TYPE, "invalid config media type")
            config, config_bytes = _json_blob(store, config_desc["digest"], config_desc["size"],
                                              budget=max_compressed_bytes - manifest_bytes)
            _require(config["os"] == "linux" and config["architecture"] == "amd64",
                     "unexpected image platform")
            rootfs = config["rootfs"]
            descs, diffs = manifest["layers"], rootfs["diff_ids"]
            _require(rootfs["type"] == "layers" and isinstance(descs, list) and
                     isinstance(diffs, list) and 0 < len(descs) == len(diffs) <= 128,
                     "layer count mismatch")
            # Count distinct immutable objects before reading any layer payload.
            payloads = {manifest_digest: manifest_bytes}
            config_digest = config_desc["digest"]
            _require(config_digest not in payloads, "descriptor role collision")
            payloads[config_digest] = config_bytes
            unique = {}
            for desc, diff in zip(descs, diffs):
                digest, size = desc["digest"], desc["size"]
                _hex(digest)
                _hex(diff)
                _require(desc["mediaType"] == LAYER_TYPE and type(size) is int and size > 0,
                         "invalid layer descriptor")
                _require(digest not in payloads or digest in unique,
                         "descriptor role collision")
                _require(digest not in unique or unique[digest] == (size, diff),
                         "inconsistent repeated descriptor")
                unique[digest] = (size, diff)
                payloads[digest] = size
            required_bytes = sum(payloads.values())
            _require(required_bytes <= max_compressed_bytes, "compressed payload budget exceeded")
            # Confirm required file sizes without reading compressed layer contents.
            for digest, (size, _) in unique.items():
                with _blob(store, digest, size):
                    pass
            layers = []
            expanded = members = 0
            unique = {}
            inventory = {} if logical_inventory else None
            for layer, (desc, diff) in enumerate(zip(descs, diffs), 1):
                row = _scan_layer(store, desc, diff, max_expanded_bytes - expanded,
                                  MAX_MEMBERS - members, inventory=inventory, layer=layer)
                expanded += row["expanded_bytes"]
                members += row["members"]
                unique[row["digest"]] = row["compressed_bytes"]
                layers.append(row)
            return {"status": "layer_bytes_verified_review_only", "manifest_digest": manifest_digest,
                    "config_digest": config_desc["digest"], "layer_count": len(layers),
                    "unique_layer_count": len(unique), "unique_compressed_bytes": sum(unique.values()),
                    "logical_compressed_bytes": sum(x["compressed_bytes"] for x in layers),
                    "required_unique_payload_bytes": required_bytes,
                    "max_compressed_bytes": max_compressed_bytes,
                    "store_quota_verified": False,
                    "expanded_bytes": expanded, "layers": layers,
                    "whiteout_semantics_applied": logical_inventory, "final_inventory_verified": False,
                    **({"logical_inventory": _inventory_report(inventory)} if logical_inventory else {}),
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
    parser.add_argument("--max-compressed-bytes", required=True, type=int)
    parser.add_argument("--logical-inventory", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(args.oci_store, PINNED_MANIFEST,
                        max_expanded_bytes=args.max_expanded_bytes,
                        max_compressed_bytes=args.max_compressed_bytes,
                        logical_inventory=args.logical_inventory)
    except ValueError:
        parser.exit(1, "Offline review rejected; no admission granted.\n")
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
