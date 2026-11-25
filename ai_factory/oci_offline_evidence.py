"""Offline OCI byte evidence. Never fetches, extracts, imports or executes an image.

Use only in a separately approved, immutable inspection store. A successful
receipt is not a merged filesystem inventory, signature, license or admission.
"""
import argparse
from contextlib import contextmanager
import gzip
from email.parser import BytesHeaderParser
import hashlib
import io
import json
import os
from pathlib import PurePosixPath
import re
import stat
import struct
import tarfile
import zlib

PINNED_MANIFEST = "sha256:9a36355fa2baacaae1c6dd5a1a80492bba89d1dec5a536af572ba5fb3e96e22f"
MANIFEST_TYPE = "application/vnd.oci.image.manifest.v1+json"
CONFIG_TYPE = "application/vnd.oci.image.config.v1+json"
LAYER_TYPE = "application/vnd.oci.image.layer.v1.tar+gzip"
CHUNK = 1024 * 1024
MAX_METADATA = 2 * CHUNK
MAX_MEMBERS = 200000
MAX_MARKERS = 4096
PINNED_BINARY_PATH = "usr/local/bin/openhands-agent-server"
PINNED_BINARY_SIZE = 186275024
PINNED_BINARY_SHA256 = "e1c78a2ad4eccb34c14253eb3a13d15b6ab8c74588c8df9f308eeb579651b002"
MAX_PYZ_BYTES = 128 * CHUNK
MAX_EMBEDDED_ENTRIES = 50000


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
        # GzipFile.read() can prefetch decompressed output (e.g. 8192 bytes
        # for a one-byte request). read1() requests only the remaining bytes
        # from its underlying decompressor. Accumulate short reads without
        # exceeding the requested amount or the caller's overflow sentinel.
        wanted = min(size, self.limit - self.count + 1)
        chunks = bytearray()
        while len(chunks) < wanted:
            remaining = wanted - len(chunks)
            data = self.stream.read1(remaining)
            _require(len(data) <= remaining, "gzip read exceeded requested bound")
            if not data:
                break
            self.count += len(data)
            _require(self.count <= self.limit, "expanded byte budget exceeded")
            self.digest.update(data)
            chunks.extend(data)
        return bytes(chunks)


def _safe_path(name):
    _require(isinstance(name, str) and 0 < len(name) <= 4096 and
             not name.startswith("/") and "\\" not in name and
             not any(ord(c) < 32 or ord(c) == 127 for c in name),
             "unsafe archive member path")
    path = PurePosixPath(name)
    _require(".." not in path.parts, "unsafe archive member path")
    return path



