"""Read-only V4 measurement report. Never guesses missing completion rates."""
import argparse
import json
from pathlib import Path

try:
    from .v4_domain_progress import calculate_domain_progress, DOMAINS
except ImportError:
    from v4_domain_progress import calculate_domain_progress, DOMAINS


def build_report(manifest):
    result = calculate_domain_progress(manifest)
    if result is None:
        return {
            "status": "unmeasurable",
            "overall": {"completed_pct": None, "remaining_pct": None},
            "domains": {d: {"completed_pct": None, "remaining_pct": None} for d in DOMAINS},
            "reason": "Approved V4 source, eight phase weights, domain requirements and verified acceptance evidence are required.",
        }
    def pair(values):
        return {"completed_pct": values[0], "remaining_pct": values[1]}
    return {
        "status": "measurable",
        "overall": pair(result["overall"]),
        "domains": {d: pair(result["domains"][d]) for d in DOMAINS},
        "denominators": result["denominators"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Read-only approved V4 manifest JSON")
    args = parser.parse_args(argv)
    with args.manifest.open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    print(json.dumps(build_report(manifest), ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
