"""Adopt-First: official Ollama Python SDK -> existing isolated CODEN review pilot.

This is an operator-invoked, single synthetic transform experiment. The
Ollama server/SDK supplies inference; CODEN reuses project.run for safety
checks, packaging and independent review. No general coding agent, daemon,
cloud model, self-approval, retries or main-branch operations are implemented.

The SDK is optional and must be supplied from an independently vetted,
pinned installation. CI uses a fake SDK and a real pinned Linux sandbox.
A local Ollama server is not by itself a network isolation boundary.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from . import local_coder, ollama_probe, project

MAX_SOURCE_BYTES = 8192
CLOUD_MARKER = re.compile(r"(^|[-:/])cloud($|[-:/])", re.IGNORECASE)

SYSTEM = (
    "Return only the complete Python function def transform(value): ..."
    " without imports, decorators, helpers, file access, network, or Markdown."
    " Use basic builtins and loops/dictionaries. The input is a native Python"
    " JSON-compatible value. Do not output tests, explanatory text or other"
    " code outside the function."
)


def _result(status, *, attempted=False, directory=None):
    result = {
        "status": status,
        "model_run_attempted": attempted,
        "execution_authorized": False,
        "provider_approved": False,
        "release_authorized": False,
        "automatic_retry_allowed": False,
    }
    if directory is not None:
        result["directory"] = str(directory)
    return result


def _response_text(response):
    text = response.get("response") if isinstance(response, dict) else getattr(response, "response", None)
    if not isinstance(text, str) or not text or len(text.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise ValueError("invalid model response")
    source = local_coder.extract_code(text)
    if len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise ValueError("source too large")
    project.inspect_source(source)
    return source


def run_once(task, output_root, endpoint, model, *, allow_local_inference=False,
             client_factory=None, discovery=None):
    """One explicit local generation; no auto-model download or agent actions.

    The generated source is never executed on the host directly. It enters
    existing CODEN AST+Ruff checks and pinned bubblewrap acceptance tests.
    """
    ollama_probe._port(endpoint)
    if not isinstance(model, str) or not ollama_probe.MODEL.fullmatch(model) or CLOUD_MARKER.search(model):
        raise ValueError("reviewed local-only model name required")
    if type(allow_local_inference) is not bool:
        raise ValueError("local inference opt-in must be boolean")
    if not project.valid(task) or task.get("recipe") != "python-transform":
        raise ValueError("only synthetic Python transform acceptance fixture supported")
    if not allow_local_inference:
        return _result("disabled")

    root = Path(output_root)
    if not root.is_dir() or root.is_symlink() or root.parent.is_symlink():
        raise ValueError("existing trusted operator output directory required")

    # The upstream Ollama SDK auto-adds OLLAMA_API_KEY from the environment.
    # For this strictly local, unauthenticated experiment, reject it instead.
    if "OLLAMA_API_KEY" in os.environ:
        return _result("unsafe_environment")

    if not project.supported_host():
        return _result("sandbox_unavailable")

    lookup = ollama_probe.probe if discovery is None else discovery
    try:
        available = lookup(endpoint, model, allow_loopback=True)
    except (OSError, ValueError, TypeError):
        return _result("model_unavailable")
    if not isinstance(available, dict) or available.get("probe_status") != "available" or available.get("model_available") is not True:
        return _result("model_unavailable")

    if client_factory is None:
        try:
            from ollama import Client
        except ImportError:
            return _result("sdk_unavailable")
        client_factory = Client

    prompt = (
        task["description"]
        + "\nVisible examples (never review-only cases):\n"
        + project.encoded(task["cases"])
        + "\nReturn a complete transform(value) function only."
    )
    client = None
    try:
        # Explicit host, no httpx environment proxies, no redirects. No tools.
        client = client_factory(
            host=endpoint, timeout=90, follow_redirects=False, trust_env=False,
        )
        response = client.generate(
            model=model, prompt=prompt, system=SYSTEM, stream=False,
            options={"temperature": 0, "num_predict": 192},
            keep_alive=0,
        )
        source = _response_text(response)
    except Exception:
        # Provider exceptions may contain credentials or unsanitized prompts.
        # A failed generation can have consumed local compute but is not replayed.
        return _result("inference_failed" if client is None else "invalid_model_output"
                       if "response" in locals() else "inference_failed", attempted=True)
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass

    try:
        with tempfile.TemporaryDirectory(prefix=".model-source-", dir=root) as temp:
            source_file = Path(temp) / "candidate.py"
            source_file.write_text(source, encoding="utf-8")
            source_file.chmod(0o600)
            directory, status = project.run(task, root, source_path=source_file)
        if status not in ("awaiting_human_review", "failed", "blocked"):
            return _result("needs_review", attempted=True, directory=directory)
        return _result(status, attempted=True, directory=directory)
    except Exception:
        # Model outputs may have produced partial artifacts; never auto-retry.
        return _result("needs_review", attempted=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--model", required=True)
    parser.add_argument("--allow-local-inference", action="store_true",
                        help="Operator explicitly permits one model generation on local Ollama")
    args = parser.parse_args(argv)
    try:
        task = json.loads(project.read_text(args.task, 32768))
        result = run_once(task, args.output_root, args.endpoint, args.model,
                          allow_local_inference=args.allow_local_inference)
    except (OSError, ValueError, TypeError):
        result = _result("invalid_config")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] in ("disabled", "awaiting_human_review") else 1


if __name__ == "__main__":
    sys.exit(main())