def inspect_carchive_toc(stream, *, max_declared_expanded_bytes):
    """Review-only PyInstaller Linux ELF CArchive table, not a general extractor.

    This deliberately accepts a narrow layout (EOF cookie and contiguous TOC).
    No archive data decompression, marshal deserialization, filesystem writes,
    module imports, or following of link targets. A TOC declaration is not an
    actual decompressed size or proof of component completeness. Caller must
    independently verify the exact binary hash and actual aggregate read budget.
    """
    _require(type(max_declared_expanded_bytes) is int and max_declared_expanded_bytes > 0,
             "explicit positive nested declaration budget required")
    cookie = struct.Struct("!8sIIII64s")
    header = struct.Struct("!IIIIBc")
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    _require(cookie.size + 4 < size <= 512 * CHUNK, "unsupported executable size")
    stream.seek(0)
    _require(stream.read(4) == b"\x7fELF", "expected ELF")
    stream.seek(size-cookie.size)
    raw = stream.read(cookie.size)
    _require(len(raw) == cookie.size, "truncated archive cookie")
    magic, length, offset, toc_size, pyvers, library = cookie.unpack(raw)
    _require(magic == b"MEI\x0c\x0b\x0a\x0b\x0e", "expected EOF CArchive cookie")
    _require(cookie.size < length <= size-4 and offset+toc_size+cookie.size == length,
             "inconsistent archive bounds")
    _require(0 < toc_size <= 8*CHUNK, "archive TOC budget exceeded")
    lib = library.rstrip(b"\0")
    _require(pyvers == 313 and re.fullmatch(rb"libpython3\.13\.so(?:\.[0-9]+)*",lib),
             "unexpected archive Python library")
    start = size-length
    stream.seek(start+offset)
    toc = stream.read(toc_size)
    _require(len(toc) == toc_size, "truncated archive TOC")
    rows, options, spans, seen = [], [], [], set()
    pos = declared = 0
    while pos < len(toc):
        _require(len(rows)+len(options) < 50000, "archive entry budget exceeded")
        _require(len(toc)-pos >= header.size, "truncated archive TOC entry")
        n, begin, stored, expanded, compressed, kind = header.unpack_from(toc,pos)
        _require(header.size < n <= 8192 and n%16 == 0 and pos+n <= len(toc),
                 "invalid archive TOC entry size")
        namebytes = toc[pos+header.size:pos+n]
        name, sep, padding = namebytes.partition(b"\0")
        _require(bool(name) and bool(sep) and not any(padding) and len(name)<=4096,
                 "invalid archive entry name padding")
        try:
            name = name.decode("utf-8")
        except UnicodeError as exc:
            raise ValueError("invalid archive entry name encoding") from exc
        _require(not any(ord(c)<32 or ord(c)==127 for c in name), "invalid archive entry name")
        _require(kind in (b"b",b"z",b"Z",b"M",b"m",b"s",b"x",b"o",b"l",b"n"),
                 "unsupported archive entry type; independent review required")
        _require(compressed in (0,1) and begin+stored <= offset,
                 "invalid archive member range or compression flag")
        _require(compressed or stored == expanded, "inconsistent uncompressed member size")
        if kind == b"o":
            _require(stored == expanded == 0 and compressed == 0, "invalid runtime option")
            options.append(name)
        else:
            normalized = str(_safe_path(name))
            _require(normalized != "." and normalized not in seen, "ambiguous archive member path")
            seen.add(normalized)
            if stored:
                spans.append((begin,begin+stored))
            declared += expanded
            _require(declared <= max_declared_expanded_bytes, "nested declaration budget exceeded")
            rows.append({"name":name,"type":kind.decode("ascii"),"offset":begin,
                         "stored_bytes":stored,"declared_expanded_bytes":expanded,
                         "compressed":bool(compressed)})
        pos += n
    spans.sort()
    _require(all(a[1]<=b[0] for a,b in zip(spans,spans[1:])), "overlapping archive member ranges")
    return {"status":"carchive_toc_candidate_review_required","entries":rows,
            "payload_bytes":offset,
            "runtime_option_count":len(options),"python_version":pyvers,
            "archive_bytes":length,"toc_bytes":toc_size,
            "metadata_bytes_read":4+cookie.size+toc_size,
            "declared_expanded_bytes":declared,"nested_payload_bytes_decompressed":0,
            "pyz_toc_read":False,"symlink_targets_reviewed":False,
            "embedded_inventory_verified":False,"execution_authorized":False,
            "release_authorized":False}



class _InspectionBudget:
    """Count every nested stream read and every decompressed output byte."""
    def __init__(self, limit):
        _require(type(limit) is int and limit > 0, "explicit nested read budget required")
        self.limit = limit
        self.used = 0
        self.decompressed = 0
        self.entries = 0

    def take(self, n, *, output=False):
        _require(0 <= n <= self.limit-self.used, "aggregate nested read budget exceeded")
        self.used += n
        if output:
            self.decompressed += n

    def count_entries(self, n):
        self.entries += n
        _require(self.entries <= MAX_EMBEDDED_ENTRIES, "aggregate embedded entry budget exceeded")


class _BudgetStream:
    def __init__(self, stream, budget):
        self.stream, self.budget = stream, budget

    def seek(self, *args):
        return self.stream.seek(*args)

    def tell(self):
        return self.stream.tell()

    def read(self, n):
        _require(type(n) is int and 0 <= n <= 8*CHUNK, "nested stream read exceeds bound")
        self.budget.take(n)
        raw = self.stream.read(n)
        _require(len(raw) == n, "truncated nested archive")
        return raw


