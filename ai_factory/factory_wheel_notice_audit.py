"""Static, review-only license evidence; never install or execute a wheel."""
import base64
import csv
from email.parser import BytesHeaderParser
import hashlib
import io
import json
import re
from pathlib import Path, PurePosixPath
import stat
import struct
import tempfile
import unicodedata
import zlib
import tomllib
from urllib.parse import urlsplit
from urllib.request import build_opener, HTTPRedirectHandler
import zipfile

CAP = 64 * 1024 * 1024
LOCK_SHA = '6d8348da6768ae32bb7665bdc7ca2525d53e576e13729fcc41f0a28df7c25b69'
TARGETS = {
    'agent-client-protocol': ('1.0.0', {'179c14266997841438ee15245a2668d31b2c695c13bff87d01c36e016185ddd0'}),
    'browser-use-sdk': ('2.0.15', {'5d8ba3836070c67a9774baac556b233e22f266823d3dee34295d98869bec7752'}),
    'jsonref': ('1.1.0', {'590dc7773df6c21cbf948b5dac07a72a251db28b0238ceecce0a2abfa8ec30a9'}),
    'lmnr-claude-code-proxy': ('0.1.23', {'0fd8e1bfeef82802c8a74533a6d27e7c7912c7db68358ca67976f1635311503f'}),
    'protobuf': ('6.33.5', {'cbf16ba3350fb7b889fca858fb215967792dc125b35c7976ca4818bee3521cf0', '69915a973dd0f60f31a08b8318b73eab2bd6a392c79184b3612226b0a3f8ec02'}),
}


def select_candidates(lock, targets):
    result = []
    for name, (version, hashes) in targets.items():
        found = set()
        for pkg in lock['package']:
            if (pkg['name'], pkg['version']) != (name, version):
                continue
            for entry in pkg.get('wheels', []):
                digest = entry['hash'].removeprefix('sha256:')
                if digest not in hashes:
                    continue
                url = urlsplit(entry['url'])
                if (url.scheme != 'https' or url.netloc != 'files.pythonhosted.org'
                        or not url.path.endswith('.whl') or url.query or url.fragment
                        or digest in found):
                    raise ValueError('unexpected wheel URL or duplicate')
                found.add(digest)
                result.append((name, version, digest, entry['url']))
        if found != hashes:
            raise ValueError('missing locked candidate')
    return result


def _validate_namespace(entries):
    # Validate the complete namespace before decompressing any notice.
    # ZipInfo.filename can truncate at NUL; compare the original spelling.
    seen = {}
    for e in entries:
        spelling = e.filename[:-1] if e.is_dir() else e.filename
        p = PurePosixPath(spelling)
        if (not spelling or e.orig_filename != e.filename
                or p.is_absolute() or '..' in p.parts
                or any(part in ('', '.', '..') for part in spelling.split('/'))
                or any(ord(c) < 32 or ord(c) == 127 for c in spelling)
                or '\\' in spelling or ':' in spelling or p in seen
                or stat.S_ISLNK(e.external_attr >> 16) or e.flag_bits & 1):
            raise ValueError('unsafe wheel member')
        seen[p] = e.is_dir()
    for p in seen:
        if any(parent in seen and not seen[parent] for parent in p.parents):
            raise ValueError('wheel file ancestor collision')


def _inspect_legacy_notices(raw, digest):
    """Historical notice inventory only; not a RECORD or shared-budget admission."""
    if len(raw) > CAP or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('wheel size or digest mismatch')
    evidence = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries = z.infolist()
        if len(entries) > 50000 or sum(e.file_size for e in entries) > 4 * CAP:
            raise ValueError('wheel expansion limit')
        _validate_namespace(entries)
        for e in entries:
            if e.is_dir():
                continue
            p = PurePosixPath(e.filename)
            name = p.name.upper()
            if (name == 'METADATA' or name.startswith(('LICENSE', 'LICENCE', 'NOTICE', 'COPYING', 'COPYRIGHT'))
                    or 'licenses' in p.parts):
                if e.file_size > 2 * 1024 * 1024:
                    raise ValueError('notice size limit')
                data = z.read(e)
                evidence[e.filename] = {'sha256': hashlib.sha256(data).hexdigest(), 'base64': base64.b64encode(data).decode('ascii')}
    if not any(p.endswith('.dist-info/METADATA') for p in evidence):
        raise ValueError('missing distribution metadata')
    return evidence


