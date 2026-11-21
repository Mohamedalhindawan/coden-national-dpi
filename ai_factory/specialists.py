"""Run bounded local AI specialists, checkpointing each verified handoff in SQLite."""

import argparse
import ast
import tempfile
import time
import zipfile
from pathlib import Path

from . import local_coder
from .operations import Operations
from .project import digest, encoded, inspect_source, lint, sandbox_args, verify


def parse_test(text):
    statement = text.strip().splitlines()[0] if text.strip() else ""
    node = ast.parse(statement).body
    if len(node) == 1 and isinstance(node[0], ast.Assert):
        expr = node[0].test
        if (
            isinstance(expr, ast.Compare)
            and len(expr.ops) == 1
            and isinstance(expr.ops[0], ast.Eq)
            and isinstance(expr.left, ast.Call)
            and isinstance(expr.left.func, ast.Name)
            and expr.left.func.id == "transform"
            and len(expr.left.args) == 1
            and not expr.left.keywords
        ):
            case = dict(
                input=ast.literal_eval(expr.left.args[0]),
                expected=ast.literal_eval(expr.comparators[0]),
            )
            if len(encoded(case)) <= 4096:
                return case
    raise ValueError("expected a single literal test")


def approved(verdict):
    if verdict.strip() != "PASS":
        raise ValueError("model withheld approval")


def archive(path, files):
    with zipfile.ZipFile(path, "x") as out:
        for name, content in sorted(files.items()):
            out.writestr(zipfile.ZipInfo(name), content.encode())


