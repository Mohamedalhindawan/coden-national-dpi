"""Offline eight-role factory for synthetic, single-module Python JSON transforms."""

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from .review_queue import prepare_review_queue

EXAMPLE = Path(__file__).with_name("examples") / "status-counts.json"
LIMIT = 16384
MAX_AST_NODES = 512
MAX_AST_DEPTH = 40
ROLES = (
    "architecture",
    "coding",
    "security",
    "testing",
    "documentation",
    "devops",
    "review",
)
DEMO = """def transform(value):
    counts = {}
    for status in value:
        counts[status] = counts.get(status, 0) + 1
    return counts
"""
ENTRY = """
if __name__ == "__main__":
    import json
    import sys

    print(json.dumps(transform(json.load(sys.stdin)), allow_nan=False))
"""


def encoded(value):
    return json.dumps(value, allow_nan=False, ensure_ascii=True, sort_keys=True)


def read_text(path, limit):
    with os.fdopen(
        os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW), "rb"
    ) as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError("regular file required")
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("file too large")
    return raw.decode("utf-8")


def valid(task):
    if not isinstance(task, dict) or len(encoded(task)) > 32768:
        return False
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", str(task.get("id", ""))):
        return False
    if (
        task.get("estimated_cost_usd") != 0
        or not prepare_review_queue([task], budget_usd=0)["valid"]
    ):
        return False
    if task["requested_actions"] != ["run_tests"] or task.get("recipe") not in (
        "status-counts",
        "python-transform",
    ):
        return False
    for field in ("cases", "review_cases"):
        cases = task.get(field)
        if not isinstance(cases, list) or not 1 <= len(cases) <= 8:
            return False
        if any(
            not isinstance(c, dict)
            or set(c) != {"input", "expected"}
            or len(encoded(c)) > 4096
            for c in cases
        ):
            return False
    visible = {encoded(c["input"]) for c in task["cases"]}
    return all(encoded(c["input"]) not in visible for c in task["review_cases"])


def inspect_source(source):
    """Constrain the plugin interface; OS isolation separately contains execution."""
    tree = ast.parse(source)
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise ValueError("expected a single function")
    func = tree.body[0]
    if (
        func.name != "transform"
        or ast.unparse(func.args) != "value"
        or func.decorator_list
        or func.returns
    ):
        raise ValueError("expected transform(value)")
    allowed = (
        ast.Module,
        ast.FunctionDef,
        ast.arguments,
        ast.arg,
        ast.Name,
        ast.Load,
        ast.Store,
        ast.Assign,
        ast.AugAssign,
        ast.Subscript,
        ast.Constant,
        ast.Return,
        ast.For,
        ast.If,
        ast.IfExp,
        ast.Dict,
        ast.List,
        ast.Tuple,
        ast.Call,
        ast.Attribute,
        ast.BinOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Mod,
        ast.Compare,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.Gt,
        ast.In,
        ast.UnaryOp,
        ast.USub,
        ast.Not,
    )
    pending = [(tree, 0)]
    visited = 0
    while pending:
        node, depth = pending.pop()
        visited += 1
        if visited > MAX_AST_NODES or depth > MAX_AST_DEPTH:
            raise ValueError("source AST exceeds policy limits")
        pending.extend((child, depth + 1) for child in ast.iter_child_nodes(node))
        if not isinstance(node, allowed):
            raise ValueError("unsupported syntax")
        if isinstance(node, ast.Name) and node.id.startswith("_"):
            raise ValueError("private name")
        if isinstance(node, ast.Attribute) and (
            node.attr != "get" or not isinstance(node.ctx, ast.Load)
        ):
            raise ValueError("unsupported attribute")
        if isinstance(node, ast.Call) and not (
            isinstance(node.func, ast.Attribute)
            or isinstance(node.func, ast.Name)
            and node.func.id in {"len", "sum", "sorted", "min", "max"}
        ):
            raise ValueError("unsupported call")


def lint(source):
    if version("ruff") != "0.17.6":
        raise RuntimeError("unsupported Ruff version")
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "ruff",
            "check",
            "--isolated",
            "--no-cache",
            "--select",
            "E9,F,S",
            "--stdin-filename",
            "transform.py",
            "-",
        ],
        input=source.encode(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=8,
    )
    if result.returncode:
        raise ValueError("Ruff check failed")


def supported_host():
    try:
        result = subprocess.check_output(
            [shutil.which("bwrap") or "/usr/bin/bwrap", "--version"],
            text=True,
            timeout=3,
        )
        return (
            result.strip() == "bubblewrap 0.12.0" and Path("/usr/bin/prlimit").is_file()
        )
    except (OSError, subprocess.SubprocessError):
        return False


def sandbox_args():
    if not supported_host():
        raise RuntimeError("supported sandbox unavailable")
    args = [
        shutil.which("bwrap") or "/usr/bin/bwrap",
        "--unshare-user",
        "--unshare-all",
        "--disable-userns",
        "--die-with-parent",
        "--new-session",
        "--clearenv",
        "--cap-drop",
        "ALL",
        "--ro-bind",
        "/usr/lib",
        "/usr/lib",
        "--symlink",
        "usr/lib",
        "/lib",
        "--ro-bind",
        "/usr/lib64",
        "/usr/lib64",
        "--symlink",
        "usr/lib64",
        "/lib64",
    ]
    for name in ("/usr/bin/python3", "/usr/bin/prlimit"):
        args.extend(["--ro-bind", name, name])
    return args