CHUNK = 64 * 1024
MAX_RECORD = 2 * 1024 * 1024
MAX_METADATA = 2 * 1024 * 1024


def _distribution_identity(raw, prefix):
    """Conservative identity check, not a full Core Metadata validator.

    Unusual version spellings require review rather than implicit equivalence.
    No package code, external parser dependency or installation is involved.
    """
    metadata = BytesHeaderParser().parsebytes(raw)
    names = metadata.get_all("Name", [])
    versions = metadata.get_all("Version", [])
    if metadata.defects or len(names) != 1 or len(versions) != 1:
        raise ValueError("missing or ambiguous wheel metadata identity")
    name, version = names[0], versions[0]
    if (not isinstance(name, str) or not isinstance(version, str)
            or len(name) > 200 or len(version) > 128
            or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?", name)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.!+_]*", version)):
        raise ValueError("unsupported wheel metadata identity")
    directory = prefix.removesuffix(".dist-info/")
    directory_name, separator, directory_version = directory.rpartition("-")
    normalize = lambda value: re.sub(r"[-_.]+", "-", value).lower()
    canonical_name = normalize(name)
    if (not separator or normalize(directory_name) != canonical_name
            or directory_version != version):
        raise ValueError("wheel METADATA and dist-info identity mismatch")
    return {"name": canonical_name, "version": version}


class WheelBudget:
    """Single-use-on-failure accounting for a serial, trusted batch caller.

    Compressed bytes count each admitted archive once; expanded bytes count
    all emitted member bytes, including RECORD and permitted signature files.
    Limits are deliberately no larger than the proposed three-wheel scope.
    This is not an OS quota or a network acquisition authorization.
    """
    __slots__ = ("_compressed_limit", "_expanded_limit", "_io_limit", "_compressed", "_expanded", "_archive_read", "_native_reserved", "_evidence_limit", "_evidence", "_failed")

    def __init__(self, compressed_limit=8 * 1024**2, expanded_limit=128 * 1024**2, io_limit=128 * 1024**2, evidence_limit=16 * 1024**2):
        if (type(compressed_limit) is not int or type(expanded_limit) is not int
                or not 0 < compressed_limit <= 8 * 1024**2
                or not 0 < expanded_limit <= 128 * 1024**2
                or type(io_limit) is not int or not 0 < io_limit <= 128 * 1024**2
                or type(evidence_limit) is not int or not 0 < evidence_limit <= 16 * 1024**2):
            raise ValueError("invalid wheel budget")
        self._compressed_limit = compressed_limit
        self._expanded_limit = expanded_limit
        self._io_limit = io_limit
        self._evidence_limit = evidence_limit
        self._evidence = 0
        self._compressed = self._expanded = self._archive_read = self._native_reserved = 0
        self._failed = False

    @property
    def compressed_bytes(self):
        return self._compressed

    @property
    def expanded_bytes(self):
        return self._expanded

    @property
    def failed(self):
        return self._failed

    @property
    def remaining(self):
        return min(self._expanded_limit - self._expanded, self.io_remaining)

    @property
    def archive_read_bytes(self):
        return self._archive_read

    @property
    def native_input_reserved_bytes(self):
        return self._native_reserved

    @property
    def logical_io_bytes(self):
        return self._archive_read + self._expanded + self._native_reserved

    @property
    def io_remaining(self):
        return self._io_limit - self.logical_io_bytes

    def _require_io(self, count):
        if self.failed or count < 0 or count > self.io_remaining:
            self._failed = True
            raise ValueError("shared logical I/O budget exhausted or failed")

    def _read(self, count):
        self._require_io(count)
        self._archive_read += count

    def _reserve_native(self, count):
        self._require_io(count)
        self._native_reserved += count

    @property
    def evidence_bytes(self):
        return self._evidence

    def _retain_evidence(self, name, row):
        # Bound serialized member receipts, not the entire Python heap.
        # A single row is already bounded by pathname and native output limits.
        count = len(json.dumps({name: row}, ensure_ascii=True, separators=(",", ":")).encode("ascii"))
        if self.failed or count > self._evidence_limit-self._evidence:
            self._failed = True
            raise ValueError("aggregate wheel evidence limit exhausted")
        self._evidence += count

    def _admit(self, count):
        if self.failed or count > self._compressed_limit - self._compressed:
            self._failed = True
            raise ValueError("compressed wheel budget exhausted or failed")
        self._compressed += count

    def _charge(self, count):
        if self.failed or count > self.remaining:
            self._failed = True
            raise ValueError("expanded wheel budget exhausted or failed")
        self._expanded += count