class _PYZMetadata:
    """Narrow data grammar for the v6.22.3 writer's list of (name,(type,offset,size)).
    Reject arbitrary types, code, cycles and container references. Never invoke marshal.
    """
    def __init__(self, raw):
        self.raw, self.pos, self.refs, self.nodes = raw, 0, [], 0

    def take(self, n):
        _require(0 <= n <= len(self.raw)-self.pos, "truncated PYZ metadata")
        part = self.raw[self.pos:self.pos+n]
        self.pos += n
        return part

    def integer(self):
        return struct.unpack("<i", self.take(4))[0]

    def read(self, depth=0):
        self.nodes += 1
        _require(depth <= 3 and self.nodes <= 6*MAX_EMBEDDED_ENTRIES+1,
                 "PYZ metadata complexity exceeded")
        tag = self.take(1)[0]
        flagged, tag = bool(tag & 128), chr(tag & 127)
        slot = None
        if flagged:
            _require(tag != "r", "invalid PYZ reference flags")
            slot = len(self.refs)
            self.refs.append(None)
        if tag == "r":
            idx = self.integer()
            _require(0 <= idx < len(self.refs) and type(self.refs[idx]) in (int,str),
                     "unsafe PYZ reference")
            return self.refs[idx]
        if tag == "i":
            val = self.integer()
        elif tag in ("z","Z","a","A","u","t"):
            n = self.take(1)[0] if tag in ("z","Z") else self.integer()
            _require(0 < n <= 4096, "PYZ name length exceeded")
            try:
                val = self.take(n).decode("ascii" if tag in ("z","Z","a","A") else "utf-8")
            except UnicodeError as exc:
                raise ValueError("invalid PYZ name encoding") from exc
        elif tag == "[":
            n = self.integer()
            _require(depth == 0 and 0 < n <= MAX_EMBEDDED_ENTRIES, "invalid PYZ root list")
            val = [self.read(depth+1) for _ in range(n)]
        elif tag in ("(",")"):
            n = self.take(1)[0] if tag == ")" else self.integer()
            _require((depth,n) in ((1,2),(2,3)), "unexpected PYZ tuple shape")
            val = tuple(self.read(depth+1) for _ in range(n))
        else:
            raise ValueError("unsupported PYZ metadata type")
        # Container references are deliberately not resolved.
        if slot is not None and type(val) in (int,str):
            self.refs[slot] = val
        return val


def _hash_member(stream, offset, stored, compressed, budget, *, expected=None, capture_limit=0):
    """Stream raw or zlib bytes; never materialize code objects or execute payloads."""
    stream.seek(offset)
    decoder = zlib.decompressobj() if compressed else None
    h, size, prefix = hashlib.sha256(), 0, b""
    captured = bytearray() if capture_limit else None

    def consume(data):
        nonlocal size,prefix
        size += len(data)
        _require(expected is None or size <= expected, "embedded member exceeds declared size")
        h.update(data)
        prefix = (prefix+data[:512])[:512]
        if captured is not None:
            _require(size <= capture_limit, "embedded capture exceeds memory bound")
            captured.extend(data)

    left = stored
    try:
        while left:
            data = stream.read(min(CHUNK,left))
            left -= len(data)
            if decoder is None:
                consume(data)
                continue
            while data:
                limit = min(CHUNK,budget.limit-budget.used)
                if expected is not None:
                    limit = min(limit,expected-size+1)
                _require(limit>0, "aggregate decompression budget exhausted")
                out = decoder.decompress(data,limit)
                budget.take(len(out),output=True)
                consume(out)
                _require(not decoder.unused_data, "trailing compressed member data")
                tail = decoder.unconsumed_tail
                _require(len(tail)<len(data) or bool(out), "stalled embedded decompressor")
                data = tail
            _require(not decoder.eof or left==0, "trailing compressed member bytes")
        if decoder is not None:
            _require(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail,
                     "incomplete compressed embedded member")
    except zlib.error as exc:
        raise ValueError("invalid compressed embedded member") from exc
    _require(expected is None or size==expected, "embedded member size mismatch")
    return {"sha256":h.hexdigest(),"actual_bytes":size,"prefix":prefix},captured


