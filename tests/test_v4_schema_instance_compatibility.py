"""Fail-closed regression checks for issue #55 schema/instance reconciliation.

This does not claim that YAML registries conform to enterprise JSON Schemas.
"""
import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "enterprise/governance/v4-schema-instance-compatibility.json"


def approval_url_is_scoped(value):
    """Require a canonical PR link in this repository; not proof of approval."""
    if not isinstance(value, str):
        return False
    try:
        parts = urlsplit(value)
    except ValueError:
        return False
    segments = parts.path.split("/")[1:]
    return (parts.scheme == "https" and parts.netloc == "github.com"
            and not parts.query and not parts.fragment
            and not parts.username and not parts.password
            and parts.port is None
            and len(segments) == 4
            and segments[:3] == ["Mohamedalhindawan", "coden-national-dpi", "pull"]
            and segments[3].isascii() and segments[3].isdecimal()
            and int(segments[3]) > 0)


def migration_allowed(entry):
    """Fail closed unless a complete mapping has attributable human approval.

    This predicate is a necessary gate, not proof of YAML/JSON Schema conformance.
    """
    if not isinstance(entry, dict):
        return False
    mapping = entry.get("field_map")
    missing = entry.get("required_missing")
    unmapped = entry.get("unmapped_values")
    return (
        entry.get("migration") == "approved"
        and isinstance(entry.get("approved_by"), str)
        and bool(entry["approved_by"].strip())
        and isinstance(entry.get("approval_evidence_url"), str)
        and approval_url_is_scoped(entry["approval_evidence_url"])
        and isinstance(entry.get("schema"), str)
        and bool(entry["schema"].strip())
        and isinstance(entry.get("registry"), str)
        and bool(entry["registry"].strip())
        and isinstance(missing, list)
        and not missing
        and isinstance(unmapped, dict)
        and not unmapped
        and isinstance(mapping, dict)
        and bool(mapping)
        and all(isinstance(v, str) and bool(v.strip()) for v in mapping.values())
    )

class SchemaInstanceCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MAPPING.read_text(encoding="utf-8"))

    def test_scope_and_draft_status(self):
        self.assertEqual(self.manifest["issue"], 55)
        self.assertEqual(self.manifest["status"], "draft")
        self.assertEqual(set(self.manifest["source_prs"]), {43, 44, 46, 51, 53})

    def test_contracts_are_not_claimed_compatible(self):
        for name in ("risk", "kpi"):
            with self.subTest(contract=name):
                self.assertFalse(migration_allowed(self.manifest["contracts"][name]))
                self.assertEqual(
                    self.manifest["contracts"][name]["migration"],
                    "blocked_pending_human_mapping",
                )

    def test_risk_required_fields_are_explicitly_missing(self):
        risk = self.manifest["contracts"]["risk"]
        self.assertTrue({"initiative_id", "likelihood", "impact", "identified_at"}
                        <= set(risk["required_missing"]))
        self.assertIsNone(risk["field_map"]["status"])
        self.assertIsNone(risk["field_map"]["owner"])
        self.assertIsNone(risk["field_map"]["severity"])

    def test_kpi_missing_contract_fields_are_explicit(self):
        kpi = self.manifest["contracts"]["kpi"]
        self.assertTrue({"objective_id", "unit", "direction", "status", "created_at"}
                        <= set(kpi["required_missing"]))
        self.assertIn("observed_value", kpi["template_only"])
        self.assertEqual(kpi["measurement_pr"], 44)

    def test_approval_flag_alone_cannot_bypass_missing_fields(self):
        for name in ("risk", "kpi"):
            with self.subTest(contract=name):
                record = dict(self.manifest["contracts"][name], migration="approved")
                self.assertFalse(migration_allowed(record))

    def test_complete_reviewed_mapping_can_pass_predicate(self):
        record = {"migration": "approved", "required_missing": [],
                  "unmapped_values": {}, "field_map": {"id": "risk_id"},
                  "schema": "schemas/risk.json", "registry": "enterprise/risk.yaml",
                  "approved_by": "human-reviewer",
                  "approval_evidence_url": "https://github.com/Mohamedalhindawan/coden-national-dpi/pull/76"}
        self.assertTrue(migration_allowed(record))
        record["field_map"]["status"] = None
        self.assertFalse(migration_allowed(record))


    def test_missing_approval_or_malformed_mapping_is_rejected(self):
        valid = {"migration": "approved", "required_missing": [],
                 "unmapped_values": {}, "field_map": {"id": "risk_id"},
                 "schema": "schemas/risk.json", "registry": "enterprise/risk.yaml",
                 "approved_by": "human-reviewer",
                 "approval_evidence_url": "https://github.com/example/repo/pull/1"}
        for field, value in (("approved_by", ""), ("approval_evidence_url", "http://example.org"),
                             ("field_map", {}), ("required_missing", None),
                             ("unmapped_values", None), ("schema", ""), ("registry", "")):
            with self.subTest(field=field):
                self.assertFalse(migration_allowed(dict(valid, **{field: value})))
        self.assertFalse(migration_allowed(None))
        self.assertFalse(migration_allowed([]))


    def test_approval_url_scope_rejects_untrusted_or_ambiguous_links(self):
        for url in ("https://github.com/example/repo/pull/1",
                    "https://github.com/Mohamedalhindawan/coden-national-dpi/issues/55",
                    "https://github.com/Mohamedalhindawan/coden-national-dpi/pull/76?x=1",
                    "https://github.com/Mohamedalhindawan/coden-national-dpi/pull/76#review",
                    "https://github.com/Mohamedalhindawan/coden-national-dpi/pull/not-a-number",
                    "https://github.com.evil.test/Mohamedalhindawan/coden-national-dpi/pull/76",
                    "https://github.com/Mohamedalhindawan/coden-national-dpi/pull/0",
                    "https://github.com/Mohamedalhindawan/coden-national-dpi/pull/76/",
                    "https://github.com/Mohamedalhindawan/coden-national-dpi/pull/76//",
                    "https://github.com/Mohamedalhindawan/coden-national-dpi/pull/76%2F",
                    None):
            with self.subTest(url=url):
                self.assertFalse(approval_url_is_scoped(url))
        self.assertTrue(approval_url_is_scoped(
            "https://github.com/Mohamedalhindawan/coden-national-dpi/pull/76"))

if __name__ == "__main__":
    unittest.main()
