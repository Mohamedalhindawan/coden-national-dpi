"""Static inventory of a hash-pinned Python archive; never extract or execute it."""
import base64
import hashlib
import io
import tarfile
from pathlib import PurePosixPath

CAP = 128 * 1024 * 1024


def inventory(raw, expected_sha):
    if len(raw) > CAP or hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError('archive digest or size mismatch')
    seen = set()
    expanded = files = text_bytes = 0
    native, texts, links = [], [], []
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        for m in archive:
            p = PurePosixPath(m.name)
            if (not p.parts or p.parts[0] != 'python' or '..' in p.parts or
                    '\\' in m.name or ':' in m.name or str(p) != m.name or
                    m.name in seen or len(seen) >= 100000):
                raise ValueError('unsafe or excessive archive members')
            seen.add(m.name)
            if m.issym() or m.islnk():
                links.append({'path': m.name, 'target': m.linkname, 'kind': 'symlink' if m.issym() else 'hardlink'})
                continue
            if m.isdir():
                continue
            if not m.isfile() or not 0 <= m.size <= CAP:
                raise ValueError('unsupported member or size')
            files += 1
            expanded += m.size
            if expanded > 1024 * 1024 * 1024:
                raise ValueError('expanded size limit')
            name = p.name.lower()
            text = ('license' in name or 'licence' in name or 'notice' in name or
                    name.startswith(('copying', 'copyright')) or name in ('vendor.txt', 'metadata', 'python.json'))
            with archive.extractfile(m) as stream:
                prefix = stream.read(8)
                kind = ('ELF' if prefix.startswith(b'\x7fELF') else
                        'archive' if prefix == b'!<arch>\n' else
                        'PE_candidate' if prefix.startswith(b'MZ') else None)
                if not text and not kind:
                    continue
                if text and (m.size > 2 * 1024 * 1024 or text_bytes + m.size > 16 * 1024 * 1024):
                    raise ValueError('text evidence limit')
                data = prefix + stream.read()
            record = {'path': m.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
            if len(data) != m.size:
                raise ValueError('member size mismatch')
            if kind:
                native.append(dict(record, kind=kind))
            if text:
                text_bytes += len(data)
                texts.append(dict(record, base64=base64.b64encode(data).decode('ascii')))
    return {'archive_sha256': expected_sha, 'member_count': len(seen), 'regular_files': files,
            'expanded_regular_bytes': expanded, 'native': native, 'text_evidence': texts, 'links': links,
            'extracted': False, 'executed': False, 'license_approved': False,
            'compiled_membership_verified': False, 'release_authorized': False}
