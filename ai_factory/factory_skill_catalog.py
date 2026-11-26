"""CODEN Factory: guarded discovery and explicit review-only staging of six portable agent skills.

SKILL.md files are instructions, not runnable components. This module never
imports, executes, enables or installs a skill, agent, model or GitHub action.
"""
import argparse
import hashlib
import os
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "configs" / "factory_execution_skills_v0_1.json"
SKILLS = {
    "intake": "factory-batch-intake",
    "multifile": "factory-tdd-multifile",
    "sandbox": "factory-sandbox-preflight",
    "admission": "factory-adopt-first-gate",
    "review": "factory-independent-review",
    "recovery": "factory-pr-stack-recovery",
}
NAME = re.compile(r"^factory-[a-z0-9-]{1,48}$")


def _read_skill(path: Path, name: str) -> bytes:
    """Verify the actual portable skill exists and declares its canonical name."""
    if (any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file()
            or not 450 < path.stat().st_size < 7000):
        raise ValueError("unsafe or incomplete Agent Skill document")
    raw = path.read_bytes()
    if not 450 < len(raw) < 7000:
        raise ValueError("unsafe or incomplete Agent Skill document")
    text = raw.decode("utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError("skill frontmatter missing")
    header, body = text[4:].split("\n---\n", 1)
    fields = {}
    for line in header.splitlines():
        key, separator, val = line.partition(":")
        if not separator or key not in {"name", "description"} or key in fields:
            raise ValueError("invalid skill frontmatter")
        fields[key] = val.strip()
    if (fields.get("name") != name or not fields.get("description")
            or len(fields["description"]) > 500 or not body.strip()):
        raise ValueError("skill name/description does not match manifest")
    return raw


def validate(data: dict) -> list[dict]:
    """Fail closed if the manifest changes scope, count, privileges or paths."""
    if not isinstance(data, dict) or set(data) != {
        "schema_version", "scope", "status", "automatic_skill_installation",
        "automatic_runtime_execution", "paid_calls_authorized", "skills",
    }:
        raise ValueError("unexpected skill manifest fields")
    if (data.get("schema_version") != "0.1.0"
            or data.get("scope") != "CODEN_FACTORY_ONLY"
            or data.get("status") != "DRAFT_UNAPPROVED"
            or data.get("automatic_skill_installation") is not False
            or data.get("automatic_runtime_execution") is not False
            or data.get("paid_calls_authorized") is not False):
        raise ValueError("unexpected skill catalog scope or permissions")

    rows = data.get("skills")
    if not isinstance(rows, list) or len(rows) != 6:
        raise ValueError("exactly six reviewed skill definitions required")
    seen_names = set()
    seen_tasks = set()
    results = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "name", "task_kind", "purpose", "path", "status", "installed_by_catalog",
            "runtime_invoked", "release_authorized",
        }:
            raise ValueError("unexpected skill entry fields")
        name = row.get("name")
        task = row.get("task_kind")
        if (not isinstance(name, str) or NAME.fullmatch(name) is None
                or name in seen_names
                or not isinstance(task, str) or SKILLS.get(task) != name
                or task in seen_tasks
                or row.get("path") != f".github/skills/{name}/SKILL.md"
                or not isinstance(row.get("purpose"), str)
                or not 5 <= len(row["purpose"]) <= 200
                or row.get("status") != "DRAFT_NOT_AUTO_ACTIVATED"
                or row.get("installed_by_catalog") is not False
                or row.get("runtime_invoked") is not False
                or row.get("release_authorized") is not False):
            raise ValueError("untrusted skill entry, duplicate or privilege escalation")
        path = ROOT / row["path"]
        _read_skill(path, name)
        seen_names.add(name)
        seen_tasks.add(task)
        results.append(row.copy())

    if seen_names != set(SKILLS.values()) or seen_tasks != set(SKILLS):
        raise ValueError("missing factory skill")
    return results


def _unique_json_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate skill manifest key")
        result[key] = value
    return result


def load() -> list[dict]:
    """Read only checked-in local definitions, without imports or installations."""
    if MANIFEST.is_symlink() or not MANIFEST.is_file() or MANIFEST.stat().st_size > 20000:
        raise ValueError("skill manifest missing or untrusted")
    return validate(json.loads(MANIFEST.read_text(encoding="utf-8"),
                               object_pairs_hook=_unique_json_keys))


