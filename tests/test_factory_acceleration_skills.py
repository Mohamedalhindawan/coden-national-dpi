"""TDD contract for 6 portable, non-executing CODEN engineering skills.

Skills are text procedures discoverable by compatible agents; they do not
install, invoke, authorize, deploy or automatically merge any component.
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ai_factory import factory_skill_catalog

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "factory-batch-intake",
    "factory-tdd-multifile",
    "factory-sandbox-preflight",
    "factory-adopt-first-gate",
    "factory-independent-review",
    "factory-pr-stack-recovery",
}
TASKS = {
    "intake": "factory-batch-intake",
    "multifile": "factory-tdd-multifile",
    "sandbox": "factory-sandbox-preflight",
    "admission": "factory-adopt-first-gate",
    "review": "factory-independent-review",
    "recovery": "factory-pr-stack-recovery",
}


class FactoryAccelerationSkillsTests(unittest.TestCase):
    def test_6_actual_portable_skill_directories_are_discoverable(self):
        rows = factory_skill_catalog.load()
        self.assertEqual({row["name"] for row in rows}, EXPECTED)
        self.assertEqual(len(rows), 6)
        for row in rows:
            with self.subTest(name=row["name"]):
                path = ROOT / ".github" / "skills" / row["name"] / "SKILL.md"
                self.assertEqual(row["path"], str(path.relative_to(ROOT)))
                self.assertTrue(path.is_file())
                self.assertFalse(path.is_symlink())
                raw = path.read_text(encoding="utf-8")
                self.assertTrue(raw.startswith("---\n"))
                self.assertIn("\n---\n", raw)
                self.assertIn("name: " + row["name"], raw)
                self.assertIn("description:", raw)
                self.assertIn("Human review", raw)
                self.assertIn("no automatic merge", raw.lower())
                self.assertGreater(len(raw), 450)
                self.assertLess(len(raw), 7000)
                self.assertEqual(row["status"], "DRAFT_NOT_AUTO_ACTIVATED")
                self.assertFalse(row["installed_by_catalog"])
                self.assertFalse(row["runtime_invoked"])
                self.assertFalse(row["release_authorized"])

    def test_strict_task_matching_returns_one_relevant_skill_and_no_permission(self):
        for task, name in TASKS.items():
            with self.subTest(task=task):
                result = factory_skill_catalog.choose(task)
                self.assertEqual(result["task_kind"], task)
                self.assertEqual(result["recommended_skill"], name)
                self.assertFalse(result["execute_now"])
                self.assertFalse(result["release_authorized"])
                self.assertFalse(result["paid_calls_authorized"])
        with self.assertRaises(ValueError):
            factory_skill_catalog.choose("deploy")
        with self.assertRaises(ValueError):
            factory_skill_catalog.choose("../secrets")

    def test_manifest_and_skill_integrity_guards_fail_closed(self):
        manifest = json.loads(factory_skill_catalog.MANIFEST.read_text(encoding="utf-8"))
        bad = copy.deepcopy(manifest)
        bad["skills"][0]["name"] = bad["skills"][1]["name"]
        with self.assertRaises(ValueError):
            factory_skill_catalog.validate(bad)
        bad = copy.deepcopy(manifest)
        bad["skills"][0]["release_authorized"] = True
        with self.assertRaises(ValueError):
            factory_skill_catalog.validate(bad)
        bad = copy.deepcopy(manifest)
        bad["skills"][0]["path"] = "../../secrets"
        with self.assertRaises(ValueError):
            factory_skill_catalog.validate(bad)
        bad = copy.deepcopy(manifest)
        bad["skills"].pop()
        with self.assertRaises(ValueError):
            factory_skill_catalog.validate(bad)

    def test_skill_documents_have_actionable_and_safe_checklists(self):
        docs = {
            row["name"]: (ROOT / row["path"]).read_text(encoding="utf-8")
            for row in factory_skill_catalog.load()
        }
        self.assertIn("acceptance criteria", docs["factory-batch-intake"].lower())
        self.assertIn("hidden", docs["factory-tdd-multifile"].lower())
        self.assertIn("bubblewrap", docs["factory-sandbox-preflight"].lower())
        self.assertIn("cpu", docs["factory-sandbox-preflight"].lower())
        self.assertIn("sbom", docs["factory-adopt-first-gate"].lower())
        self.assertIn("sha-256", docs["factory-independent-review"].lower())
        self.assertIn("base branch", docs["factory-pr-stack-recovery"].lower())
        for text in docs.values():
            self.assertIn("do not claim", text.lower())
            self.assertIn("draft", text.lower())

    def test_quickstart_from_agent_instructions(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(".github/skills", agents)
        self.assertIn("factory_skill_catalog", agents)
        self.assertIn("not automatically installed", agents.lower())


if __name__ == "__main__":
    unittest.main()
