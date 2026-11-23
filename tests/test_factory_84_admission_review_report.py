"""TDD contract: safe real 84-source review report + QUARANTINED Qwen output.

The unapproved model code is treated as inert provenance, never imported or run
by the factory report. The existing catalog must remain read-only.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from ai_factory import factory_84_registry
from ai_factory import factory_84_admission_report as admission

SRC_SHA = "c410f3e98b7e01e9208954da558cd6b94ee22fc0fe5fa04fa3a1027db401f9cc"
PYZ_SHA = "e011e317dc06efb6870978d40e4d17263a308c30655a565518006af23b564573"


class Real84AdmissionReviewReportTests(unittest.TestCase):
    def test_real_catalog_has_84_pending_license_and_84_pending_security(self):
        before = factory_84_registry.load()
        snapshot = copy.deepcopy(before)
        report = admission.build_report()
        self.assertEqual(before, snapshot)
        self.assertEqual(report["source_entries"], 84)
        self.assertEqual(report["unique_upstream_repositories"], 76)
        self.assertEqual(report["source_approval_pending"], 84)
        self.assertEqual(report["license_review_pending"], 84)
        self.assertEqual(report["security_review_pending"], 84)
        self.assertEqual(report["review_checks_pending"], 168)
        self.assertEqual(report["by_priority"], {
            "P0": {"sources": 26, "pending_checks": 52},
            "P1": {"sources": 39, "pending_checks": 78},
            "P2": {"sources": 19, "pending_checks": 38},
        })
        self.assertFalse(report["release_authorized"])
        self.assertFalse(report["source_catalog_modified"])
        self.assertFalse(report["model_candidate_executed_by_report"])
        self.assertEqual(report["paid_calls"], 0)
        self.assertEqual(len(report["rows"]), 84)
        self.assertTrue(all(item["pending_flags"] == [
            "license_pending", "security_pending"
        ] for item in report["rows"]))
        self.assertEqual(report["model_candidate_pyzip_sha256"], PYZ_SHA)

    def test_quarantined_real_generated_source_exact_hash_and_safe_ast(self):
        code = admission.CANDIDATE_PATH.read_bytes()
        self.assertEqual(hashlib.sha256(code).hexdigest(), SRC_SHA)
        self.assertEqual(admission.CANDIDATE_SOURCE_SHA256, SRC_SHA)
        ast_root = ast.parse(code.decode("utf-8"))
        self.assertEqual(len(ast_root.body), 1)
        self.assertIsInstance(ast_root.body[0], ast.FunctionDef)
        self.assertEqual(ast_root.body[0].name, "transform")
        self.assertFalse(any(isinstance(node, (
            ast.Import, ast.ImportFrom, ast.Call, ast.While, ast.With, ast.Try,
            ast.Global, ast.Nonlocal,
        )) for node in ast.walk(ast_root)))
        self.assertIn("elif flag == 'security_pending'", code.decode("utf-8"))
        report = admission.build_report()
        self.assertEqual(report["candidate_source_sha256"], SRC_SHA)
        self.assertEqual(report["candidate_status"], "awaiting_human_review")

    def test_does_not_allow_laundering_approval_or_changed_review_fields(self):
        base = factory_84_registry.load()
        bad = [
            {"license_review": "approved"},
            {"security_review": "passed"},
            {"approved": True},
            {"enabled": True},
            {"installed": True},
            {"admission": "active"},
            {"pinned_commit": "0" * 40},
            {"source_url": "https://example.org"},
        ]
        for mutation in bad:
            with self.subTest(mutation=mutation):
                rows = copy.deepcopy(base)
                rows[0].update(mutation)
                with patch.object(admission.factory_84_registry, "load",
                                  return_value=rows):
                    with self.assertRaises(ValueError):
                        admission.build_report()

    def test_missing_duplicate_and_extra_sources_fail_closed(self):
        base = factory_84_registry.load()
        for bad in (base[:-1], base + [copy.deepcopy(base[0])]):
            with patch.object(admission.factory_84_registry, "load",
                              return_value=bad):
                with self.assertRaises(ValueError):
                    admission.build_report()
        altered = copy.deepcopy(base)
        altered[1]["id"] = altered[0]["id"]
        with patch.object(admission.factory_84_registry, "load",
                          return_value=altered):
            with self.assertRaises(ValueError):
                admission.build_report()

    def test_source_tampering_is_detected_without_executing_model_code(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as td:
            altered = Path(td) / "candidate.py"
            altered.write_text("def transform(value):\n    return 1\n", encoding="utf-8")
            with patch.object(admission, "CANDIDATE_PATH", altered):
                with self.assertRaises(ValueError):
                    admission.build_report()

    def test_json_report_is_deterministic_and_no_release_or_provider_secrets(self):
        a = admission.build_report()
        b = admission.build_report()
        self.assertEqual(a, b)
        self.assertEqual(a["source"], "verified_84_source_adopt_first_registry")
        self.assertEqual(a["candidate_status"], "awaiting_human_review")
        self.assertEqual(a["metric_kind"], "read_only_source_review_backlog")
        self.assertNotIn("api_key", json.dumps(a).lower())
        self.assertNotIn("token", json.dumps(a).lower())
        self.assertEqual({row["id"] for row in a["rows"]},
                         {row["id"] for row in factory_84_registry.load()})


if __name__ == "__main__":
    unittest.main()
