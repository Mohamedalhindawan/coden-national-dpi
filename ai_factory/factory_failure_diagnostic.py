"""Redacted failure-stage receipt for the synthetic CODEN offline-model job.

Never return generated Python, prompts, paths, event details or exception messages.
This is diagnostic metadata only and does not prove inference succeeded.
"""
import argparse
import ast
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
# Only fixed public AST grammar names, never generated code or prompt text.
FORBIDDEN_SHAPES = (
    "GeneratorExp", "ListComp", "SetComp", "DictComp", "BoolOp",
    "In", "NotIn", "While", "Try", "With", "Import", "ImportFrom",
    "Lambda", "NamedExpr", "Yield", "YieldFrom", "Await",
    "ClassDef", "Global", "Nonlocal", "Delete", "Raise",
)


def _forbidden_shape(node: ast.AST) -> str | None:
    seen = {type(item).__name__ for item in ast.walk(node)}
    return next((shape for shape in FORBIDDEN_SHAPES if shape in seen), None)




def _security_hint(work: Path):
    """Classify an AST rejection without running or exposing generated source."""
    program = work / "program.py"
    try:
        if (program.is_symlink() or not program.is_file()
                or program.stat().st_size > 32768):
            return None
        parsed = ast.parse(program.read_text(encoding="utf-8"))
        # project.py appends its own fixed __main__ block after generated transform.
        if (len(parsed.body) != 2
                or not isinstance(parsed.body[0], ast.FunctionDef)
                or not isinstance(parsed.body[1], ast.If)):
            return "unexpected_source_layout"
        from .project import inspect_source

        try:
            inspect_source(ast.unparse(parsed.body[0]))
        except ValueError as exc:
            hint = {
                "unsupported syntax": "unsupported_syntax",
                "expected a single function": "unexpected_source_layout",
                "expected transform(value)": "wrong_interface",
                "source AST exceeds policy limits": "ast_limit",
                "private name": "private_name",
                "unsupported attribute": "unsupported_attribute",
                "unsupported call": "unsupported_call",
            }.get(str(exc), "ast_validation_failure")
            if hint == "unsupported_syntax":
                return (hint, _forbidden_shape(parsed.body[0]))
            return hint
        return "lint_or_other"
    except (OSError, ValueError, SyntaxError, UnicodeError, RecursionError):
        return None


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
        summary = {"status": "failed", "stage": role, "error_type": error}
        if role == "security" and error == "ValueError":
            hint = _security_hint(work)
            if isinstance(hint, tuple):
                summary["security_hint"] = hint[0]
                if hint[1] is not None:
                    summary["security_node"] = hint[1]
            elif hint is not None:
                summary["security_hint"] = hint
        return summary
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