class _MeteredArchive:
    """Meter logical reads of an immutable in-memory archive, including rereads.

    No claim about physical device reads, zlib internals, or external tools.
    All archive access in the strict path goes through this object.
    """
    def __init__(self, raw, budget):
        self._stream = io.BytesIO(raw)
        self._size = len(raw)
        self._budget = budget

    def tell(self):
        return self._stream.tell()

    def seek(self, offset, whence=0):
        return self._stream.seek(offset, whence)

    def seekable(self):
        return True

    def read(self, size=-1):
        available = max(0, self._size - self.tell())
        requested = available if size < 0 else size
        self._budget._require_io(requested)
        count = min(requested, available)
        self._budget._read(count)
        return self._stream.read(count)

    def at(self, offset, size):
        if offset < 0 or size < 0 or offset+size > self._size:
            raise ValueError("archive read outside bounds")
        self.seek(offset)
        raw = self.read(size)
        if len(raw) != size:
            raise ValueError("short archive read")
        return raw


def _classic_eocd(reader, size):
    """Narrow review profile; reject split/ZIP64/comment/trailing layouts."""
    if size < 22:
        raise ValueError("short ZIP end record")
    magic,disk,central_disk,disk_count,total_count,central_size,central_offset,comment = struct.unpack(
        "<4s4H2IH",reader.at(size-22,22))
    if (magic != b"PK\x05\x06" or disk or central_disk or comment
            or disk_count != total_count or not 0 < total_count <= 50000
            or central_offset + central_size != size-22
            or central_offset == 0xffffffff or central_size == 0xffffffff):
        raise ValueError("unsupported ZIP end record")
    return total_count,central_offset


def _check_extra(extra):
    offset = 0
    while offset < len(extra):
        if len(extra)-offset < 4:
            raise ValueError("truncated ZIP extra field")
        kind,size = struct.unpack_from("<HH",extra,offset)
        offset += 4
        if size > len(extra)-offset or kind in (0x0001,0x7075):
            raise ValueError("unsupported ZIP64 or Unicode-path extra field")
        offset += size


def _strict_ranges(reader, z, entries):
    """Resolve bounded local records without extracting any file.

    Conservative profile: stored/deflate, ordinary local sizes, no data
    descriptor, no ambiguous padding or overlapping ranges. Other valid
    ZIP variants require review, not a fallback to the legacy reader.
    """
    ranges = {}
    end = 0
    for e in sorted(entries, key=lambda item: item.header_offset):
        offset = e.header_offset
        if offset != end or offset + 30 > z.start_dir:
            raise ValueError("noncontiguous or overlapping local records")
        (magic, _, flags, method, _, _, crc, compressed, expanded,
         nlen, xlen) = struct.unpack("<4s5H3I2H", reader.at(offset, 30))
        if (magic != b"PK\x03\x04" or flags != e.flag_bits
                or flags & ~0x806 or method not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                or method != e.compress_type
                or (crc, compressed, expanded) != (e.CRC, e.compress_size, e.file_size)):
            raise ValueError("unsupported or inconsistent local wheel header")
        begin = offset + 30 + nlen + xlen
        end = begin + compressed
        if begin > z.start_dir or end > z.start_dir:
            raise ValueError("wheel local record bounds")
        name = reader.at(offset + 30, nlen).decode("utf-8" if flags & 0x800 else "cp437")
        _check_extra(reader.at(offset+30+nlen,xlen))
        _check_extra(e.extra)
        if name != e.orig_filename:
            raise ValueError("wheel local name mismatch")
        ranges[e.filename] = (begin, end)
    if end != z.start_dir:
        raise ValueError("unaccounted local ZIP bytes")
    return ranges


