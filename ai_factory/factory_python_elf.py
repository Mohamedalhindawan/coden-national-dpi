"""Static ELF evidence from an already digest-verified archive and inventory."""
import hashlib
import io
import re
import os
import selectors
import signal
import time
import subprocess
import tarfile
import tempfile
from pathlib import Path


def _bounded_command(argv, *, stdout_limit, stderr_limit, timeout):
    """Read both pipes concurrently with bounded buffers and a total deadline.

    On error/cancellation kill the new process group and reap its leader.
    The surrounding admission sandbox must still enforce cgroup-wide limits.
    """
    if (not 0 < stdout_limit <= 8 * 1024**2
            or not 0 < stderr_limit <= 64 * 1024
            or not 0 < timeout <= 30):
        raise ValueError("invalid ELF command limits")
    deadline = time.monotonic() + timeout
    proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            start_new_session=True, close_fds=True,
                            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
    try:
        buffers = {proc.stdout: bytearray(), proc.stderr: bytearray()}
        limits = {proc.stdout: stdout_limit, proc.stderr: stderr_limit}
        with selectors.DefaultSelector() as selector:
            for pipe in buffers:
                selector.register(pipe, selectors.EVENT_READ)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ValueError("ELF inspection timeout")
                events = selector.select(remaining)
                if not events:
                    raise ValueError("ELF inspection timeout")
                for key, _ in events:
                    pipe = key.fileobj
                    buffer = buffers[pipe]
                    # At most one sentinel byte past the permitted output.
                    block = os.read(pipe.fileno(), min(65536, limits[pipe] - len(buffer) + 1))
                    if not block:
                        selector.unregister(pipe)
                        continue
                    if len(block) > limits[pipe] - len(buffer):
                        raise ValueError("ELF inspection output limit")
                    buffer.extend(block)
        try:
            rc = proc.wait(timeout=max(0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired as exc:
            raise ValueError("ELF inspection timeout") from exc
        if rc or buffers[proc.stderr]:
            raise ValueError("ELF inspection failed or emitted diagnostics")
        return buffers[proc.stdout].decode("utf-8", errors="strict")
    except BaseException:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired as exc:
            raise ValueError("ELF inspection cleanup failed") from exc
        raise
    finally:
        proc.stdout.close()
        proc.stderr.close()


def inspect_elf_file(path):
    """Collect bounded readelf metadata without loading the candidate."""
    def readelf(*flags, limit=512 * 1024):
        return _bounded_command(['/usr/bin/readelf', '-W', *flags, str(Path(path).absolute())],
                                stdout_limit=limit, stderr_limit=64 * 1024, timeout=30)

    out = readelf('-h', '-d')
    return dict(machine=re.findall(r'^\s*Machine:\s*(.+)$', out, re.M),
                needed=re.findall(r'\(NEEDED\).*\[([^\]]+)\]', out),
                soname=re.findall(r'\(SONAME\).*\[([^\]]+)\]', out),
                search_paths=re.findall(r'\((?:RPATH|RUNPATH)\).*\[([^\]]+)\]', out),
                rpath=re.findall(r'\(RPATH\).*\[([^\]]*)\]', out),
                runpath=re.findall(r'\(RUNPATH\).*\[([^\]]*)\]', out),
                interpreter=re.findall(r'\[Requesting program interpreter: ([^\]\n]+)\]', readelf('-l')),
                version_info=readelf('-V'),
                dynamic_symbols=readelf('--dyn-syms', limit=8 * 1024 * 1024))


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
