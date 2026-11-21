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


def generate(archive, model, description, cases, sandbox):
    check_file(archive, CPU_SHA)
    check_file(model, MODEL_SHA)
    examples = "\n".join(
        f"assert transform({c['input']!r}) == {c['expected']!r}" for c in cases
    )
    prompt = (
        "<|im_start|>system\nReturn only Python source for a single function called "
        "transform(value). No explanation, annotations, imports or helpers. Use simple "
        "builtins, loops and dictionaries. The caller already decodes input and encodes output. "
        "Return the native Python value directly. Do not call json.loads or json.dumps.<|im_end|>\n<|im_start|>user\n"
        + description
        + "\nThe function must pass these Python assertions:\n"
        + examples
        + "<|im_end|>\n<|im_start|>assistant\n```python\ndef transform(value):\n"
    )
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