def _member_blocks(reader, e, span, budget):
    """Bound actual emitted bytes, even for a forged central directory.

    A one-byte overflow probe is never retained or accepted as evidence.
    No unbounded flush, no ZipExtFile read-ahead/truncation.
    """
    count = crc = 0
    decoder = zlib.decompressobj(-15) if e.compress_type == zipfile.ZIP_DEFLATED else None
    begin, end = span
    def account(block):
        nonlocal count, crc
        budget._charge(len(block))
        count += len(block)
        if count > e.file_size:
            raise ValueError("actual wheel member size exceeds declaration")
        crc = zlib.crc32(block, crc)
        return block

    for offset in range(begin, end, CHUNK):
        count_to_read = min(CHUNK, end-offset)
        if decoder is None:
            if count_to_read > budget.remaining or count_to_read > e.file_size-count:
                budget._failed = True
                raise ValueError("stored member expansion budget or size")
            budget._require_io(2*count_to_read)
        pending = reader.at(offset,count_to_read)
        if decoder is None:
            yield account(pending)
            continue
        if decoder.eof:
            raise ValueError("trailing compressed member bytes")
        while pending:
            limit = min(CHUNK, budget.remaining + 1, e.file_size - count + 1)
            block = decoder.decompress(pending, limit)
            tail = decoder.unconsumed_tail
            if decoder.unused_data or (not block and tail == pending):
                raise ValueError("invalid compressed member boundary")
            if block:
                yield account(block)
            pending = tail
    if decoder is not None and not decoder.eof:
        # Drain bounded output from decoder state, never use flush().
        while not decoder.eof:
            block = decoder.decompress(b"", min(CHUNK, budget.remaining + 1, e.file_size - count + 1))
            if not block and not decoder.eof:
                raise ValueError("incomplete deflate member")
            if block:
                yield account(block)
    if count != e.file_size or crc != e.CRC:
        raise ValueError("wheel member size or CRC mismatch")


