import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = ROOT / "skills"
REGISTRY = SKILLS_ROOT / "registry.yaml"
REQUIRED_HEADINGS = (
    "## Purpose", "## Scope", "## Required inputs", "## Workflow",
    "## Deliverables", "## Quality gates", "## Security",
    "## Evaluation", "## Failure and escalation", "## Change history",
)

class SkillsLibraryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = REGISTRY.read_text(encoding="utf-8")
        cls.entries = []
        for block in re.split(r"(?m)^  - id: ", cls.text)[1:]:
            skill_id = block.splitlines()[0].strip()
            path = re.search(r"(?m)^    path: (.+)$", block)
            status = re.search(r"(?m)^    status: (.+)$", block)
            cls.entries.append((skill_id, path.group(1).strip() if path else None,
                                status.group(1).strip() if status else None))

    def test_expected_skill_count(self):
        self.assertEqual(len(self.entries), 60, "Registry must contain exactly 60 skills")

    def test_registry_has_unique_ids(self):
        ids = [entry[0] for entry in self.entries]
        self.assertTrue(ids, "No skills registered")
        self.assertEqual(len(ids), len(set(ids)), "Duplicate skill IDs found")

    def test_registry_paths_exist(self):
        missing = [path for _, path, _ in self.entries
                   if not path or not (SKILLS_ROOT / path).is_file()]
        self.assertEqual(missing, [], f"Missing skill files: {missing}")

    def test_every_skill_has_required_sections(self):
        failures = []
        for skill_id, path, _ in self.entries:
            if not path or not (SKILLS_ROOT / path).is_file():
                failures.append(f"{skill_id}: file missing")
                continue
            content = (SKILLS_ROOT / path).read_text(encoding="utf-8")
            missing = [heading for heading in REQUIRED_HEADINGS if heading not in content]
            if missing:
                failures.append(f"{skill_id}: {', '.join(missing)}")
        self.assertEqual(failures, [], "\\n".join(failures))

    def test_pilot_benchmark_cases_exist_and_are_synthetic(self):
        pilot = SKILLS_ROOT / "validation" / "pilot"
        expected = ("PRD-01-T01.md", "DPI-02-T01.md", "AI-01-T01.md",
                    "SEC-02-T01.md", "QA-01-T01.md")
        missing = [name for name in expected if not (pilot / name).is_file()]
        self.assertEqual(missing, [], f"Missing pilot cases: {missing}")
        for name in expected:
            case = (pilot / name).read_text(encoding="utf-8").lower()
            self.assertIn("synthetic", case, f"{name} must explicitly use synthetic data")

    def test_all_skills_remain_draft_until_approved(self):
        invalid = [(skill_id, status) for skill_id, _, status in self.entries if status != "draft"]
        self.assertEqual(invalid, [], f"Unexpected lifecycle statuses: {invalid}")

if __name__ == "__main__":
    unittest.main()
