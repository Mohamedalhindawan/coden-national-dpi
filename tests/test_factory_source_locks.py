"""Fail-closed, offline acceptance tests for CODEN's *candidate* immutable source locks.

A pinned upstream commit is NOT a license/security admission or install grant.
"""
import copy
import json
import hashlib
import tempfile
from pathlib import Path
import re
import unittest

from ai_factory import factory_source_locks

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "configs" / "factory_72_adopt_first.json"
LOCKS = ROOT / "configs" / "factory_critical_source_pins_v0_1.json"
EXPECTED = {"source-001", "source-002", "source-003", "source-004",
            "source-005", "source-009", "source-011", "source-012",
            "source-013", "source-015", "source-018"}


class FactoryCandidatePinsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads(SOURCE.read_text(encoding="utf-8"))
        cls.locks = json.loads(LOCKS.read_text(encoding="utf-8"))
        cls.rows = factory_source_locks.validate(cls.locks, cls.original)

    def test_all_critical_sources_have_real_upstream_snapshots(self):
        self.assertEqual({x["source_id"] for x in self.rows}, EXPECTED)
        self.assertEqual(len(self.rows), 11)
        self.assertEqual(len({x["repo"] for x in self.rows}), 6)
        self.assertEqual(self.locks["status"], "candidate_snapshots_only")
        self.assertFalse(self.locks["auto_install"])
        self.assertFalse(self.locks["enable_runtime"])
        self.assertFalse(self.locks["allow_paid_models"])
        self.assertFalse(self.locks["authorize_release"])

    def test_no_mutable_revisions_and_all_pinned_files_are_blob_verified(self):
        for item in self.rows:
            with self.subTest(source=item["source_id"]):
                commit = item["commit_sha"]
                self.assertRegex(commit, r"^[0-9a-f]{40}$")
                self.assertRegex(item["blob_sha"], r"^[0-9a-f]{40}$")
                self.assertEqual(item["immutable_url"],
                    "https://github.com/" + item["repo"] + "/blob/" + commit + "/" + item["evidence_path"])
                self.assertNotIn("HEAD", item["immutable_url"])
                self.assertNotIn("main/", item["immutable_url"])
                self.assertEqual(item["source_verified"], "github_api_revision_and_blob_metadata")
                self.assertFalse(item["approved_for_install"])
                self.assertFalse(item["runtime_enabled"])
                self.assertEqual(item["security_review"], "pending")
                self.assertEqual(item["license_review"], "pending")
                self.assertEqual(item["dependency_review"], "pending")

    def test_registry_exact_repo_names_and_paths_match(self):
        baseline = {x["id"]: x for x in self.original["candidates"]}
        for row in self.rows:
            old = baseline[row["source_id"]]
            self.assertEqual(row["repo"], old["upstream_repo"])
            if "/blob/HEAD/" in old["source_url"]:
                self.assertEqual(row["evidence_path"], old["source_url"].split("/blob/HEAD/", 1)[1])

    def test_reject_unauthorized_or_unpinned_approval_mutations(self):
        for field in ("auto_install", "enable_runtime", "allow_paid_models", "authorize_release"):
            altered = copy.deepcopy(self.locks)
            altered[field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                factory_source_locks.validate(altered, self.original)
        for key, value in (
            ("commit_sha", "main"), ("commit_sha", "f" * 39),
            ("blob_sha", None), ("approved_for_install", True),
            ("runtime_enabled", True), ("license_review", "approved"),
            ("security_review", "approved"), ("dependency_review", "approved"),
        ):
            altered = copy.deepcopy(self.locks)
            altered["sources"][0][key] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                factory_source_locks.validate(altered, self.original)

    def test_reject_changing_evidence_source_or_duplicate_repo_commit(self):
        bad = copy.deepcopy(self.locks)
        bad["sources"][0]["repo"] = "malicious/fork"
        with self.assertRaises(ValueError):
            factory_source_locks.validate(bad, self.original)
        bad = copy.deepcopy(self.locks)
        bad["sources"][0]["evidence_path"] = "../../LICENSE"
        with self.assertRaises(ValueError):
            factory_source_locks.validate(bad, self.original)
        bad = copy.deepcopy(self.locks)
        bad["sources"][0]["immutable_url"] = "https://evil.com/scripts/install.sh"
        with self.assertRaises(ValueError):
            factory_source_locks.validate(bad, self.original)
        bad = copy.deepcopy(self.locks)
        bad["sources"][1]["commit_sha"] = "a" * 40
        with self.assertRaises(ValueError):
            factory_source_locks.validate(bad, self.original)

    def test_query_is_read_only_subset_and_not_runtime(self):
        one = factory_source_locks.select(self.rows, source_id="source-001")
        self.assertEqual(len(one), 1)
        self.assertEqual(one[0]["repo"], "OpenHands/software-agent-sdk")
        self.assertFalse(one[0]["runtime_enabled"])
        with self.assertRaises(ValueError):
            factory_source_locks.select(self.rows, source_id="source-999")


    def test_staged_file_git_blob_hash_matches_record_and_reports_sha256(self):
        payload = b"safe synthetic source text for integrity check\n"
        blob = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "source.txt"
            file.write_bytes(payload)
            result = factory_source_locks.verify_staged_blob(file, blob)
            self.assertEqual(result["git_blob_sha1"], blob)
            self.assertEqual(result["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(result["size_bytes"], len(payload))
            file.write_bytes(payload + b"# tampering")
            with self.assertRaises(ValueError):
                factory_source_locks.verify_staged_blob(file, blob)

    def test_staged_file_blocks_symlinks_and_oversize_inputs(self):
        payload = b"safe"
        blob = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            file = root / "source.txt"
            file.write_bytes(payload)
            alias = root / "alias"
            alias.symlink_to(file)
            with self.assertRaises(ValueError):
                factory_source_locks.verify_staged_blob(alias, blob)
            with self.assertRaises(ValueError):
                factory_source_locks.verify_staged_blob(root, blob)
            with self.assertRaises(ValueError):
                factory_source_locks.verify_staged_blob(file, blob, max_bytes=2)


if __name__ == "__main__":
    unittest.main()
