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

    def inventory(self, root, layers):
        from ai_factory.oci_offline_evidence import verify
        store = root / "blobs/sha256"
        store.mkdir(parents=True)
        def put(raw, media=None):
            digest = hashlib.sha256(raw).hexdigest()
            (store / digest).write_bytes(raw)
            return {"digest": "sha256:" + digest, "size": len(raw), "mediaType": media}
        descs, diffs = [], []
        for members in layers:
            raw = io.BytesIO()
            with tarfile.open(fileobj=raw, mode="w") as tar:
                for name, kind, value, mode in members:
                    info = tarfile.TarInfo(name)
                    info.type, info.mode = kind, mode
                    data = value if kind == tarfile.REGTYPE else b""
                    if kind in (tarfile.LNKTYPE, tarfile.SYMTYPE):
                        info.linkname = value
                    info.size = len(data)
                    tar.addfile(info, io.BytesIO(data))
            diffs.append("sha256:" + hashlib.sha256(raw.getvalue()).hexdigest())
            descs.append(put(gzip.compress(raw.getvalue(), mtime=0),
                             "application/vnd.oci.image.layer.v1.tar+gzip"))
        cfg = put(json.dumps({"os":"linux","architecture":"amd64","rootfs":{
            "type":"layers","diff_ids":diffs}}).encode(), "application/vnd.oci.image.config.v1+json")
        manifest = put(json.dumps({"schemaVersion":2,"mediaType":"application/vnd.oci.image.manifest.v1+json",
                                   "config":cfg,"layers":descs}).encode())
        return verify(root, manifest["digest"], max_compressed_bytes=100000,
                      max_expanded_bytes=100000, logical_inventory=True)

    def test_inventory_whiteouts_lower_only_and_opaque_order(self):
        R, D = tarfile.REGTYPE, tarfile.DIRTYPE
        with tempfile.TemporaryDirectory() as d:
            report = self.inventory(Path(d), [
                [("etc",D,None,0o755),("etc/old",R,b"old",0o644),
                 ("etc/keep",R,b"lower",0o644),("remove/sub",R,b"gone",0o644)],
                [("etc/new",R,b"new",0o755),("etc/.wh..wh..opq",R,b"",0),
                 ("etc/keep",R,b"upper",0o644),("etc/.wh.keep",R,b"",0),
                 (".wh.remove",R,b"",0)]])
            inv = report["logical_inventory"]
            rows = {row["path"]:row for row in inv["entries"]}
            self.assertNotIn("etc/old", rows)
            self.assertNotIn("remove", rows)
            self.assertNotIn("remove/sub", rows)
            self.assertEqual(rows["etc/keep"]["sha256"], hashlib.sha256(b"upper").hexdigest())
            self.assertEqual(rows["etc/new"]["layer"], 2)
            self.assertTrue(rows["etc/new"]["mode"] & 0o111)
            self.assertTrue(report["whiteout_semantics_applied"])
            self.assertFalse(report["final_inventory_verified"])
            self.assertFalse(report["release_authorized"])

    def test_inventory_replaced_directory_and_hardlink_retains_content(self):
        R,D,H=tarfile.REGTYPE,tarfile.DIRTYPE,tarfile.LNKTYPE
        with tempfile.TemporaryDirectory() as d:
            report=self.inventory(Path(d), [
                [("tree",D,None,0o755),("tree/a",R,b"old",0o4755),("alias",H,"tree/a",0o644)],
                [("tree",R,b"replacement",0o644)]])
            rows={x["path"]:x for x in report["logical_inventory"]["entries"]}
            self.assertNotIn("tree/a",rows)
            self.assertEqual(rows["alias"]["sha256"],hashlib.sha256(b"old").hexdigest())
            self.assertEqual(rows["alias"]["mode"],0o4755)
            self.assertEqual(rows["tree"]["sha256"],hashlib.sha256(b"replacement").hexdigest())

    def test_inventory_rejects_ambiguous_paths_and_unresolved_hardlinks(self):
        R,S,H=tarfile.REGTYPE,tarfile.SYMTYPE,tarfile.LNKTYPE
        for entries in [
            [("a",S,"/usr",0o777),("a/child",R,b"x",0o644)],
            [("a",R,b"x",0o644),("./a",R,b"y",0o644)],
            [("a",H,"missing",0o644)],
            [("a",S,"../../outside",0o777)],
        ]:
            with self.subTest(entries=entries), tempfile.TemporaryDirectory() as d:
                with self.assertRaises(ValueError):
                    self.inventory(Path(d), [entries])

    def test_inventory_package_metadata_from_final_regular_files_only(self):
        R=tarfile.REGTYPE
        with tempfile.TemporaryDirectory() as d:
            report=self.inventory(Path(d), [[
                ("var/lib/dpkg/status",R,b"Package: old\nStatus: install ok installed\nVersion: 1\nArchitecture: amd64\n",0o644),
            ],[
                ("var/lib/dpkg/status",R,b"Package: new\nStatus: install ok installed\nVersion: 2\nArchitecture: amd64\n",0o644),
                ("usr/lib/python3/site-packages/foo-1.dist-info/METADATA",R,b"Name: foo\nVersion: 1\nLicense-Expression: MIT\n\n",0o644),
            ]])
            rows=report["logical_inventory"]["package_metadata"]
            self.assertEqual([(x["name"],x["version"]) for x in rows],[("foo","1"),("new","2")])
            self.assertFalse(report["license_approved"])
            self.assertFalse(report["embedded_inventory_verified"])
