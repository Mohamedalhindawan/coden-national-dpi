"""Fast preflight checks for AI-agent work in the CODEN repository.

This script checks repository structure and safety statements before the full
test suite. It does not replace tests, code review, or security scanning.
"""
import argparse
import json
from pathlib import Path

REQUIRED_FILES = (
    "AGENTS.md",
    "README.md",
    "CODEN_MASTER_ENGINEERING_PLAYBOOK.md",
    "api/openapi.yaml",
    "tests/test_prototype_contract.py",
    ".github/workflows/prototype-checks.yml",
)

REQUIRED_MARKERS = {
    "AGENTS.md": (
        "Use synthetic/demo data only.",
        "Human approval required",
    ),
    "README.md": (
        "proposal and prototype",
        "Use synthetic data only.",
    ),
    "CODEN_MASTER_ENGINEERING_PLAYBOOK.md": (
        "not an approved national production system",
        "All high-impact changes require explicit human approval.",
    ),
    "api/openapi.yaml": (
        "This specification is not a deployed API",
        "const: true",
        "bearerAuth",
    ),
}


def inspect_repository(root: Path) -> list[dict[str, object]]:
    """Return deterministic pass/fail results for required project guardrails."""
    results: list[dict[str, object]] = []

    for relative_path in REQUIRED_FILES:
        path = root / relative_path
        exists = path.is_file()
        results.append({
            "name": f"file:{relative_path}",
            "passed": exists,
            "detail": "required file exists" if exists else "required file is missing",
        })

    for relative_path, markers in REQUIRED_MARKERS.items():
        path = root / relative_path
        if not path.is_file():
            for marker in markers:
                results.append({
                    "name": f"marker:{relative_path}:{marker}",
                    "passed": False,
                    "detail": "cannot check safety marker because the file is missing",
                })
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            for marker in markers:
                results.append({
                    "name": f"marker:{relative_path}:{marker}",
                    "passed": False,
                    "detail": f"cannot read file: {error}",
                })
            continue

        for marker in markers:
            found = marker in content
            results.append({
                "name": f"marker:{relative_path}:{marker}",
                "passed": found,
                "detail": "required safety statement found" if found
                else "required safety statement is missing",
            })

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON for automation",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (defaults to the parent of tools/)",
    )
    args = parser.parse_args()
    results = inspect_repository(args.root.resolve())
    failed = [result for result in results if not result["passed"]]

    if args.json:
        print(json.dumps({
            "ok": not failed,
            "total": len(results),
            "passed": len(results) - len(failed),
            "failed": len(failed),
            "checks": results,
        }, ensure_ascii=False, indent=2))
    else:
        for result in results:
            status = "PASS" if result["passed"] else "FAIL"
            print(f"[{status}] {result['name']}: {result['detail']}")
        print(f"Preflight: {len(results) - len(failed)}/{len(results)} checks passed")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