def execute(program, value):
    args = sandbox_args()
    args.extend(
        [
            "--ro-bind",
            str(program.resolve()),
            "/program",
            "--remount-ro",
            "/",
            "/usr/bin/prlimit",
            "--as=134217728",
            "--cpu=2",
            "--nproc=1",
            "--fsize=16384",
            "--nofile=32",
            "--",
            "/usr/bin/python3",
            "-ISB",
            "/program",
        ]
    )
    with tempfile.TemporaryFile() as output:
        result = subprocess.run(
            args,
            input=encoded(value).encode(),
            stdout=output,
            stderr=subprocess.DEVNULL,
            env={},
            timeout=5,
        )
        if result.returncode:
            raise RuntimeError("isolated execution failed")
        output.seek(0)
        return json.loads(output.read(LIMIT))


def verify(program, cases):
    for case in cases:
        if encoded(execute(program, case["input"])) != encoded(case["expected"]):
            raise ValueError("acceptance mismatch")
    return len(cases)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(task, root, source_path=None, *, local_assets=None):
    work = Path(tempfile.mkdtemp(prefix="coden-project-", dir=root))
    role = "orchestrator"

    def record(state, **info):
        with (work / "events.jsonl").open("a", encoding="utf-8") as log:
            print(
                encoded(
                    dict(
                        time=datetime.now(timezone.utc).isoformat(),
                        role=role,
                        state=state,
                        **info,
                    )
                ),
                file=log,
            )

    try:
        if not valid(task) or (
            task["recipe"] == "python-transform"
            and source_path is None
            and local_assets is None
        ):
            record("blocked")
            return work, "blocked"
        record(
            "planned",
            task_id=task["id"],
            stages=ROLES,
            attempts=1,
            paid_calls=0,
            budget_usd=0,
        )
        role = "architecture"
        contract = dict(
            interface="transform(value)",
            transport="JSON stdin/stdout",
            task=task["id"],
            release="human review",
            acceptance=task["cases"],
        )
        (work / "contract.json").write_text(encoded(contract))
        record("complete", contract_sha256=digest(work / "contract.json"))
        role = "coding"
        if local_assets is not None:
            from . import local_coder

            source = local_coder.generate(
                *local_assets, task["description"], task["cases"], sandbox_args()
            )
            origin = "local Qwen2.5-Coder / llama.cpp b12600"
        elif source_path is not None:
            source = read_text(source_path, LIMIT)
            origin = "local candidate"
        else:
            source = DEMO
            origin = "built-in recipe"
        program = work / "program.py"
        program.write_text(source + "\n" + ENTRY, encoding="utf-8")
        record("complete", input=origin, sha256=digest(program))
        role = "security"
        inspect_source(source)
        lint(source)
        record("passed", checks=["transform AST policy", "Ruff 0.17.6 E9,F,S"])
        role = "testing"
        record(
            "passed",
            verified_cases=verify(program, task["cases"]),
            sandbox="bubblewrap 0.12.0",
        )
        role = "documentation"
        readme = work / "README.md"
        readme.write_text(
            f"# {task['id']}\n\n{task['description']}\n\n"
            "Run with Python 3 using JSON on standard input.\n\n"
            "    python3 candidate.pyz < input.json\n\n"
            "Synthetic review candidate. See contract.json for example input and output.\n",
            encoding="utf-8",
        )
        record("complete", sha256=digest(readme))
        role = "devops"
        artifact = work / "candidate.pyz"
        with zipfile.ZipFile(artifact, "x") as archive:
            for name, path in [
                ("__main__.py", program),
                ("README.md", readme),
                ("contract.json", work / "contract.json"),
            ]:
                archive.writestr(zipfile.ZipInfo(name), path.read_bytes())
        record("packaged", sha256=digest(artifact))
        role = "review"
        checked = verify(artifact, task["review_cases"])
        receipt = dict(
            sha256=digest(artifact),
            review_cases=checked,
            release_authorized=False,
            review_kind="automated artifact acceptance",
            status="awaiting_human_review",
        )
        (work / "review.json").write_text(encoded(receipt))
        record("passed", **receipt)
        role = "orchestrator"
        record("awaiting_human_review")
        return work, "awaiting_human_review"
    except (
        OSError,
        ValueError,
        RuntimeError,
        SyntaxError,
        RecursionError,
        ArithmeticError,
        subprocess.SubprocessError,
        ImportError,
    ) as exc:
        record("failed", error=type(exc).__name__)
        return work, "failed"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path, default=EXAMPLE)
    coding = parser.add_mutually_exclusive_group()
    coding.add_argument(
        "--local-model",
        nargs=2,
        type=Path,
        metavar=("CPU_TARBALL", "GGUF"),
        help="Generate once with hash-verified offline model files",
    )
    coding.add_argument(
        "--source", type=Path, help="Local reviewed synthetic transform module"
    )
    parser.add_argument(
        "--output", type=Path, help="Existing directory for private run folders"
    )
    args = parser.parse_args()
    try:
        task = json.loads(read_text(args.task, 32768))
        work, status = run(
            task, args.output, args.source, local_assets=args.local_model
        )
    except (OSError, ValueError, RecursionError) as exc:
        parser.exit(2, f"Input error ({type(exc).__name__})\n")
    print(encoded(dict(directory=str(work), status=status)))
    return int(status != "awaiting_human_review")


if __name__ == "__main__":
    raise SystemExit(main())
