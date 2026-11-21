"""Read-only operator CLI to verify CODEN synthetic artifact evidence offline.

Never executes candidate code, creates manifests, calls providers, approves
releases or mutates the artifact root. JSON input and errors are not echoed.
"""

import argparse
import json
import os
from pathlib import Path
import stat
import sys

from .artifact_evidence import verify_bundle

MAX_JSON_BYTES = 64 * 1024


def _unique_pairs(pairs):
    output = {}
    for key, value in pairs:
        if key in output:
            raise ValueError("duplicate JSON field")
        output[key] = value
    return output


def _read_json(path):
    file = Path(path)
    if file.is_symlink() or file.parent.is_symlink():
        raise ValueError("unsafe input path")
    fd = os.open(file, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_JSON_BYTES:
            raise ValueError("invalid input file")
        with os.fdopen(os.dup(fd), "rb") as stream:
            raw = stream.read(MAX_JSON_BYTES + 1)
        if len(raw) > MAX_JSON_BYTES:
            raise ValueError("oversized JSON input")
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON number")))
        if not isinstance(data, dict):
            raise ValueError("expected JSON mapping")
        return data
    finally:
        os.close(fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        request = _read_json(args.request)
        report = _read_json(args.report)
        manifest = _read_json(args.manifest)
        result = verify_bundle(request, report, manifest, args.root)
    except (OSError, ValueError, TypeError, OverflowError, RecursionError):
        print("Artifact verification blocked: evidence invalid or unavailable", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