def _inspect_record(raw, digest, budget, *, native_session=None):
    budget._admit(len(raw))
    reader = _MeteredArchive(raw,budget)
    read_before = budget.archive_read_bytes
    io_before = budget.logical_io_bytes
    native_before = budget.native_input_reserved_bytes
    evidence_before = budget.evidence_bytes
    hasher = hashlib.sha256()
    for offset in range(0,len(raw),CHUNK):
        hasher.update(reader.at(offset,min(CHUNK,len(raw)-offset)))
    if hasher.hexdigest() != digest:
        raise ValueError("wheel digest mismatch")
    before = budget.expanded_bytes
    expected_count,expected_central = _classic_eocd(reader,len(raw))
    with zipfile.ZipFile(reader) as z:
        entries = z.infolist()
        if (len(entries) != expected_count or z.start_dir != expected_central
                or sum(e.file_size for e in entries) > budget.remaining):
            raise ValueError("wheel member count or declared expansion budget")
        # Bound depth before constructing path ancestors.
        for e in entries:
            name = e.filename.rstrip("/")
            if e.volume != 0 or len(name.encode("utf-8")) > 4096 or len(name.split("/")) > 64:
                raise ValueError("unsupported member disk or path extent")
        _validate_namespace(entries)
        aliases = {}
        for e in entries:
            name = e.filename.rstrip("/")
            if (len(name.encode("utf-8")) > 4096 or len(name.split("/")) > 64
                    or unicodedata.normalize("NFC", name) != name
                    or any(unicodedata.category(c).startswith("C") for c in name)):
                raise ValueError("noncanonical Unicode wheel path")
            mode = stat.S_IFMT(e.external_attr >> 16)
            if mode not in (0, stat.S_IFDIR if e.is_dir() else stat.S_IFREG):
                raise ValueError("unsupported wheel member type")
            if e.is_dir() and e.file_size != 0:
                raise ValueError("nonempty directory entry")
            for p in (PurePosixPath(name), *PurePosixPath(name).parents):
                spelling = str(p)
                key = unicodedata.normalize("NFC", spelling.casefold())
                if aliases.setdefault(key, spelling) != spelling:
                    raise ValueError("Unicode or casefold wheel path collision")
        spans = _strict_ranges(reader, z, entries)
        files = {e.filename: e for e in entries if not e.is_dir()}
        roots = {p.split("/")[0] for p in files if p.split("/")[0].endswith(".dist-info")}
        if len(roots) != 1:
            raise ValueError("expected one top-level dist-info directory")
        prefix = next(iter(roots)) + "/"
        record = prefix + "RECORD"
        if any(prefix + suffix not in files for suffix in ("METADATA", "WHEEL", "RECORD")):
            raise ValueError("missing wheel distribution metadata or RECORD")
        if files[record].file_size > MAX_RECORD:
            raise ValueError("RECORD size limit")
        record_bytes = b"".join(_member_blocks(reader, files[record], spans[record], budget))
        signatures = {record + ".jws", record + ".p7s"}
        rows = {}
        for row in csv.reader(io.StringIO(record_bytes.decode("utf-8"), newline=""), strict=True):
            if len(row) != 3 or row[0] in rows or row[0] not in files or row[0] in signatures:
                raise ValueError("unexpected or duplicate RECORD row")
            name, digest_field, size = row
            if name == record:
                if digest_field or size:
                    raise ValueError("RECORD self row must be empty")
                rows[name] = (None, None)
                continue
            algo, sep, encoded = digest_field.partition("=")
            if (not sep or algo not in ("sha256", "sha384", "sha512")
                    or not encoded or size != str(files[name].file_size)):
                raise ValueError("invalid RECORD hash algorithm or size")
            rows[name] = (algo, encoded)
        if set(rows) != set(files) - signatures:
            raise ValueError("RECORD member coverage mismatch")
        metadata_path = prefix + "METADATA"
        if files[metadata_path].file_size > MAX_METADATA:
            raise ValueError("METADATA size limit")
        metadata_bytes = b"".join(_member_blocks(reader, files[metadata_path],
                                               spans[metadata_path], budget))
        algo, expected = rows[metadata_path]
        actual = base64.urlsafe_b64encode(hashlib.new(algo, metadata_bytes).digest()).decode("ascii").rstrip("=")
        if actual != expected:
            raise ValueError("METADATA RECORD hash mismatch")
        distribution = _distribution_identity(metadata_bytes, prefix)
        receipt = {}
        for e in entries:
            name = e.filename
            algo, encoded = rows.get(name, (None, None))
            sha = hashlib.sha256()
            verifier = hashlib.new(algo) if algo and algo != "sha256" else sha
            first = b""
            if name == record:
                blocks = (record_bytes,)
            elif name == metadata_path:
                blocks = (metadata_bytes,)
            else:
                blocks = _member_blocks(reader, e, spans[name], budget)
            native_file = None
            native = None
            try:
                for block in blocks:
                    sha.update(block)
                    if verifier is not sha:
                        verifier.update(block)
                    if native_file is not None:
                        native_file.write(block)
                    elif len(first) < 8:
                        take = min(8-len(first), len(block))
                        first += block[:take]
                        if (native_session is not None and first.startswith(b"\x7fELF")
                                and not e.is_dir()):
                            native_file = native_session.open(e.file_size)
                            native_file.write(first)
                            native_file.write(block[take:])
                if algo and base64.urlsafe_b64encode(verifier.digest()).decode("ascii").rstrip("=") != encoded:
                    raise ValueError("RECORD content hash mismatch")
                if native_file is not None:
                    native_file.close()
                    budget._reserve_native(4*e.file_size)
                    native = native_session.inspect()
            finally:
                if native_file is not None:
                    native_file.close()
                    native_session.remove()
            if not e.is_dir():
                row = {"sha256": sha.hexdigest(), "bytes": e.file_size,
                       "record_hash_verified": algo is not None,
                       "elf_magic": first.startswith(b"\x7fELF")}
                if native is not None:
                    row["native"] = native
                budget._retain_evidence(name,row)
                receipt[name] = row
    return {"record_verified": True, "wheel_sha256": digest,
            "distribution": distribution, "compressed_bytes": len(raw),
            "expanded_bytes": budget.expanded_bytes - before, "files": receipt,
            "archive_read_bytes": budget.archive_read_bytes-read_before,
            "logical_io_bytes": budget.logical_io_bytes-io_before,
            "native_input_reserved_bytes": budget.native_input_reserved_bytes-native_before,
            "native_internal_io_verified": False,
            "evidence_bytes": budget.evidence_bytes-evidence_before,
            "legacy_signature_files": sorted(signatures & set(files)),
            "legacy_signatures_verified": False, "release_authorized": False}


