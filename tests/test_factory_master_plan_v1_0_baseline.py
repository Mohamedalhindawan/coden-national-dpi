"""CODEN Factory Founder-approved v1.0 document baseline integrity check.

Approval here is ONLY of the internal plan's content and direction, not a
production readiness claim, a GitHub branch merge, or state approval of tools.
"""
import hashlib
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "CODEN_AI_FACTORY_MASTER_PLAN_v1.0_APPROVED.md"
ADR = ROOT / "docs" / "decisions" / "ADR-FACTORY-MASTER-PLAN-v1.0-2026-11-23.md"
LOCKED_GIT_BLOB = "3476b956555db136dbc4bc41b78d93ac881b10f1"


class FactoryMasterPlanApprovalBaselineTests(unittest.TestCase):
    def test_all_80_sections_and_26_parts_are_present_in_exact_sequence(self):
        text = PLAN.read_text(encoding="utf-8")
        sections = [int(i) for i in re.findall(r"^### (\d+)\. ", text, re.M)]
        self.assertEqual(sections, list(range(1, 81)))
        self.assertEqual(len(re.findall(r"^## الجزء ", text, re.M)), 26)
        self.assertIn("Integrated Implementation Master Plan", text)
        self.assertIn("23 نوفمبر 2026", text)
        self.assertIn("المهندس/ محمد الهندوان", text)
        self.assertIn("FOUNDER-APPROVED INTERNAL BASELINE", text)
        self.assertIn("Open Source First", text)
        self.assertIn("Human-Governed", text)
        self.assertIn("الخدمة الرقمية اليمنية", text)

    def test_plan_is_immutable_reviewable_github_blob(self):
        raw = PLAN.read_bytes()
        actual = hashlib.sha1(
            b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
        ).hexdigest()
        self.assertEqual(actual, LOCKED_GIT_BLOB)
        self.assertIn("3476b956555db136dbc4bc41b78d93ac881b10f1", ADR.read_text())

    def test_approval_scope_does_not_authorize_production_or_merge(self):
        text = PLAN.read_text(encoding="utf-8")
        adr = ADR.read_text(encoding="utf-8")
        self.assertIn("غير معتمدة رسمياً", text)
        self.assertIn("لا تمثل إعلان اكتمال تنفيذ المصنع", text)
        self.assertIn("Human Approval", text)
        self.assertIn("لا يتم الدمج أو النشر للإنتاج", text)
        self.assertIn("FOUNDERS_APPROVED_INTERNAL_PLAN", adr)
        self.assertIn("plan_only", adr)
        self.assertIn("not a production authorization", adr.lower())
        self.assertIn("main", adr)
        self.assertIn("v1.1", adr)
        self.assertIn("26", adr)
        self.assertIn("80", adr)

    def test_project_entrypoints_link_this_exact_frozen_plan(self):
        for path in (ROOT / "README.md", ROOT / "AGENTS.md"):
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertIn("CODEN_AI_FACTORY_MASTER_PLAN_v1.0_APPROVED.md", text)
                self.assertIn("Founder-approved", text)
                self.assertIn("not production", text.lower())


if __name__ == "__main__":
    unittest.main()