def _inspect_pyz(stream, budget):
    source = _BudgetStream(stream,budget)
    source.seek(0,os.SEEK_END)
    size=source.tell()
    _require(17<size<=MAX_PYZ_BYTES, "unsupported PYZ size")
    source.seek(0)
    header=source.read(17)
    _require(header[:8]==b"PYZ\0\xf3\x0d\x0d\x0a" and header[12:]==b"\0"*5,
             "unexpected PYZ header or Python bytecode version")
    toc_offset=struct.unpack("!i",header[8:12])[0]
    _require(17<=toc_offset<size and size-toc_offset<=8*CHUNK, "invalid PYZ TOC bounds")
    source.seek(toc_offset)
    raw=source.read(size-toc_offset)
    reader=_PYZMetadata(raw)
    toc=reader.read()
    _require(type(toc) is list and reader.pos==len(raw), "invalid or trailing PYZ metadata")
    budget.count_entries(len(toc))
    rows,spans,seen=[],[],set()
    for row in toc:
        _require(type(row) is tuple and len(row)==2 and type(row[0]) is str and
                 type(row[1]) is tuple and len(row[1])==3, "invalid PYZ entry")
        name,(kind,offset,stored)=row
        _require(all(part.isidentifier() for part in name.split(".")) and name not in seen,
                 "unsafe or duplicate PYZ module name")
        seen.add(name)
        _require(all(type(v) is int for v in (kind,offset,stored)) and kind in (0,1,3)
                 and 17<=offset<=toc_offset and 0<=stored<=toc_offset-offset
                 and ((kind==3 and stored==0) or (kind!=3 and stored>0)), "invalid PYZ entry bounds")
        if stored:
            spans.append((offset,offset+stored))
        rows.append({"name":name,"type":kind,"offset":offset,"stored_bytes":stored})
    spans.sort()
    _require(all(a[1]<=b[0] for a,b in zip(spans,spans[1:])), "overlapping PYZ entry ranges")
    _require_contiguous(spans,17,toc_offset)
    for row in rows:
        if row["type"]==3:
            row.update(sha256=None,actual_bytes=0)
        else:
            data,_=_hash_member(source,row["offset"],row["stored_bytes"],True,budget)
            # These are hashes of opaque serialized bytes, never unmarshaled.
            data.pop("prefix")
            row.update(data)
    return {"entries":rows,"toc_sha256":hashlib.sha256(raw).hexdigest(),
            "toc_bytes":len(raw),"archive_bytes":size}


def inspect_pyz_toc(stream, *, max_read_bytes):
    budget=_InspectionBudget(max_read_bytes)
    report=_inspect_pyz(stream,budget)
    return {**report,"status":"pyz_metadata_candidate_review_required",
            "aggregate_read_bytes":budget.used,"nested_payload_bytes_decompressed":budget.decompressed,
            "embedded_inventory_verified":False,"release_authorized":False}


def _require_contiguous(spans, start, end):
    # Exact writer layout: no padding or unaccounted payload between members.
    for a,b in sorted(spans):
        _require(a==start and b>=a, "unaccounted or overlapping archive payload")
        start=b
    _require(start==end, "unaccounted archive payload")


def _embedded_paths(rows):
    paths={str(_safe_path(row["name"])):row for row in rows}
    for path,row in paths.items():
        _require(not any(str(p) in paths for p in PurePosixPath(path).parents),
                 "archive member has a non-directory ancestor")
        if row["type"]=="n":
            target=row["lexical_target"]
            # Do not follow link chains, including links in parent paths.
            # Conservative: ambiguous chains need separate review.
            _require(not any(paths.get(str(p),{}).get("type")=="n"
                             for p in (PurePosixPath(target),*PurePosixPath(target).parents)),
                     "embedded link chain or cycle requires review")


