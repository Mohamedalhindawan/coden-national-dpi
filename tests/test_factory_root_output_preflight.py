import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ai_factory import factory_root_output_preflight as review
from ai_factory import factory_root_source_payload as payload
from ai_factory import factory_wheel_notice_audit as scanner
from test_factory_root_wheel_review import candidate, ROOTS, NOTICE


class OutputDirectoryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.out = Path(temp.name)
        self.lock = ("\n".join(
            '[[package]]\nname = "' + name + '"\nversion = "1.63.1"\n'
            '[package.metadata]\nrequires-dist = [{name="demo"}]\nprovides-extras=[]'
            for name in ROOTS) + "\n").encode()
        roots = {}
        for name in ROOTS:
            basename = name.replace("-", "_") + "-1.63.1-py3-none-any.whl"
            body, _ = candidate(name, headers="Requires-Dist: demo\n")
            (self.out / basename).write_bytes(body)
            path = "openhands/" + name.removeprefix("openhands-").replace("-", "_") + "/fixture.py"
            data = b"# synthetic only\n"
            roots[name] = {path: {"sha256": hashlib.sha256(data).hexdigest(),
                                  "bytes": len(data), "required": True}}
        self.expectations = json.dumps({"roots": roots}).encode()
        for obj, key, raw in ((scanner, "ROOT_NOTICE_SHA256", NOTICE),
                              (scanner, "ROOT_METADATA_LOCK_SHA256", self.lock),
                              (payload, "EXPECTED_SHA256", self.expectations)):
            p = patch.object(obj, key, hashlib.sha256(raw).hexdigest())
            p.start()
            self.addCleanup(p.stop)

    def check(self):
        return review.review_output_directory(self.out, lock_bytes=self.lock,
                                              expectations_bytes=self.expectations)

    def test_actual_wheel_bytes_match_source_and_metadata(self):
        result = self.check()
        self.assertEqual(result["status"], "ROOT_OUTPUT_DIRECTORY_REVIEW_ONLY")
        self.assertEqual(result["wheel_count"], 4)
        self.assertEqual(result["matched_payload_files"], 4)
        self.assertEqual(result["console_script_count"], 1)
        self.assertTrue(result["filename_identity_match"])
        for key in ("builder_provenance_verified", "installation_authorized", "release_authorized"):
            self.assertIs(result[key], False)

    def test_missing_or_extra_output_blocks(self):
        p = self.out / "extra.whl"
        p.write_bytes(b"x")
        with self.assertRaises(ValueError):
            self.check()
        p.unlink()
        next(self.out.iterdir()).unlink()
        with self.assertRaises(ValueError):
            self.check()

    def test_swapped_names_rejected_even_when_all_wheels_valid(self):
        a, b = sorted(self.out.iterdir())[:2]
        raw_a, raw_b = a.read_bytes(), b.read_bytes()
        a.write_bytes(raw_b)
        b.write_bytes(raw_a)
        with self.assertRaises(ValueError):
            self.check()

    def test_symlink_fifo_hardlink_and_oversize_rejected(self):
        path = sorted(self.out.iterdir())[0]
        original = path.read_bytes()
        outside = self.out.parent / (self.out.name + "-outside")
        outside.write_bytes(original)
        self.addCleanup(outside.unlink)
        path.unlink()
        path.symlink_to(outside)
        with self.assertRaises((OSError, ValueError)):
            self.check()
        path.unlink()
        os.mkfifo(path)
        with self.assertRaises((OSError, ValueError)):
            self.check()
        path.unlink()
        os.link(outside, path)
        with self.assertRaises((OSError, ValueError)):
            self.check()
        path.unlink()
        with path.open("wb") as f:
            f.truncate(8 * 1024**2 + 1)
        with self.assertRaises(ValueError):
            self.check()

    def test_tampered_lock_or_payload_contract_rejected(self):
        with self.assertRaises(ValueError):
            review.review_output_directory(self.out, lock_bytes=self.lock+b"\n",
                                           expectations_bytes=self.expectations)
        with self.assertRaises(ValueError):
            review.review_output_directory(self.out, lock_bytes=self.lock,
                                           expectations_bytes=self.expectations+b"\n")