def stage(ops, claim, assets, work):
    role = claim["task_id"]
    task = ops.task
    goal = task["description"]
    visible = task["cases"]
    result = ops.result

    def ask(instruction, material, *, prefix="", grammar=None):
        prompt = (
            f"<|im_start|>system\nYou are the {role} specialist. {instruction}<|im_end|>\n"
            f"<|im_start|>user\n{material}<|im_end|>\n<|im_start|>assistant\n{prefix}"
        )
        ops.reserve(claim, len(prompt.encode()))
        answer = local_coder.complete(*assets, prompt, sandbox_args(), grammar)
        answer = answer.strip("\n").removesuffix("[end of text]").rstrip()
        if not answer.strip():
            raise ValueError("empty model response")
        return answer

    if role == "orchestrator":
        order = ask(
            "Set acceptance priority: edge-first for shortest inputs first, normal-first for largest first.",
            goal + "\nCases: " + encoded(visible),
            grammar='root ::= "edge-first" | "normal-first"',
        ).strip()
        if order not in {"edge-first", "normal-first"}:
            raise ValueError("invalid test plan")
        return {"plan": order}
    visible = sorted(
        visible,
        key=lambda c: len(encoded(c["input"])),
        reverse=result("orchestrator")["plan"] == "normal-first",
    )
    if role == "architecture":
        module = ask(
            "Choose the Python business module name. Return only the name.",
            goal + "\n" + result("orchestrator")["plan"][:512],
            grammar='root ::= "metrics" | "summary" | "analysis"',
        ).strip()
        if module not in {"metrics", "summary", "analysis"}:
            raise ValueError("invalid module name")
        return {"module": module}
    module = result("architecture")["module"]
    if role == "coding":
        assertions = "\n".join(
            f"assert transform({c['input']!r}) == {c['expected']!r}" for c in visible
        )
        body = ask(
            "Return only the body of transform(value). Use simple Python, no imports or annotations.",
            f"Module {module}. {goal}\n{assertions}",
            prefix="```python\ndef transform(value):\n",
        )
        code = "def transform(value):\n" + body.split("\n```")[0] + "\n"
        return {"source": code}
    code = result("coding")["source"]
    if role == "security":
        inspect_source(code)
        lint(code)
        verdict = ask(
            "Inspect the source. PASS for a pure transform with no unsafe operations. Otherwise BLOCK.",
            code,
            grammar='root ::= "PASS" | "BLOCK"',
        )
        approved(verdict)
        return {"decision": verdict, "checks": ["AST policy", "Ruff E9,F,S"]}
    if role == "testing":
        known = {encoded(c["input"]) for c in visible}
        alternatives = [
            value
            for c in visible
            if isinstance(c["input"], list)
            for value in [c["input"][::-1], c["input"] * 2]
            if encoded(value) not in known and len(encoded(value)) <= 512
        ]
        prefix = (
            f"assert transform({alternatives[0]!r}) == "
            if alternatives
            else "assert transform("
        )
        sample = ask(
            "Complete the Python assertion. Give the expected literal result for the supplied input.",
            goal + "\n" + code + "\nExisting cases: " + encoded(visible),
            prefix=prefix,
        )
        case = parse_test(prefix + sample)
        if encoded(case["input"]) in known or type(case["input"]) not in {
            type(c["input"]) for c in visible
        }:
            raise ValueError("test input must be new and match the public contract")
        # Execute the case before granting the test stage a successful handoff.
        from .project import ENTRY

        program = work / "test-subject.py"
        program.write_text(code + "\n" + ENTRY)
        count = verify(program, [*visible, case])
        return {"case": case, "passed": count}
    if role == "documentation":
        summary = (
            ask(
                "Describe the program's purpose in one sentence of plain text. No examples or code.",
                goal,
            )
            .strip()
            .splitlines()[0]
        )
        example = visible[0]
        readme = (
            f"# {task['id']}\n\n{summary}\n\nRun `python3 candidate.pyz < input.json`. "
            f"Input and output use JSON.\n\nInput: `{encoded(example['input'])}`\n\n"
            f"Expected: `{encoded(example['expected'])}`\n"
        )
        return {"readme": readme}
    if role == "devops":
        mode = ask(
            "Select sorted or compact JSON formatting for a standalone offline JSON CLI.",
            goal + "\n" + result("documentation")["readme"][:512],
            grammar='root ::= "sorted" | "compact"',
        ).strip()
        if mode not in ("sorted", "compact"):
            raise ValueError("unsupported output format")
        opts = "sort_keys=True" if mode == "sorted" else 'separators=(",", ":")'
        cli = (
            f"import json\nimport sys\nfrom {module} import transform\n\n"
            f"def main():\n    print(json.dumps(transform(json.load(sys.stdin)), allow_nan=False, {opts}))\n"
        )
        cases = [*visible, result("testing")["case"]]
        test = (
            f"import unittest\nfrom {module} import transform\n\nclass Contract(unittest.TestCase):\n"
            + "".join(
                f"    def test_{i}(self):\n        self.assertEqual(transform({c['input']!r}), {c['expected']!r})\n"
                for i, c in enumerate(cases)
            )
        )
        files = {
            module + ".py": code,
            "cli.py": cli,
            "__main__.py": "from cli import main\nmain()\n",
            "test_contract.py": test,
            "README.md": result("documentation")["readme"],
        }
        path = work / "candidate.pyz"
        archive(path, files)
        # Run the shipped unittest class inside the same isolation as the release candidate.
        harness = files.copy()
        harness["__main__.py"] = (
            "import unittest, json\nfrom test_contract import Contract\n"
            "suite=unittest.defaultTestLoader.loadTestsFromTestCase(Contract)\n"
            "r=unittest.TextTestRunner().run(suite)\nprint(json.dumps(r.wasSuccessful()))\n"
        )
        checks = work / "tests.pyz"
        archive(checks, harness)
        verify(checks, [{"input": None, "expected": True}])
        return {
            "artifact": str(path),
            "sha256": digest(path),
            "files": sorted(files),
            "passed": len(cases),
            "format": mode,
        }
    package = result("devops")
    path = Path(package["artifact"])
    if digest(path) != package["sha256"]:
        raise ValueError("archive changed since packaging")
    count = verify(path, task["review_cases"])
    verdict = ask(
        "Review the implementation against the requirement. PASS if acceptable, otherwise BLOCK.",
        goal
        + "\n"
        + code
        + f"\nSecurity, unit tests and {count} withheld checks passed.",
        grammar='root ::= "PASS" | "BLOCK"',
    )
    approved(verdict)
    return {
        "decision": verdict,
        "artifact": str(path),
        "sha256": digest(path),
        "withheld_passed": count,
        "status": "awaiting_human_review",
        "release_authorized": False,
    }


def work_once(ops, assets):
    claim = ops.claim()
    if claim is None:
        return False
    work = Path(tempfile.mkdtemp(prefix=claim["task_id"] + "-", dir=ops.root))
    started = time.monotonic()
    try:
        receipt = stage(ops, claim, assets, work)
        receipt.update(
            elapsed_ms=round((time.monotonic() - started) * 1000),
            provider="offline-llama.cpp",
            model_sha256=local_coder.MODEL_SHA,
        )
        ops.complete(claim, receipt)
    except Exception as exc:
        ops.fail(claim, type(exc).__name__)
        raise
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--local-model", nargs=2, type=Path, required=True)
    parser.add_argument("--steps", type=int, choices=range(1, 9), default=8)
    args = parser.parse_args()
    ops = Operations(args.directory.resolve())
    try:
        for _ in range(args.steps):
            if not work_once(ops, args.local_model):
                break
        report = ops.status()
        if report["states"]["review"] == "succeeded":
            report["review"] = ops.result("review")
        print(encoded(report))
        return int(bool(report["tasks"]["failed"] or report["tasks"]["blocked"]))
    finally:
        ops.close()


if __name__ == "__main__":
    raise SystemExit(main())
