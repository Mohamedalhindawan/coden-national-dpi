import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "skills" / "registry.yaml"
REQUIRED_HEADINGS = (
    "## Purpose",
    "## Scope",
    "## Required inputs",
    "## Workflow",
    "## Deliverables",
    "## Quality gates",
    "## Security",
    "## Evaluation",
    "## Failure and escalation",
    "## Change history",
)

class SkillsLibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = REGISTRY.read_text(encoding="utf-8")
        cls.entries = []
        blocks = re.split(r"(?m)^  - id: ", cls.text)[1:]
        for block in blocks:
            lines = block.splitlines()
            skill_id = lines[0].strip()
            path_match = re.search(r"(?m)^    path: (.+)$", block)
            status_match = re.search(r"(?m)^    status: (.+)$", block)
            cls.entries.append((skill_id, path_match.group(1).strip() if path_match else None,
                                status_match.group(1).strip() if status_match else None))

    def test_registry_has_unique_ids(self):
        ids = [entry[0] for entry in self.entries]
        self.assertTrue(ids, "No skills registered")
        self.assertEqual(len(ids), len(set(ids)), "Duplicate skill IDs found")

    def test_registry_paths_exist(self):
        missing = [path for _, path, _ in self.entries if not path or not (ROOT / path).is_file()]
        self.assertEqual(missing, [], f"Missing skill files: {missing}")

    def test_every_skill_has_required_sections(self):
        failures = []
        for skill_id, path, _ in self.entries:
            if not path or not (ROOT / path).is_file():
                continue
            content = (ROOT / path).read_text(encoding="utf-8")
            missing = [heading for heading in REQUIRED_HEADINGS if heading not in content]
            if missing:
                failures.append(f"{skill_id}: {', '.join(missing)}")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_draft_status_is_explicit(self):
        invalid = [(skill_id, status) for skill_id, _, status in self.entries if status != "draft"]
        self.assertEqual(invalid, [], f"Unexpected lifecycle statuses: {invalid}")

if __name__ == "__main__":
    unittest.main()