def inspect_embedded_binary(stream, *, max_read_bytes):
    budget=_InspectionBudget(max_read_bytes)
    source=_BudgetStream(stream,budget)
    outer=inspect_carchive_toc(source,max_declared_expanded_bytes=max_read_bytes)
    budget.count_entries(len(outer["entries"])+outer["runtime_option_count"])
    _require_contiguous([(r["offset"],r["offset"]+r["stored_bytes"]) for r in outer["entries"] if r["stored_bytes"]],0,outer["payload_bytes"])
    source.seek(0,os.SEEK_END)
    start=source.tell()-outer["archive_bytes"]
    pyz,unknown=[],[]
    for row in outer["entries"]:
        kind=row["type"]
        capture=MAX_PYZ_BYTES if kind=="z" else 4096 if kind=="n" else 0
        data,raw=_hash_member(source,start+row["offset"],row["stored_bytes"],row["compressed"],
                              budget,expected=row["declared_expanded_bytes"],capture_limit=capture)
        prefix=data.pop("prefix")
        row.update(data)
        row["content_kind"]="elf" if prefix.startswith(b"\x7fELF") else "opaque_bytes"
        if kind=="z":
            row["content_kind"]="pyz"
            _require(len(pyz)==0, "multiple PYZ archives require independent review")
            pyz.append({"container_name":row["name"],"sha256":row["sha256"],
                        **_inspect_pyz(io.BytesIO(raw),budget)})
        elif kind=="n":
            try:
                _require(raw is not None and raw.endswith(b"\0") and b"\0" not in raw[:-1], "invalid embedded link terminator")
                target=bytes(raw[:-1]).decode("utf-8")
            except UnicodeError as exc:
                raise ValueError("invalid embedded link target") from exc
            _require(not target.startswith("/"), "absolute embedded link target")
            row["lexical_target"]=_link_target(row["name"],target)
            row["content_kind"]="symlink"
        elif kind=="Z" or row["name"].lower().endswith((".zip",".whl",".pyz",".tar",".gz",".bz2",".xz",".7z")) or prefix.startswith((b"PK\x03\x04",b"PK\x05\x06",b"PK\x07\x08",b"PYZ\0",b"\x1f\x8b",b"BZh",b"\xfd7zXZ\0",b"7z\xbc\xaf\x27\x1c")) or prefix[257:262]==b"ustar":
            # Do not recurse through unreviewed formats. Retain their identities only.
            unknown.append(row["name"])
            row["content_kind"]="unreviewed_archive"
        elif kind in ("m","M","s"):
            row["content_kind"]="opaque_python_payload"
    _embedded_paths(outer["entries"])
    return {**outer,"status":"embedded_archive_candidate_review_required",
            "pyz_archives":pyz,"pyz_toc_read":bool(pyz),"uninspected_nested_archives":unknown,
            "aggregate_read_bytes":budget.used,"nested_payload_bytes_decompressed":budget.decompressed,
            "unknown_archive_admission":"BLOCKED" if unknown else "NOT_ESTABLISHED",
            "content_kind_magic_is_not_full_format_validation":True,
            "symlink_targets_reviewed":True,"symlinks_followed":False,
            "embedded_inventory_verified":False,"release_authorized":False}


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


def _entry_record(archive, entry, path, *, binary_capture=None):
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
        binary = binary_capture is not None and name == PINNED_BINARY_PATH
        if binary:
            _require(entry.size == PINNED_BINARY_SIZE and not binary_capture, "unexpected pinned binary occurrence")
        raw = bytearray()
        count = 0
        with source:
            for data in iter(lambda: source.read(CHUNK), b""):
                if count == 0:
                    first = data[:4]
                h.update(data)
                count += len(data)
                if capture or binary:
                    raw.extend(data)
        _require(count == entry.size, "truncated member")
        row.update(sha256=h.hexdigest(), elf=first==b"\x7fELF")
        if binary:
            _require(row["sha256"]==PINNED_BINARY_SHA256 and row["elf"], "pinned binary hash mismatch")
            binary_capture["bytes"]=raw
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


class _StrictTarInfo(tarfile.TarInfo):
    def _proc_member(self, archive):
        # Bound metadata before tarfile can allocate its padded body or recurse.
        # These are parser safety caps, not an assertion that all OCI tar
        # variants are supported. Fail closed on sparse or excessive metadata.
        _require(self.type != tarfile.GNUTYPE_SPARSE, "sparse tar metadata unsupported")
        extended = self.type in (tarfile.XHDTYPE,tarfile.XGLTYPE,tarfile.SOLARIS_XHDTYPE,
                                 tarfile.GNUTYPE_LONGNAME,tarfile.GNUTYPE_LONGLINK)
        if not extended:
            return super()._proc_member(archive)
        depth=getattr(archive,"_coden_extended_depth",0)
        total=getattr(archive,"_coden_extended_bytes",0)+self.size
        _require(0<=self.size<=MAX_METADATA and total<=16*CHUNK and depth<8,
                 "extended tar metadata bound exceeded")
        archive._coden_extended_depth=depth+1
        archive._coden_extended_bytes=total
        try:
            return super()._proc_member(archive)
        finally:
            archive._coden_extended_depth=depth

    @classmethod
    def fromtarfile(cls, archive):
        # Catch at the member boundary: newer 3.12 security updates use private
        # _frombuf internally, bypassing a public frombuf override.
        # Only a genuine all-zero header may terminate a layer.
        try:
            return super().fromtarfile(archive)
        except tarfile.EOFHeaderError:
            raise
        except tarfile.HeaderError as exc:
            raise ValueError("invalid or truncated tar header") from exc


