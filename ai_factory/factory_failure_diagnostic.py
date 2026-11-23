"""Redacted failure-stage receipt for the synthetic CODEN offline-model job.

Never return generated Python, prompts, paths, event details or exception messages.
This is diagnostic metadata only and does not prove inference succeeded.
"""
import argparse
import json
from pathlib import Path

UNAVAILABLE = {"status": "diagnostic_unavailable"}
STAGES = frozenset({
    "orchestrator", "architecture", "coding", "security",
    "testing", "documentation", "devops", "review",
})
ERROR_TYPES = frozenset({
    "OSError", "ValueError", "RuntimeError", "SyntaxError",
    "RecursionError", "ArithmeticError", "TimeoutExpired",
    "ImportError", "CalledProcessError", "SubprocessError",
})


def summarize(result_path: Path, output_root: Path) -> dict:
    """Give only safe, allowlisted stage/type fields; fail closed on bad evidence."""
    try:
        result_path = Path(result_path)
        output_root = Path(output_root)
        if (result_path.is_symlink() or not result_path.is_file()
                or result_path.stat().st_size > 4096
                or output_root.is_symlink() or not output_root.is_dir()):
            return dict(UNAVAILABLE)
        record = json.loads(result_path.read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            return dict(UNAVAILABLE)
        status = record.get("status")
        folder = record.get("directory")
        if status not in ("failed", "blocked") or not isinstance(folder, str):
            return dict(UNAVAILABLE)
        work = Path(folder)
        if (not work.is_absolute() or work.is_symlink()
                or not work.is_dir() or not work.name.startswith("coden-project-")
                or work.parent.resolve() != output_root.resolve()):
            return dict(UNAVAILABLE)
        path = work / "events.jsonl"
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 65536:
            return dict(UNAVAILABLE)
        lines = path.read_text(encoding="utf-8").splitlines()
        if not 1 <= len(lines) <= 32:
            return dict(UNAVAILABLE)
        last = json.loads(lines[-1])
        if not isinstance(last, dict) or last.get("state") != status:
            return dict(UNAVAILABLE)
        role = last.get("role")
        if role not in STAGES:
            return dict(UNAVAILABLE)
        if status == "blocked":
            return {"status": "blocked", "stage": role}
        error = last.get("error")
        if error not in ERROR_TYPES:
            return dict(UNAVAILABLE)
        return {"status": "failed", "stage": role, "error_type": error}
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError):
        return dict(UNAVAILABLE)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(summarize(args.result, args.root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
