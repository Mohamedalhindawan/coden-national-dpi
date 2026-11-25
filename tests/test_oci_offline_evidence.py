import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest


def fixture(root, member=".wh.old", size=0, repeated=False, wrong_diff=False):
    store = root / "blobs" / "sha256"
    store.mkdir(parents=True)
    def put(raw):
        digest = hashlib.sha256(raw).hexdigest()
        (store / digest).write_bytes(raw)
        return {"digest": "sha256:" + digest, "size": len(raw)}
    def obj(data):
        return put(json.dumps(data, sort_keys=True).encode())
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as tar:
        entry = tarfile.TarInfo(member)
        entry.size = size
        tar.addfile(entry, io.BytesIO(b"x" * size))
    layer = put(gzip.compress(raw.getvalue(), mtime=0))
    layer["mediaType"] = "application/vnd.oci.image.layer.v1.tar+gzip"
    diff = "sha256:" + hashlib.sha256(raw.getvalue()).hexdigest()
    if wrong_diff:
        diff = "sha256:" + "0" * 64
    count = 2 if repeated else 1
    config = obj({"os": "linux", "architecture": "amd64", "rootfs": {
        "type": "layers", "diff_ids": [diff] * count}})
    config["mediaType"] = "application/vnd.oci.image.config.v1+json"
    manifest = obj({"schemaVersion": 2,
                    "mediaType": "application/vnd.oci.image.manifest.v1+json",
                    "config": config, "layers": [layer] * count})
    return manifest["digest"], store / layer["digest"][7:]


class OfflineOCIReviewTests(unittest.TestCase):
    def review(self, root, digest, limit=100000):
        from ai_factory.oci_offline_evidence import verify
        return verify(root, digest, max_expanded_bytes=limit,
                      max_compressed_bytes=100000)

    def test_verified_ordered_layers_and_whiteouts_not_admission(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            digest, _ = fixture(root, repeated=True)
            result = self.review(root, digest)
            self.assertEqual(result["status"], "layer_bytes_verified_review_only")
            self.assertEqual(result["layer_count"], 2)
            self.assertEqual(result["unique_layer_count"], 1)
            self.assertEqual([x["whiteouts"] for x in result["layers"]],
                             [[".wh.old"], [".wh.old"]])
            self.assertFalse(result["final_inventory_verified"])
            self.assertFalse(result["release_authorized"])
            self.assertFalse(result["execution_authorized"])

    def test_tampered_blob_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            digest, layer = fixture(root)
            layer.write_bytes(b"!" + layer.read_bytes()[1:])
            with self.assertRaises(ValueError):
                self.review(root, digest)

    def test_wrong_diff_id_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            digest, _ = fixture(root, wrong_diff=True)
            with self.assertRaises(ValueError):
                self.review(root, digest)

    def test_invalid_whiteout_and_path_rejected(self):
        for member, size in [(".wh.old", 1), ("../escape", 0), ("/absolute", 0)]:
            with self.subTest(member=member), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                digest, _ = fixture(root, member, size)
                with self.assertRaises(ValueError):
                    self.review(root, digest)

    def test_total_expanded_limit_includes_repeated_layers(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            digest, _ = fixture(root, repeated=True)
            with self.assertRaises(ValueError):
                self.review(root, digest, limit=15000)

    def test_missing_and_symlink_blob_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            digest, layer = fixture(root)
            data = layer.read_bytes()
            layer.unlink()
            with self.assertRaises(ValueError):
                self.review(root, digest)
            target = root / "outside"
            target.write_bytes(data)
            layer.symlink_to(target)
            with self.assertRaises(ValueError):
                self.review(root, digest)

    def test_compressed_budget_preflight_counts_unique_blobs_and_metadata(self):
        from ai_factory import oci_offline_evidence as audit
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            digest, _ = fixture(root, repeated=True)
            total = sum(p.stat().st_size for p in (root / "blobs/sha256").iterdir())
            with patch.object(audit, "_scan_layer", side_effect=AssertionError("must not read layers")):
                with self.assertRaisesRegex(ValueError, "compressed.*budget"):
                    audit.verify(root, digest, max_expanded_bytes=100000,
                                 max_compressed_bytes=total - 1)
            result = audit.verify(root, digest, max_expanded_bytes=100000,
                                  max_compressed_bytes=total)
            self.assertEqual(result["required_unique_payload_bytes"], total)
            self.assertEqual(result["max_compressed_bytes"], total)
            self.assertFalse(result["release_authorized"])
