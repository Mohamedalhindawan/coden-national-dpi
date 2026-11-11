"""Verify the exact PR #43 KPI schema fixture is unchanged.

Source: PR #43, schemas/enterprise/kpi.schema.json,
Git blob 827d5a4d0299ca727be594c56130f1605353bd6a.
This offline guard detects accidental fixture edits; it cannot detect later
upstream branch changes and does not approve a canonical schema.
"""
import hashlib
import json
import unittest
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "kpi_pr43_schema_snapshot.json"
EXPECTED_BLOB = "827d5a4d0299ca727be594c56130f1605353bd6a"


class KpiFixtureIntegrityTests(unittest.TestCase):
    def test_fixture_matches_verified_pr43_git_blob(self):
        data = FIXTURE.read_bytes()
        git_blob = b"blob " + str(len(data)).encode("ascii") + b"\\0" + data
        self.assertEqual(hashlib.sha1(git_blob).hexdigest(), EXPECTED_BLOB)

    def test_fixture_declares_expected_draft_and_schema_identity(self):
        schema = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(
            schema["$schema"],
            "https://json-schema.org/draft/2020-12/schema",
        )
        self.assertEqual(
            schema["$id"],
            "https://coden.it.com/schemas/enterprise/kpi.schema.json",
        )


if __name__ == "__main__":
    unittest.main()
