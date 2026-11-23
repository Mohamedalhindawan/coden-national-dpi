"""Batch 0: test-first, offline real Spec Kit source reuse (review-only).

The original GitHub Spec Kit templates are adopted as byte-identical MIT
licensed source assets. This never runs third-party code or approves a source.
"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from ai_factory import spec_kit_pilot
from ai_factory.factory_source_locks import load as load_locks, verify_staged_blob


class SpecKitPilotTests(unittest.TestCase):
    def test_three_original_upstream_templates_match_immutable_locks(self):
        locks = {row["source_id"]: row for row in load_locks()}
        self.assertEqual(set(spec_kit_pilot.TEMPLATES),
                         {"source-011", "source-012", "source-013"})
        for source_id, name in spec_kit_pilot.TEMPLATES.items():
            with self.subTest(source=source_id):
                lock = locks[source_id]
                self.assertEqual(lock["repo"], "github/spec-kit")
                self.assertEqual(lock["commit_sha"], spec_kit_pilot.SPEC_KIT_COMMIT)
                staged = spec_kit_pilot.ASSETS / name
                proof = verify_staged_blob(staged, lock["blob_sha"])
                self.assertFalse(proof["install_authorized"])
                self.assertGreater(proof["size_bytes"], 0)
        license_proof = verify_staged_blob(
            spec_kit_pilot.ASSETS / "LICENSE",
            spec_kit_pilot.LICENSE_BLOB_SHA,
        )
        self.assertGreater(license_proof["size_bytes"], 0)

    def test_real_staged_documents_keep_original_bytes_and_attribution(self):
        with TemporaryDirectory() as temp:
            out = Path(temp) / "review-only"
            receipt = spec_kit_pilot.stage(out)
            self.assertEqual(receipt["status"], "awaiting_human_review")
            self.assertFalse(receipt["release_authorized"])
            self.assertFalse(receipt["runtime_enabled"])
            self.assertEqual(receipt["paid_calls"], 0)
            self.assertEqual(receipt["upstream_commit"], spec_kit_pilot.SPEC_KIT_COMMIT)
            self.assertEqual(len(receipt["sources"]), 3)
            for source_id, template in spec_kit_pilot.TEMPLATES.items():
                destination = spec_kit_pilot.OUTPUT_NAMES[source_id]
                self.assertEqual(
                    (out / destination).read_bytes(),
                    (spec_kit_pilot.ASSETS / template).read_bytes(),
                )
            self.assertEqual((out / "LICENSE").read_bytes(),
                             (spec_kit_pilot.ASSETS / "LICENSE").read_bytes())
            self.assertEqual(
                json.loads((out / "evidence.json").read_text(encoding="utf-8")),
                receipt,
            )
            self.assertEqual(sorted(p.name for p in out.iterdir()),
                             ["LICENSE", "evidence.json", "plan.md", "spec.md", "tasks.md"])

    def test_rejects_existing_destination_and_symlink_parent(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            existing = root / "existing"
            existing.mkdir()
            with self.assertRaises(ValueError):
                spec_kit_pilot.stage(existing)
            symlink = root / "alias"
            symlink.symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError):
                spec_kit_pilot.stage(symlink / "output")
            self.assertFalse((root / "output").exists())

    def test_corrupted_upstream_template_or_license_fail_closed(self):
        with TemporaryDirectory() as temp:
            fake = Path(temp) / "sources"
            fake.mkdir()
            for name in (*spec_kit_pilot.TEMPLATES.values(), "LICENSE"):
                (fake / name).write_bytes((spec_kit_pilot.ASSETS / name).read_bytes())
            (fake / "plan-template.md").write_text("UNTRUSTED MODIFICATION", encoding="utf-8")
            with patch.object(spec_kit_pilot, "ASSETS", fake):
                with self.assertRaises(ValueError):
                    spec_kit_pilot.stage(Path(temp) / "broken")
            self.assertFalse((Path(temp) / "broken").exists())
            (fake / "plan-template.md").write_bytes(
                (spec_kit_pilot.ASSETS / "plan-template.md").read_bytes()
            )
            (fake / "LICENSE").write_text("removed attribution", encoding="utf-8")
            with patch.object(spec_kit_pilot, "ASSETS", fake):
                with self.assertRaises(ValueError):
                    spec_kit_pilot.stage(Path(temp) / "missing-license")
            self.assertFalse((Path(temp) / "missing-license").exists())

    def test_symlink_source_rejected(self):
        with TemporaryDirectory() as temp:
            fake = Path(temp) / "sources"
            fake.mkdir()
            for name in (*spec_kit_pilot.TEMPLATES.values(), "LICENSE"):
                (fake / name).write_bytes((spec_kit_pilot.ASSETS / name).read_bytes())
            (fake / "tasks-template.md").unlink()
            (fake / "tasks-template.md").symlink_to(spec_kit_pilot.ASSETS / "tasks-template.md")
            with patch.object(spec_kit_pilot, "ASSETS", fake):
                with self.assertRaises(ValueError):
                    spec_kit_pilot.stage(Path(temp) / "bad")
            self.assertFalse((Path(temp) / "bad").exists())


if __name__ == "__main__":
    unittest.main()
