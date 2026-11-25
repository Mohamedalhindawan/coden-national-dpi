"""Independent acceptance of a 3-file synthetic OpenHands sandbox export.

No OpenHands SDK, LLM or hosted provider is invoked here. An upstream coding
agent must have run in a separately trusted, isolated workspace before its
output is copied for review. CODEN validates its output as untrusted DATA,
builds a fixed-layout Python zipapp and tests it in the existing pinned
Linux bubblewrap sandbox. Agent-generated tests are NEVER executed.

No task execution or API/network calls occur without operator CLI opt-in.
Nothing here can approve, merge or deploy a release.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import zipfile

from . import project

MAX_SOURCE = 16384
MAX_DOCUMENT = 8192
EXPECTED_FILES = frozenset({"app/logic.py", "README.md", "tests/test_logic.py"})
ENTRY = (
    "from app.logic import transform\n"
    "if __name__ == '__main__':\n"
    "    import json\n"
    "    import sys\n"
    "    print(json.dumps(transform(json.load(sys.stdin)), allow_nan=False))\n"
)


def _trusted_dir(path):
    directory = Path(path).absolute()
    if not directory.is_dir() or any(
        ancestor.is_symlink() for ancestor in (directory, *directory.parents)
    ):
        raise ValueError("existing nonlinked operator directory required")
    return directory


def _read_regular(path, max_bytes):
    # The upstream SDK export is not a trust source. Do not follow symlinks,
    # FIFOs/devices or unexpectedly large files.
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > max_bytes:
            raise ValueError("invalid generated file")
        with os.fdopen(os.dup(fd), "rb") as stream:
            data = stream.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError("generated file exceeds size limit")
        return data.decode("utf-8")
    finally:
        os.close(fd)


def _read_export(path):
    root = _trusted_dir(path)
    present = set()
    for item in root.iterdir():
        if item.is_symlink():
            raise ValueError("linked workspace item forbidden")
        if item.name == "README.md":
            present.add("README.md")
        elif item.name in ("app", "tests"):
            if not item.is_dir():
                raise ValueError("expected source directory")
            members = list(item.iterdir())
            expected = "logic.py" if item.name == "app" else "test_logic.py"
            if len(members) != 1 or members[0].name != expected or members[0].is_symlink():
                raise ValueError("unexpected generated files")
            present.add(f"{item.name}/{expected}")
        else:
            raise ValueError("unexpected workspace file")
    if present != EXPECTED_FILES:
        raise ValueError("incomplete multi-file candidate")
    return {
        "app/logic.py": _read_regular(root / "app" / "logic.py", MAX_SOURCE),
        "README.md": _read_regular(root / "README.md", MAX_DOCUMENT),
        "tests/test_logic.py": _read_regular(root / "tests" / "test_logic.py", MAX_DOCUMENT),
    }


def _result(status, directory=None):
    r = {
        "status": status,
        "execution_authorized": False,
        "release_authorized": False,
        "automatic_retry_allowed": False,
        "agent_execution_performed": False,
    }
    if directory is not None:
        r["directory"] = Path(directory)
    return r


def review(task, candidate_root, output_root):
    """Operator-controlled review; this does not invoke OpenHands itself."""
    if not project.valid(task) or task.get("recipe") != "python-transform":
        raise ValueError("only approved synthetic transform task allowed")
    outputs = _trusted_dir(output_root).resolve()
    export = _trusted_dir(candidate_root).resolve()
    if (outputs == export or outputs in export.parents or export in outputs.parents):
        raise ValueError("review output must be disjoint from agent export")
    source = _read_export(export)

    # Only app/logic.py is executable source in the zipapp. The generated
    # tests are treated as evidence for human inspection, NOT as CI scripts.
    project.inspect_source(source["app/logic.py"])
    ast.parse(source["tests/test_logic.py"])
    project.lint(source["app/logic.py"])
    if not project.supported_host():
        raise RuntimeError("verified Linux bubblewrap sandbox unavailable")

    work = Path(tempfile.mkdtemp(prefix="coden-openhands-review-", dir=outputs))
    archive = work / "candidate.pyz"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_STORED) as packaged:
        for path, text in (
            ("__main__.py", ENTRY),
            ("app/__init__.py", ""),
            ("app/logic.py", source["app/logic.py"]),
        ):
            packaged.writestr(zipfile.ZipInfo(path), text.encode("utf-8"))
    try:
        visible = project.verify(archive, task["cases"])
        hidden = project.verify(archive, task["review_cases"])
    except (OSError, ValueError, RuntimeError, SyntaxError, RecursionError,
            ArithmeticError, subprocess.TimeoutExpired):
        # Keep the untrusted archive for operator inspection. Never create an
        # approval receipt or automatically replay the untrusted candidate.
        return _result("failed", work)

    receipt = {
        "task_id": task["id"],
        "status": "awaiting_human_review",
        "sha256": project.digest(archive),
        "visible_cases": visible,
        "review_cases": hidden,
        "agent_files_examined": sorted(EXPECTED_FILES),
        "source_files_sha256": {
            path: hashlib.sha256(text.encode("utf-8")).hexdigest()
            for path, text in sorted(source.items())
        },
        "task_sha256": hashlib.sha256(project.encoded(task).encode("utf-8")).hexdigest(),
        "agent_authored_tests_executed": False,
        "sandbox": "bubblewrap 0.12.0",
        "execution_authorized": False,
        "release_authorized": False,
    }
    (work / "review.json").write_text(project.encoded(receipt), encoding="utf-8")
    return _result("awaiting_human_review", work)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--evaluate-isolated", action="store_true",
                        help="Operator authorizes only bounded synthetic sandbox verification")
    args = parser.parse_args(argv)
    if not args.evaluate_isolated:
        print(json.dumps({**_result("disabled")}, sort_keys=True))
        return 0
    try:
        task = json.loads(project.read_text(args.task, 32768))
        result = review(task, args.candidate_dir, args.output_root)
    except (OSError, ValueError, TypeError, RuntimeError):
        result = _result("blocked")
    if "directory" in result:
        result["directory"] = str(result["directory"])
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "awaiting_human_review" else 1


if __name__ == "__main__":
    sys.exit(main())