def inspect_wheel(raw, digest, *, budget=None):
    """Use explicit shared budget for strict RECORD evidence; never install.

    No-budget callers retain the historical notice-only interface. Those
    receipts cannot satisfy the new R2 admission gate.
    """
    if budget is None:
        return _inspect_legacy_notices(raw, digest)
    if type(budget) is not WheelBudget or type(raw) is not bytes:
        raise ValueError("strict wheel audit requires bytes and WheelBudget")
    try:
        return _inspect_record(raw, digest, budget)
    except BaseException as exc:
        budget._failed = True
        if isinstance(exc, (zipfile.BadZipFile, zlib.error, csv.Error, UnicodeError, struct.error)):
            raise ValueError("malformed wheel structure") from exc
        raise



class _NativeSession:
    """One private temporary ELF at a time, never an archive-provided path."""
    def __init__(self, directory):
        self.path = Path(directory) / "object"
        self.count = self.output_bytes = 0

    def open(self, size):
        if not 0 < size <= 32 * 1024**2 or self.count >= 64:
            raise ValueError("native member limits")
        return self.path.open("xb")

    def inspect(self):
        from ai_factory.factory_python_elf import inspect_elf_file
        result = inspect_elf_file(self.path)
        # Per-command output is independently bounded by the ELF inspector.
        encoded = len(json.dumps(result, ensure_ascii=False).encode("utf-8"))
        if encoded > 16 * 1024**2 - self.output_bytes:
            raise ValueError("aggregate native evidence limit")
        self.output_bytes += encoded
        self.count += 1
        return result

    def remove(self):
        self.path.unlink()


def inspect_wheel_batch(candidates, *, scratch, inspect_native=False, fixture_native=False):
    """Strict three-wheel batch; bytes supplied by caller, no network access.

    An unsuccessful inspection or cleanup raises without returning a receipt.
    Caller must establish the independent OS sandbox and admission first.
    """
    if not isinstance(candidates, (list, tuple)) or len(candidates) != 3:
        raise ValueError("exactly three wheel inputs required")
    if inspect_native and fixture_native is not True:
        raise ValueError("native inspection blocked: internal reads unverified; fixture scope only")
    budget = WheelBudget()
    receipts = []
    try:
        with tempfile.TemporaryDirectory(prefix="wheel-audit-", dir=scratch) as directory:
            session = _NativeSession(directory) if inspect_native else None
            seen = set()
            for raw, digest in candidates:
                if type(raw) is not bytes or digest in seen:
                    raise ValueError("invalid or duplicate batch candidate")
                seen.add(digest)
                receipts.append(_inspect_record(raw, digest, budget, native_session=session))
            native_count = session.count if session else 0
            native_output_bytes = session.output_bytes if session else 0
    except BaseException as exc:
        budget._failed = True
        if isinstance(exc, (zipfile.BadZipFile, zlib.error, csv.Error, UnicodeError, struct.error)):
            raise ValueError("malformed wheel structure") from exc
        raise
    return {"wheels": receipts, "compressed_bytes": budget.compressed_bytes,
            "expanded_bytes": budget.expanded_bytes, "native_count": native_count,
            "archive_read_bytes": budget.archive_read_bytes,
            "logical_io_bytes": budget.logical_io_bytes,
            "native_input_reserved_bytes": budget.native_input_reserved_bytes,
            "native_internal_io_verified": False, "fixture_native": bool(inspect_native),
            "evidence_bytes": budget.evidence_bytes,
            "native_output_bytes": native_output_bytes, "legacy_signatures_verified": False,
            "record_verified": True, "release_authorized": False}


