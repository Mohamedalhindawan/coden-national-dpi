"""Static ELF evidence from an already digest-verified archive and inventory."""
import hashlib
import io
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path


def inspect_elf_file(path):
    """Collect bounded readelf metadata without loading the candidate."""
    def readelf(*flags):
        result = subprocess.run(['/usr/bin/readelf', '-W', *flags, str(path)],
                                capture_output=True, text=True, timeout=30,
                                env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'}, check=True)
        if len(result.stdout) > 512 * 1024:
            raise ValueError('ELF evidence output limit')
        return result.stdout

    out = readelf('-h', '-d')
    return dict(machine=re.findall(r'^\s*Machine:\s*(.+)$', out, re.M),
                needed=re.findall(r'\(NEEDED\).*\[([^\]]+)\]', out),
                soname=re.findall(r'\(SONAME\).*\[([^\]]+)\]', out),
                search_paths=re.findall(r'\((?:RPATH|RUNPATH)\).*\[([^\]]+)\]', out),
                version_info=readelf('-V'))


def collect_elf(raw, records):
    selected = [r for r in records if r['kind'] == 'ELF']
    expected = {r['path']: r for r in selected}
    if (len(expected) != len(selected) or len(expected) > 128 or
            len(raw) > 128 * 1024 * 1024 or
            any(not 0 < r['bytes'] <= 1024**3 for r in selected) or
            sum(r['bytes'] for r in selected) > 1024**3):
        raise ValueError('ELF inventory bounds')
    results = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r|gz') as archive:
        for entry in archive:
            if entry.name not in expected:
                continue
            r = expected[entry.name]
            if entry.name in results or not entry.isfile() or entry.size != r['bytes']:
                raise ValueError('ELF member mismatch')
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'object'
                digest = hashlib.sha256()
                count = 0
                with archive.extractfile(entry) as source, path.open('xb') as output:
                    while block := source.read(1024 * 1024):
                        count += len(block)
                        digest.update(block)
                        output.write(block)
                if count != entry.size or digest.hexdigest() != r['sha256']:
                    raise ValueError('ELF member digest mismatch')
                results[entry.name] = dict(r, **inspect_elf_file(path))
    if results.keys() != expected.keys():
        raise ValueError('missing ELF members')
    return [results[p] for p in sorted(results)]
