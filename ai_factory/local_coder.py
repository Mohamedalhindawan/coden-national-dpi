"""One offline CPU completion using verified local runtime and model artifacts."""

import hashlib
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path

CPU_SHA = "da524c71f9dd09913df29264bb7229b99a2de82d8a26e6902e6921d413560d6d"
MODEL_SHA = "1d9614638d18024d0fbb36575a15f1302a3adf044df10345688ec4f6e1c4ff32"


def check_file(path, expected):
    with path.open("rb") as handle:
        if hashlib.file_digest(handle, "sha256").hexdigest() != expected:
            raise ValueError("local asset digest mismatch")


def extract_code(text):
    text = text.strip().removesuffix("[end of text]").strip()
    fenced = re.fullmatch(r"```(?:python)?\s*\n(.*?)\n```", text, re.DOTALL)
    return (fenced.group(1) if fenced else text) + "\n"


def prompt_for(description, cases, feedback=None):
    """Policy-bounded task prompt; never include hidden review cases or prior code."""
    if feedback not in (None, "BoolOp"):
        raise ValueError("unsupported offline candidate feedback")
    examples = "\n".join(
        f"assert transform({c['input']!r}) == {c['expected']!r}" for c in cases
    )
    rules = (
        "Return only Python code completing the EXISTING def transform(value): header. "
        "Write an indented function body, not a repeated function definition. "
        "No explanation, markdown, imports, helpers, or annotations. "
        "Allowed: assignments, integer increments, for loops, independent if statements, "
        "equality ==, simple builtin len and dict.get if required, and return. "
        "Do NOT use boolean 'or' or 'and': BoolOp is forbidden by the AST safety gate. "
        "Do NOT use comprehensions, generators, membership comparisons such as "
        "if status in (...), lambda, any(), or all(). "
        "For multiple labels, compare them using TWO SEPARATE IF statements, "
        "each with its own == condition and increment; never combine conditions. "
        "In a for loop, the required word 'in' is allowed. "
        "The caller already parses JSON and serializes the native Python return value."
    )
    if feedback == "BoolOp":
        rules += (
            " The FIRST generated candidate was rejected by the AST safety policy "
            "for a BoolOp node. Generate a fresh body, not a patch. "
            "A combined if condition using 'or' or 'and' is invalid. "
            "Use two distinct if statements with simple == comparisons. "
            "An UNRELATED toy example counting 'red' and 'blue' labels has this "
            "AST-safe function body (do NOT use these toy labels in the real task):\n"
            "    count = 0\n"
            "    for item in value:\n"
            "        if item == 'red':\n"
            "            count += 1\n"
            "        if item == 'blue':\n"
            "            count += 1\n"
            "    return count\n"
            "For the actual candidate, write a NEW body using the actual task's "
            "labels, keeping the same independent-if structure."
        )
    return (
        "<|im_start|>system\n" + rules
        + "<|im_end|>\n<|im_start|>user\n"
        + description
        + "\nThe function must pass these public Python assertions:\n"
        + examples
        + "<|im_end|>\n<|im_start|>assistant\n```python\ndef transform(value):\n"
    )


def generate(archive, model, description, cases, sandbox, *, feedback=None):
    check_file(archive, CPU_SHA)
    check_file(model, MODEL_SHA)
    prompt = prompt_for(description, cases, feedback)
    with tempfile.TemporaryDirectory() as temp:
        with tarfile.open(archive) as bundle:
            bundle.extractall(temp, filter="data")
        runtime = str(Path(temp) / "llama-b12600")
        args = [
            *sandbox,
            "--proc",
            "/proc",
            "--ro-bind",
            runtime,
            "/llama",
            "--ro-bind",
            str(model.resolve()),
            "/model.gguf",
            "--remount-ro",
            "/",
            "/llama/llama-completion",
            "--offline",
            "-m",
            "/model.gguf",
            "-t",
            "2",
            "-c",
            "2048",
            "-n",
            "192",
            "--seed",
            "7",
            "--temp",
            "0",
            "--no-warmup",
            "--no-display-prompt",
            "-no-cnv",
            "-p",
            prompt,
        ]
        result = subprocess.run(
            args, capture_output=True, env={}, stdin=subprocess.DEVNULL, timeout=90
        )
        if result.returncode or len(result.stdout) > 16384:
            raise RuntimeError("offline completion failed")
        body = result.stdout.decode("utf-8").split("\n```", 1)[0]
        return extract_code("def transform(value):\n" + body)