# Retained Sprint 21/25 identities, not a new acquisition or admission.
# The historical inventory is incomplete for license/provenance purposes.
_R2_HISTORICAL_WHEELS = (
    ("jiter", "0.16.0", "c682bea068a90b764577bdb78a60a4c1d1606daf9cd4c893832a37c7cc9d9026",
     {"jiter/jiter.cpython-313-x86_64-linux-gnu.so":
      (832152, "bbc712e9a00a2b01cfa40286d129cb43f019692d7bf94069f58ab1de6094d29e")}),
    ("tokenizers", "0.23.2", "41c2f84d172449b4dadb9cdc508e3e364076613c35b16e76ecfe47a60d1e3305",
     {"tokenizers/tokenizers.abi3.so":
      (11317624, "7c4ddf7ad4251a646d324151b4d698da59531fdd892ea3abd24a6f323fcb1d6b")}),
    ("fastmcp-slim", "4.2.0", "174239bed3ac47275afa7fe82941a65f86ad0314205195766c92b138c6dcfebe", {}),
)


# Retained artifact 14981902769 (native inventory), 14953700367 (upgraded
# source/wheel evidence), 14952151177 (fastmcp-slim metadata).
# Exact per-archive counts and four member hashes are historical comparisons,
# not independent provenance or a complete member inventory.
_R2_HISTORICAL_COUNTS = {
    "jiter": (343320, 885473, 9),
    "tokenizers": (3386843, 11701061, 32),
    "fastmcp-slim": (994236, 3507586, 288),
}
_R2_HISTORICAL_MEMBERS = {
    "jiter": {
        "jiter-0.16.0.dist-info/METADATA": (5212, "b1bcf7374eb4f4195f890ab610b6de54ae8766456df7ddf757f95d255097ef2e"),
        "jiter-0.16.0.dist-info/licenses/LICENSE": (1091, "7c7134b9f7b978c03fca875517cf398db91f19bbb8109b6685e742aa3f57468e"),
    },
    "tokenizers": {
        "tokenizers-0.23.2.dist-info/METADATA": (9830, "d2d200c0d0c48895b2c3b02cdd8c06c26dea8f9be38ef193e9b4dd5a566c89be"),
    },
    "fastmcp-slim": {
        "fastmcp_slim-4.2.0.dist-info/METADATA": (11160, "df6b0719b4582d41663c1ef35cdc7f655dc809d16f144a4cea0589e7bc8ba3c1"),
    },
}


