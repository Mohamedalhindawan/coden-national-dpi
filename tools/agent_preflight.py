#!/usr/bin/env python3
"""Run the local preflight checks used by the free-first agent workflow.

Checks run in this order: tracked secret scan, full test suite, OpenAPI
validation. Findings never print the matching value, only the file, line and
pattern label. Exit status is non-zero when any check fails or cannot run.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 2_000_000
ENV_TEMPLATES = {".env.example", ".env.sample", ".env.template"}
SKIP_DIRECTORIES = {".git", ".venv", "venv", "node_modules", "artifacts", "__pycache__"}

SECRET_PATTERNS = (
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("OpenAI-style API key", re.compile(r"sk-[A-Za-z0-9]{16,}")),
    ("GitHub personal access token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("AWS access key ID", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("bearer token", re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]{20,}")),
)


@dataclass(frozen=True)
class Finding:
    """A possible secret location. The matched value is intentionally absent."""

    path: str
    line: int
    label: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: possible {self.label} (value not shown)"


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str

    def render(self) -> str:
        status = "PASS" if self.ok else "FAIL"
        return f"[{status}] {self.name}: {self.detail}"


def scan_text(text: str, path: str = "<text>") -> list[Finding]:
    """Return possible secret findings without retaining the matched value."""
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                findings.append(Finding(path, number, label))
                break
    return findings


def is_disallowed_env_file(path: str) -> bool:
    """True for workspace environment files that may hold real secrets."""
    name = Path(path).name
    return name == ".env" or (name.startswith(".env.") and name not in ENV_TEMPLATES)


def is_skipped_path(path: str) -> bool:
    """Skip caches, environments, and generated screenshots when scanning."""
    return any(part in SKIP_DIRECTORIES for part in Path(path).parts[:-1])


def summarise(results: list[CheckResult]) -> str:
    """Render a compact report with an explicit overall status."""
    passed = sum(1 for result in results if result.ok)
    status = "PASS" if results and passed == len(results) else "FAIL"
    lines = [f"{status}: {passed}/{len(results)} preflight checks passed"]
    lines.extend(result.render() for result in results)
    return "\n".join(lines)


def run_command(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True)


def workspace_files() -> list[str]:
    """Tracked and untracked non-ignored files, so pre-commit checks cover new work."""
    result = run_command(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git ls-files failed")
    paths = {path for path in result.stdout.split("\0") if path}
    return sorted(path for path in paths if not is_skipped_path(path))


def read_text_file(path: str) -> str | None:
    data = (ROOT / path).read_bytes()
    if len(data) > MAX_FILE_BYTES or b"\0" in data[:8192]:
        return None
    return data.decode("utf-8", "replace")


def check_secrets() -> CheckResult:
    findings: list[Finding] = []
    env_files: list[str] = []
    scanned = 0
    try:
        for path in workspace_files():
            if is_disallowed_env_file(path):
                env_files.append(path)
            text = read_text_file(path)
            if text is None:
                continue
            scanned += 1
            findings.extend(scan_text(text, path))
    except (OSError, RuntimeError) as error:
        return CheckResult("Secret scan", False, f"could not scan repository: {error}")

    details = []
    if env_files:
        details.append("tracked environment files: " + ", ".join(env_files))
    if findings:
        shown = [str(finding) for finding in findings[:20]]
        if len(findings) > len(shown):
            shown.append(f"... and {len(findings) - len(shown)} more")
        details.append("\n".join(shown))
    detail = "\n".join(details) if details else f"no findings in {scanned} workspace text files"
    return CheckResult("Secret scan", not findings and not env_files, detail)


def check_tests() -> CheckResult:
    result = run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    output = [line.strip() for line in (result.stderr or result.stdout).splitlines() if line.strip()]
    tail = " | ".join(output[-2:]) if output else "no output"
    return CheckResult("Test suite", result.returncode == 0, f"exit {result.returncode}; {tail}")


def check_openapi() -> CheckResult:
    probe = run_command([sys.executable, "-c", "import openapi_spec_validator"])
    if probe.returncode != 0:
        return CheckResult(
            "OpenAPI contract",
            False,
            "validator not installed; run: python -m pip install -r requirements-dev.txt",
        )
    result = run_command([sys.executable, "-m", "openapi_spec_validator", "api/openapi.yaml"])
    if result.returncode == 0:
        return CheckResult("OpenAPI contract", True, "api/openapi.yaml is valid")
    first_line = (result.stderr or result.stdout).strip().splitlines()
    detail = first_line[0] if first_line else "validation failed"
    return CheckResult("OpenAPI contract", False, detail)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local CODEN preflight checks.")
    parser.add_argument(
        "--secrets-only",
        action="store_true",
        help="scan tracked files for secrets and skip tests and OpenAPI validation",
    )
    args = parser.parse_args(argv)

    branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip() or "unknown"
    print(f"CODEN agent preflight — branch: {branch}")

    checks = [check_secrets()]
    if not args.secrets_only:
        checks.append(check_tests())
        checks.append(check_openapi())

    print(summarise(checks))
    if all(check.ok for check in checks):
        print("\nAll required checks ran and passed. Record the commands and results in the PR.")
        return 0
    print("\nOne or more checks failed or could not run. Do not report them as passed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
