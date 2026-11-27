"""Reproduce the review-only R2 payload contract from exact retained source bytes."""
import hashlib
import io
import json
import tarfile
import unicodedata

ARCHIVE_SHA256 = 'e44613f882ec5e306723e156417966e2c63f3d06d019897d722bcd4a068a03d6'
EXPECTED_SHA256 = '18969fca5913ace8706d9eb549493dd42d29707e36c5bbba66f4a21ead9e648a'
ARCHIVE_FILES = 2297
PAYLOAD_FILES = 613
ROOTS = {'openhands-sdk': 'sdk', 'openhands-tools': 'tools',
         'openhands-workspace': 'workspace', 'openhands-agent-server': 'agent_server'}


def _required(root, path):
    if path.endswith(('.py', '/py.typed')):
        return True
    if root == 'openhands-sdk':
        return path.endswith('.j2') or '/schemas/' in path and path.endswith('.json')
    if root == 'openhands-tools':
        return (path.endswith('.j2') or '/preset/subagents/' in path and path.endswith('.md')
                or '/browser_use/js/' in path and path.endswith('.js'))
    if root == 'openhands-agent-server':
        return (path.endswith('/code_server_proxy.cjs') or path.endswith('/docker/Dockerfile')
                or '/vscode_extensions/' in path and path.endswith(('.json', '.js')))
    return False


def _derive(raw):
    if (type(raw) is not bytes or len(raw) > 8 * 1024**2
            or hashlib.sha256(raw).hexdigest() != ARCHIVE_SHA256):
        raise ValueError('source archive digest mismatch')
    roots = {name: {} for name in ROOTS}
    seen = set()
    total = 0
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as tar:
        for member in tar:
            name = member.name
            parts = name.split('/')
            if (not member.isfile() or not name.startswith('source/')
                    or len(parts) < 2 or any(p in ('', '.', '..', '.git') for p in parts)
                    or '\\' in name or not name.isascii() and unicodedata.normalize('NFC', name) != name
                    or any(ord(c) < 32 or ord(c) == 127 for c in name)
                    or name.casefold() in seen or not 0 <= member.size <= 16 * 1024**2):
                raise ValueError('unsafe or duplicate source archive member')
            seen.add(name.casefold())
            total += member.size
            if len(seen) > ARCHIVE_FILES or total > 64 * 1024**2:
                raise ValueError('source archive bound exceeded')
            root = parts[1]
            if root not in ROOTS or len(parts) < 4 or parts[2:4] != ['openhands', ROOTS[root]]:
                continue
            path = '/'.join(parts[2:])
            if len(parts) < 5:
                raise ValueError('package path is not a file subtree')
            with tar.extractfile(member) as stream:
                body = stream.read(member.size + 1)
            if len(body) != member.size:
                raise ValueError('source member length mismatch')
            roots[root][path] = {'sha256': hashlib.sha256(body).hexdigest(),
                                 'bytes': len(body), 'required': _required(root, path)}
    if len(seen) != ARCHIVE_FILES or sum(map(len, roots.values())) != PAYLOAD_FILES or not all(roots.values()):
        raise ValueError('source inventory count mismatch')
    return {'status': 'ROOT_SOURCE_PAYLOAD_EXPECTATIONS_REVIEW_ONLY',
            'r2_tree': '5a974f15a38a6f972c5cc021b45980f14a0fdbc3',
            'proposed_tree': '02271a017d25ff4c3f3dc31adaf772fde176c46f',
            'roots': roots, 'build_authorized': False, 'installation_authorized': False,
            'release_authorized': False, 'source_code_executed': False}


def reproduce_inventory(raw):
    """Return exact original contract bytes; no extraction, execution or admission."""
    result = (json.dumps(_derive(raw), indent=2, sort_keys=True) + '\n').encode()
    if hashlib.sha256(result).hexdigest() != EXPECTED_SHA256:
        raise ValueError('derived inventory digest mismatch')
    return result
