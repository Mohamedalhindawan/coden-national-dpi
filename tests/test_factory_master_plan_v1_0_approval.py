"""Regression contract for Founder-approved CODEN AI Factory v1.0 plan.

Founder approval validates the internal PLAN, never operational readiness,
commercial licensing, Government/SFD authorization, or automatic GitHub merges.
"""
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs/CODEN_AI_FACTORY_MASTER_PLAN_v1.0_APPROVED.md"
DECISION = ROOT / "docs/decisions/CODEN_FACTORY_V1_0_FOUNDER_APPROVAL.md"
MANIFEST = ROOT / "configs/coden_factory_master_plan_v1_0_baseline.json"
LOCKED_BLOB = "3476b956555db136dbc4bc41b78d93ac881b10f1"


class FounderApprovedFactoryPlanTests(unittest.TestCase):
    def test_80_sections_26_parts_and_unchanged_frozen_baseline(self):
        raw = PLAN.read_bytes()
        git_blob = hashlib.sha1(
            b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
        ).hexdigest()
        self.assertEqual(git_blob, LOCKED_BLOB)
        text = raw.decode("utf-8")
        section_numbers = [int(n) for n in re.findall(r"^### (\d+)\. ", text, re.M)]
        self.assertEqual(section_numbers, list(range(1, 81)))
        self.assertEqual(len(re.findall(r"^## الجزء ", text, re.M)), 26)
        self.assertIn("v1.0 — Integrated Implementation Master Plan", text)
        self.assertIn("المهندس/ محمد الهندوان", text)
        self.assertIn("FOUNDER-APPROVED INTERNAL BASELINE", text)
        self.assertIn("سبعة", text)
        self.assertIn("ثماني طبقات", text)
        self.assertIn("YDS — **الخدمة الرقمية اليمنية**", text)

    def test_signed_off_internal_decision_does_not_grant_runtime_approval(self):
        text = DECISION.read_text(encoding="utf-8")
        self.assertIn("2026-11-23", text)
        self.assertIn("v1.0", text)
        self.assertIn(LOCKED_BLOB, text)
        self.assertIn("المهندس/ محمد الهندوان", text)
        self.assertIn("Founder approved", text)
        self.assertIn("human review", text.lower())
        self.assertIn("not production approval", text.lower())
        self.assertIn("Draft PR", text)

    def test_machine_readable_contract_keeps_80_sections_unapproved_runtime(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["document_id"], "CODEN-AI-FACTORY-IMP-v1.0")
        self.assertEqual(data["version"], "1.0")
        self.assertEqual(data["owner_approval_date"], "2026-11-23")
        self.assertEqual(data["document_git_blob_sha1"], LOCKED_BLOB)
        self.assertEqual(data["numbered_sections"], 80)
        self.assertEqual(data["parts"], 26)
        self.assertEqual(data["technical_layers"], 8)
        self.assertEqual(data["institutional_engines"], 7)
        self.assertEqual(data["status"], "FOUNDER_APPROVED_INTERNAL_PLAN")
        self.assertFalse(data["production_approved"])
        self.assertFalse(data["github_merge_approved"])
        self.assertFalse(data["automatic_deployment_authorized"])
        self.assertFalse(data["paid_usage_authorized"])
        self.assertEqual(data["change_policy"], "new_version_required")

    def test_agents_and_readme_link_to_reference_without_overclaiming(self):
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        expected = "docs/CODEN_AI_FACTORY_MASTER_PLAN_v1.0_APPROVED.md"
        self.assertIn(expected, agents)
        self.assertIn(expected, readme)
        self.assertIn("does not authorize production", agents.lower())
        self.assertIn("no production approval", readme.lower())


if __name__ == "__main__":
    unittest.main()