def choose(task_kind: str) -> dict:
    """Suggest exactly one skill for a known task kind; NEVER invoke the skill."""
    if not isinstance(task_kind, str) or task_kind not in SKILLS:
        raise ValueError("unsupported factory task kind")
    rows = load()
    matched = [r for r in rows if r["task_kind"] == task_kind]
    if len(matched) != 1:
        raise ValueError("skill mapping ambiguous")
    item = matched[0]
    return {
        "task_kind": task_kind,
        "recommended_skill": item["name"],
        "skill_path": item["path"],
        "status": item["status"],
        "execute_now": False,
        "release_authorized": False,
        "paid_calls_authorized": False,
        "note": "Read SKILL.md and follow instructions manually; runtime integration is not authorized.",
    }


def stage_reviewed(task_kind: str, workspace, expected_sha256: str) -> dict:
    """Explicitly copy one reviewed text file to an empty private operator workspace.

    This is not SDK loading, installation, or permission to execute. The caller
    must control the workspace exclusively (no concurrent writers), provide the
    independently reviewed digest, and enforce a fresh isolated HOME/network and
    the returned public-skill switches before any separately approved SDK load.
    No .mcp.json, scripts, resources, external skills or existing files are copied.
    """
    if (not isinstance(expected_sha256, str)
            or re.fullmatch(r"[a-f0-9]{64}", expected_sha256) is None):
        raise ValueError("reviewed SHA-256 required")
    item = choose(task_kind)
    raw = _read_skill(ROOT / item["skill_path"], item["recommended_skill"])
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise ValueError("reviewed skill digest mismatch")
    root = Path(workspace).absolute()
    if (".." in root.parts
            or any(p.is_symlink() or (p / ".git").exists() for p in (root, *root.parents))
            or not root.is_dir() or root.stat().st_uid != os.getuid()
            or root.stat().st_mode & 0o077 or any(root.iterdir())):
        raise ValueError("empty private operator workspace outside a Git tree required")
    parent = root
    created = []
    target = None
    try:
        for component in (".agents", "skills", item["recommended_skill"]):
            parent = parent / component
            parent.mkdir(mode=0o700, exist_ok=False)
            created.append(parent)
        target = parent / "SKILL.md"
        with target.open("xb") as stream:
            if stream.write(raw) != len(raw):
                raise OSError("incomplete skill staging write")
        target.chmod(0o600)
    except BaseException:
        # Under the required exclusive operator-owned workspace assumption,
        # roll back only our known leaf and newly created empty directories.
        # Never recursively delete or erase unrelated entries.
        try:
            if target is not None:
                target.unlink(missing_ok=True)
            for directory in reversed(created):
                directory.rmdir()
        except OSError as exc:
            raise OSError("skill staging cleanup unverified; operator review required") from exc
        raise
    return {
        "task_kind": task_kind,
        "skill_path": str(target.relative_to(root)),
        "sha256": digest,
        "status": "REVIEW_ONLY_STAGED",
        "required_environment": {
            "OH_PUBLIC_SKILLS_ENABLED": "false",
            "OH_PUBLIC_CATALOG_ENABLED": "false",
        },
        "isolated_home_required": True,
        "runtime_invoked": False,
        "execution_authorized": False,
        "paid_calls_authorized": False,
        "release_authorized": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Read-only CODEN Agent Skill suggestions")
    parser.add_argument("--task", choices=sorted(SKILLS),
                        help="Known factory task type, e.g. sandbox or recovery")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        results = choose(args.task) if args.task else load()
    except (ValueError, OSError, TypeError, KeyError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"CODEN skill catalog BLOCKED ({type(exc).__name__})\n")
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True))
    elif args.task:
        print(f"Use {results['recommended_skill']} at {results['skill_path']}")
        print("Review-only advice. No skill execution, installation, paid calls or release.")
    else:
        for item in results:
            print(f"{item['task_kind']}: {item['name']} — {item['status']}")
        print("Six portable Agent Skills; zero runtime activations or installs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
