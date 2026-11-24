"""Static, review-only license evidence; never install or execute a wheel."""
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
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


def inspect_wheel(raw, digest):
    if len(raw) > CAP or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('wheel size or digest mismatch')
    evidence = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries = z.infolist()
        if len(entries) > 50000 or sum(e.file_size for e in entries) > 4 * CAP:
            raise ValueError('wheel expansion limit')
        seen = set()
        for e in entries:
            p = PurePosixPath(e.filename)
            if (p.is_absolute() or '..' in p.parts or '\\' in e.filename
                    or ':' in e.filename or e.filename in seen
                    or stat.S_ISLNK(e.external_attr >> 16) or e.flag_bits & 1):
                raise ValueError('unsafe wheel member')
            seen.add(e.filename)
            if e.is_dir():
                continue
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
