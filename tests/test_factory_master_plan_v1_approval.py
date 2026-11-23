"""Regressions for the founder-approved, frozen CODEN AI Factory plan v1.0.

Document approval is not production or third-party governmental approval.
No runtime privileges are created by these tests.
"""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs/CODEN_AI_FACTORY_MASTER_PLAN_v1.0_APPROVED.md"
RECORD = ROOT / "docs/decisions/ADR-FACTORY-001-PLAN-V1-APPROVAL.json"


class ApprovedFactoryPlanV1Tests(unittest.TestCase):
    def test_80_ordered_sections_26_parts_and_original_scope(self):
        text = PLAN.read_text(encoding="utf-8")
        sections = [int(n) for n in re.findall(r"(?m)^### (\d+)\. ", text)]
        self.assertEqual(sections, list(range(1, 81)))
        self.assertEqual(len(re.findall(r"(?m)^## الجزء ", text)), 26)
        self.assertIn("v1.0 — Integrated Implementation Master Plan", text)
        self.assertIn("المحركات المؤسسية السبعة", text)
        self.assertIn("ثماني طبقات تقنية مترابطة", text)
        self.assertIn("المهندس/ محمد الهندوان", text)
        self.assertIn("FOUNDER-APPROVED INTERNAL BASELINE", text)
        self.assertIn("FROZEN", text)
        self.assertIn("OpenHands", text)
        self.assertIn("Human Approval", text)
        self.assertIn("CODEN Factory Self-Development Pilot", text)
        self.assertIn("YDS", text)
        self.assertIn("الخدمة الرقمية اليمنية", text)

    def test_decision_is_internal_only_never_runtime_approval(self):
        record = json.loads(RECORD.read_text(encoding="utf-8"))
        self.assertEqual(record["decision_id"], "ADR-FACTORY-001")
        self.assertEqual(record["version"], "v1.0")
        self.assertEqual(record["date"], "2026-11-23")
        self.assertEqual(record["decision_type"], "founder_approval_of_internal_plan_only")
        self.assertEqual(record["status"], "FOUNDER_APPROVED_FROZEN")
        self.assertEqual(record["sections"], 80)
        self.assertEqual(record["parts"], 26)
        self.assertEqual(record["plan_path"], str(PLAN.relative_to(ROOT)))
        self.assertIs(record["github_main_merge_authorized"], False)
        self.assertIs(record["factory_production_authorized"], False)
        self.assertIs(record["externally_approved_by_sfd_or_government"], False)
        self.assertIs(record["paid_spend_authorized"], False)
        self.assertIs(record["automatic_security_policy_change_authorized"], False)
        self.assertIs(record["approved_openhands_execution"], False)
        self.assertIn("v1.1", record["revision_policy"])

    def test_repo_home_and_agent_rules_reference_locked_authority(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        path = "docs/CODEN_AI_FACTORY_MASTER_PLAN_v1.0_APPROVED.md"
        self.assertIn(path, readme)
        self.assertIn(path, agents)
        self.assertIn("ADR-FACTORY-001", agents)
        self.assertIn("internal", agents.lower())
        self.assertIn("not", agents.lower())

    def test_no_automatic_grant_from_an_approved_document(self):
        record = json.loads(RECORD.read_text(encoding="utf-8"))
        self.assertEqual(record["seven_enterprise_engines_preserved"], True)
        self.assertEqual(record["eight_technical_layers_preserved"], True)
        self.assertEqual(record["changes_to_code_or_runtime"], False)
        self.assertNotIn("PRODUCTION APPROVED", PLAN.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
