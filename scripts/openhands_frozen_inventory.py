"""Inspect selected data records using the upstream PyInstaller archive reader."""
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import re
import subprocess

from PyInstaller.archive.readers import CArchiveReader


def glibc_versions(path):
    output = subprocess.check_output(["readelf", "--version-info", path], text=True)
    return set(re.findall(r"\bGLIBC_[0-9]+(?:\.[0-9]+)+\b", output))


def main():
    binary = Path("server.bin")
    reader = CArchiveReader(str(binary))
    packages = []
    embedded = []
    for name, entry in reader.toc.items():
        if name.endswith(".dist-info/METADATA"):
            if entry[2] > 8 * 1024 * 1024:
                raise ValueError("oversized package metadata")
            raw = reader.extract(name)
            message = BytesParser().parsebytes(raw, headersonly=True)
            packages.append(dict(name=message["Name"], version=message["Version"],
                                 license_expression=message["License-Expression"],
                                 metadata_sha256=hashlib.sha256(raw).hexdigest()))
        if re.fullmatch(r"(?:.*/)?libpython3\.\d+\.so\.1\.0", name):
            embedded.append(name)
    if len(embedded) != 1:
        raise ValueError(f"unexpected libpython records: {embedded}")
    Path("libpython.bin").write_bytes(reader.extract(embedded[0]))
    available = glibc_versions("candidate-libc.bin")
    required = glibc_versions(binary) | glibc_versions("libpython.bin")
    if not required or not available:
        raise ValueError("missing GNU symbol-version evidence")
    result = dict(packages=packages, archive_entries=len(reader.toc),
                  server_sha256=hashlib.file_digest(binary.open("rb"), "sha256").hexdigest(),
                  libpython=embedded[0], missing_glibc_versions=sorted(required - available),
                  live_execution_authorized=False)
    Path("frozen.json").write_text(json.dumps(result, indent=2) + "\n")
    official = {p["name"].lower().replace("_", "-"): p["version"] for p in packages}
    for name in ("openhands-agent-server", "openhands-sdk", "openhands-workspace", "openhands-tools"):
        if official.get(name) != "1.63.1":
            raise ValueError(f"expected frozen distribution missing: {name}")


if __name__ == "__main__":
    main()