def compare_r2_historical_receipt(receipt):
    """Compare selected fields of a static receipt against retained evidence.

    No file, network, subprocess, or import operations. Input is data, not
    authenticated proof; a match never proves the scanner actually ran,
    verifies every historical member, or authorizes any subsequent action.
    """
    def require(condition):
        if not condition:
            raise ValueError("R2 historical receipt mismatch")

    def count(value):
        return type(value) is int and value >= 0

    require(type(receipt) is dict)
    require(receipt.get("record_verified") is True)
    for key in ("fixture_native", "native_internal_io_verified",
                "release_authorized", "legacy_signatures_verified"):
        require(receipt.get(key) is False)
    for key in ("native_count", "native_output_bytes", "native_input_reserved_bytes"):
        require(type(receipt.get(key)) is int and receipt[key] == 0)
    require(type(receipt.get("compressed_bytes")) is int and receipt["compressed_bytes"] == 4724399)
    require(type(receipt.get("expanded_bytes")) is int and receipt["expanded_bytes"] == 16094120)
    wheels = receipt.get("wheels")
    require(type(wheels) is list and len(wheels) == 3)
    expected = {name: (version, digest, native) for name, version, digest, native in _R2_HISTORICAL_WHEELS}
    seen = set()
    compressed = expanded = members = 0
    for wheel in wheels:
        require(type(wheel) is dict and wheel.get("record_verified") is True)
        for key in ("native_internal_io_verified", "release_authorized", "legacy_signatures_verified"):
            require(wheel.get(key) is False)
        dist = wheel.get("distribution")
        require(type(dist) is dict and set(dist) == {"name", "version"})
        name = dist["name"]
        require(type(name) is str and name in expected and name not in seen)
        version, digest, native = expected[name]
        require(dist["version"] == version and wheel.get("wheel_sha256") == digest)
        seen.add(name)
        c, e = wheel.get("compressed_bytes"), wheel.get("expanded_bytes")
        require(count(c) and c > 0 and count(e))
        compressed += c
        expanded += e
        require(compressed <= 4724399 and expanded <= 16094120)
        files = wheel.get("files")
        require(type(files) is dict and 0 < len(files) <= 329 - members)
        require((c, e, len(files)) == _R2_HISTORICAL_COUNTS[name])
        members += len(files)
        file_bytes = 0
        actual_native = {}
        for path, row in files.items():
            require(type(path) is str and type(row) is dict)
            size, sha = row.get("bytes"), row.get("sha256")
            require(count(size) and type(sha) is str and re.fullmatch(r"[0-9a-f]{64}", sha) is not None)
            require(type(row.get("elf_magic")) is bool and type(row.get("record_hash_verified")) is bool)
            require("native" not in row)
            file_bytes += size
            require(file_bytes <= e)
            if row["elf_magic"]:
                require(row["record_hash_verified"] is True)
                actual_native[path] = (size, sha)
        require(file_bytes == e and actual_native == native)
        for path, (size, sha) in _R2_HISTORICAL_MEMBERS[name].items():
            row = files.get(path)
            require(type(row) is dict and row["bytes"] == size and row["sha256"] == sha
                    and row["record_hash_verified"] is True and row["elf_magic"] is False)
    require(seen == set(expected) and compressed == 4724399 and expanded == 16094120 and members == 329)
    return {"status": "HISTORICAL_RECEIPT_MATCH_UNAPPROVED", "matched_wheels": 3,
            "regular_files": members, "receipt_origin_verified": False,
            "complete_historical_member_match_verified": False,
            "license_approved": False, "security_approved": False,
            "installation_authorized": False, "import_authorized": False,
            "release_authorized": False}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('redirect denied')


def main():
    archive = Path('docs/evidence/openhands-077f3fad/fixed-source-provenance.zip')
    with zipfile.ZipFile(archive) as z:
        raw = z.read('resolved.lock')
    if hashlib.sha256(raw).hexdigest() != LOCK_SHA:
        raise ValueError('lock digest mismatch')
    results = []
    output = Path('wheel-review.json')
    for name, version, digest, url in select_candidates(tomllib.loads(raw.decode()), TARGETS):
        with build_opener(NoRedirect()).open(url, timeout=30) as response:
            wheel = response.read(CAP + 1)
        evidence = inspect_wheel(wheel, digest)
        results.append(dict(name=name, version=version, wheel_sha256=digest, source=url, evidence=evidence))
    output.write_text(json.dumps(dict(status='awaiting_human_review', selected_installed_wheels_verified=False, license_admission_approved=False, release_authorized=False, candidates=results), indent=2) + '\n')
    print(f'Collected {len(results)} hash-verified candidate wheel evidence records; review required.')


if __name__ == '__main__':
    main()
