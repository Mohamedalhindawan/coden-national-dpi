"""Locate a literal and its enclosing Python definition in tracked working files."""

import argparse
import ast
import json
from pathlib import Path
import re
import subprocess

EXTENSIONS = {".py", ".md", ".html", ".js", ".ts", ".css", ".yaml", ".yml", ".toml", ".json"}
PRIVATE_PATH = re.compile(r"(^|[./_-])(env|secrets?|credentials?|passwords?|tokens?|private[-_]?keys?)([./_-]|$)", re.I)
MAX_BYTES = 512 * 1024


def tracked_text(root):
    listing = subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=root)
    for entry in listing.split(b"\0"):
        if not entry:
            continue
        meta, raw = entry.split(b"\t", 1)
        mode, _, stage = meta.split()
        if mode not in (b"100644", b"100755") or stage != b"0":
            continue
        name = raw.decode("utf-8", errors="surrogateescape")
        path = root / name
        if path.suffix.lower() not in EXTENSIONS or PRIVATE_PATH.search(name):
            continue
        try:
            if path.resolve() != path or not path.is_file() or path.stat().st_size > MAX_BYTES:
                continue
            data = path.read_bytes()
            if b"\x00" not in data:
                yield name, data.decode("utf-8")
        except (OSError, UnicodeError, RuntimeError):
            continue


def definitions(source):
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, RecursionError):
        return []
    return sorted((n.lineno, n.end_lineno, n.name) for n in ast.walk(tree)
                  if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)))


def search(root, query, limit):
    results = []
    needle = query.casefold()
    for path, source in tracked_text(root):
        if needle not in source.casefold():
            continue
        scopes = definitions(source) if path.endswith(".py") else []
        for number, line in enumerate(source.splitlines(), start=1):
            if needle not in line.casefold():
                continue
            scope = next((s for s in reversed(scopes) if s[0] <= number <= s[1]), None)
            symbol = scope[2] if scope else None
            exact = scope and number == scope[0] and symbol.casefold() == needle
            results.append((0 if exact else 1, path, number, symbol))
    return [dict(path=p, line=n, symbol=s, match=query)
            for _, p, n, s in sorted(results)[:limit]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.query.strip() or not 1 <= args.limit <= 100:
        parser.error("use a nonempty query and a limit of 1 to 100")
    location = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if location.returncode:
        parser.error("run inside a Git worktree")
    hits = search(Path(location.stdout.strip()).resolve(), args.query, args.limit)
    if args.json:
        print(json.dumps(hits, ensure_ascii=False))
    else:
        for hit in hits:
            print(f"{hit['path']}:{hit['line']} {hit['symbol'] or hit['match']}")


if __name__ == "__main__":
    main()