def _scan_layer(store, desc, expected_diff, remaining, member_budget, *, inventory=None, layer=0, binary_capture=None):
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
            with tarfile.open(fileobj=reader, mode="r|", bufsize=512, tarinfo=_StrictTarInfo) as archive:
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
                            changes.append(_entry_record(archive, entry, path, binary_capture=binary_capture))
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
                # Validate the consumed first zero header and the mandatory
                # second zero block through the tar stream (not its underlying
                # reader, which could skip buffered bytes).
                _require(archive.fileobj.tell() == archive.offset + tarfile.BLOCKSIZE,
                         "tar did not terminate at a zero header")
                _require(archive.fileobj.read(tarfile.BLOCKSIZE) == b"\0"*tarfile.BLOCKSIZE,
                         "missing second tar end block")
                while True:
                    data = archive.fileobj.read(CHUNK)
                    if not data:
                        break
                    _require(not any(data), "nonzero data after tar end")
            # Hash covers the complete stream, including its validated end padding.
            _require(reader.digest.hexdigest() == _hex(expected_diff), "diff ID mismatch")
            if inventory is not None:
                _apply_inventory(inventory, changes, whiteouts, layer)
            return {"digest": digest, "diff_id": expected_diff, "compressed_bytes": size,
                    "expanded_bytes": reader.count, "members": members, "whiteouts": whiteouts,
                    "link_count": links, "special_count": special, "setid_count": setid,
                    "candidate_paths": markers}


def verify(root, manifest_digest, *, max_expanded_bytes, max_compressed_bytes, logical_inventory=False, embedded_inventory=False):
    """Return review-only evidence from local blobs; fail closed on malformed inputs."""
    _require(type(max_expanded_bytes) is int and max_expanded_bytes > 0,
             "explicit positive inspection budget required")
    _require(type(max_compressed_bytes) is int and max_compressed_bytes > 0,
             "explicit positive compressed budget required")
    _require(type(logical_inventory) is bool and type(embedded_inventory) is bool, "explicit inventory mode required")
    _require(not embedded_inventory or (manifest_digest==PINNED_MANIFEST and logical_inventory),
             "pinned manifest and logical inventory required for embedded review")
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
            binary_capture = {} if embedded_inventory else None
            for layer, (desc, diff) in enumerate(zip(descs, diffs), 1):
                row = _scan_layer(store, desc, diff, max_expanded_bytes - expanded,
                                  MAX_MEMBERS - members, inventory=inventory, layer=layer,
                                  binary_capture=binary_capture)
                expanded += row["expanded_bytes"]
                members += row["members"]
                unique[row["digest"]] = row["compressed_bytes"]
                layers.append(row)
            embedded = {}
            if embedded_inventory:
                binary=inventory.get(PINNED_BINARY_PATH,{})
                _require(binary.get("kind")=="regular" and binary.get("layer")==13 and
                         binary.get("sha256")==PINNED_BINARY_SHA256 and binary.get("size")==PINNED_BINARY_SIZE
                         and "bytes" in binary_capture, "final pinned binary not verified")
                report=inspect_embedded_binary(io.BytesIO(binary_capture.pop("bytes")),max_read_bytes=max_expanded_bytes-expanded)
                embedded={"embedded_archive_review":{**report,"path":PINNED_BINARY_PATH,"binary_sha256":PINNED_BINARY_SHA256,"layer":13},
                          "aggregate_expanded_and_nested_read_bytes":expanded+report["aggregate_read_bytes"]}
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
                    **embedded,
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
    parser.add_argument("--embedded-inventory", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(args.oci_store, PINNED_MANIFEST,
                        max_expanded_bytes=args.max_expanded_bytes,
                        max_compressed_bytes=args.max_compressed_bytes,
                        logical_inventory=args.logical_inventory, embedded_inventory=args.embedded_inventory)
    except ValueError:
        parser.exit(1, "Offline review rejected; no admission granted.\n")
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
