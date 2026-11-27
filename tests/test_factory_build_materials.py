import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ai_factory import factory_build_materials as review


class BuildMaterialsTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.raw = b"synthetic only"
        self.pins = {"fixture.whl": (len(self.raw), hashlib.sha256(self.raw).hexdigest())}
        override = patch.object(review, "PINS", self.pins)
        override.start()
        self.addCleanup(override.stop)

    def test_exact_material_is_review_only(self):
        (self.root / "fixture.whl").write_bytes(self.raw)
        result = review.review_build_materials(self.root)
        self.assertTrue(result["pinned_materials_match"])
        self.assertEqual(result["matched"], 1)
        for key in ("build_authorized", "installation_authorized", "release_authorized", "source_tree_verified", "independent_review"):
            self.assertIs(result[key], False)

    def test_missing_wrong_size_or_digest(self):
        self.assertFalse(review.review_build_materials(self.root)["pinned_materials_match"])
        for raw in (b"x", b"x" * len(self.raw), self.raw + b"x"):
            with self.subTest(raw=raw):
                (self.root / "fixture.whl").write_bytes(raw)
                result = review.review_build_materials(self.root)
                self.assertFalse(result["pinned_materials_match"])
                self.assertEqual(result["matched"], 0)

    def test_reject_symlink_fifo_and_hardlink(self):
        original = self.root / "outside"
        original.write_bytes(self.raw)
        target = self.root / "fixture.whl"
        target.symlink_to(original)
        self.assertFalse(review.review_build_materials(self.root)["pinned_materials_match"])
        target.unlink()
        os.mkfifo(target)
        self.assertFalse(review.review_build_materials(self.root)["pinned_materials_match"])
        target.unlink()
        os.link(original, target)
        self.assertFalse(review.review_build_materials(self.root)["pinned_materials_match"])

    def test_reject_extra_material(self):
        (self.root / "fixture.whl").write_bytes(self.raw)
        (self.root / "unreviewed.whl").write_bytes(b"extra")
        result = review.review_build_materials(self.root)
        self.assertEqual(result["unexpected_entries"], 1)
        self.assertFalse(result["pinned_materials_match"])

    def test_reject_symlink_directory(self):
        alias = self.root / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(OSError):
            review.review_build_materials(alias)
