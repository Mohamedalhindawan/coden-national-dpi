import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest


def fixture(root, member=".wh.old", size=0, repeated=False, wrong_diff=False, bad_end=None):
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
    if bad_end=="invalid_header":
        raw=io.BytesIO(raw.getvalue()[:512]+b"x"*512+raw.getvalue()[1024:])
    elif bad_end=="single_zero":
        raw=io.BytesIO(raw.getvalue()[:1024])
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

    def inventory(self, root, layers, *, embedded_binary=None, max_read=100000):
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
        if embedded_binary is not None:
            from ai_factory import oci_offline_evidence as audit
            from unittest.mock import patch
            with patch.multiple(audit,PINNED_MANIFEST=manifest["digest"],
                                PINNED_BINARY_SIZE=len(embedded_binary),
                                PINNED_BINARY_SHA256=hashlib.sha256(embedded_binary).hexdigest()):
                return verify(root,manifest["digest"],max_compressed_bytes=100000,
                              max_expanded_bytes=max_read,logical_inventory=True,embedded_inventory=True)
        return verify(root, manifest["digest"], max_compressed_bytes=100000,
                      max_expanded_bytes=max_read, logical_inventory=True)

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

    def test_package_metadata_hardlink_alias_does_not_duplicate_installed_packages(self):
        R,H=tarfile.REGTYPE,tarfile.LNKTYPE
        status="var/lib/dpkg/status"
        with tempfile.TemporaryDirectory() as d:
            report=self.inventory(Path(d), [[
                (status,R,b"Package: demo\nStatus: install ok installed\nVersion: 1\nArchitecture: amd64\n",0o644),
                ("backup/status",H,status,0o644),
            ]])
            rows=report["logical_inventory"]["package_metadata"]
            self.assertEqual([(x["name"],x["metadata_path"]) for x in rows],
                             [("demo",status)])

    def test_package_metadata_hardlink_without_matching_parse_is_rejected(self):
        R,H=tarfile.REGTYPE,tarfile.LNKTYPE
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"package metadata"):
                self.inventory(Path(d), [[
                    ("backup/status",R,b"Package: demo\nStatus: install ok installed\nVersion: 1\nArchitecture: amd64\n",0o644),
                    ("var/lib/dpkg/status",H,"backup/status",0o644),
                ]])

    def test_embedded_toc_preflight_only_reads_names_and_bounds(self):
        from ai_factory.oci_offline_evidence import inspect_carchive_toc
        raw = self.carchive_fixture([("lib/demo.so",0,4,8,1,b"b"),
                                     ("PYZ.pyz",4,12,12,0,b"z")])
        result = inspect_carchive_toc(io.BytesIO(raw), max_declared_expanded_bytes=20)
        self.assertEqual([x["name"] for x in result["entries"]], ["lib/demo.so","PYZ.pyz"])
        self.assertEqual(result["declared_expanded_bytes"],20)
        self.assertEqual(result["nested_payload_bytes_decompressed"],0)
        self.assertFalse(result["embedded_inventory_verified"])
        self.assertFalse(result["release_authorized"])

    @staticmethod
    def carchive_fixture(entries, payload=b"x"*16):
        import struct
        rows = []
        for name,offset,length,expanded,compressed,kind in entries:
            namebytes = name.encode()+b"\0"
            n = 18+len(namebytes)
            n += (-n)%16
            rows.append(struct.pack("!IIIIBc",n,offset,length,expanded,compressed,kind)
                        +namebytes+b"\0"*(n-18-len(namebytes)))
        toc=b"".join(rows)
        cookie=struct.pack("!8sIIII64s",b"MEI\x0c\x0b\x0a\x0b\x0e",
                           len(payload)+len(toc)+88,len(payload),len(toc),313,b"libpython3.13.so.1.0")
        return b"\x7fELF"+payload+toc+cookie

    def test_embedded_toc_rejects_ambiguous_or_out_of_bounds_entries(self):
        from ai_factory.oci_offline_evidence import inspect_carchive_toc
        cases=[
            [("a",0,4,4,0,b"b"),("a",4,4,4,0,b"b")],
            [("../escape",0,4,4,0,b"b")],
            [("/absolute",0,4,4,0,b"b")],
            [("a",15,2,2,0,b"b")],
            [("a",0,4,8,0,b"b")],
            [("a",0,4,4,2,b"b")],
            [("a",0,4,4,0,b"b"),("b",2,4,4,0,b"b")],
            [("a",0,4,100,1,b"b")],
        ]
        for entries in cases:
            with self.subTest(entries=entries):
                with self.assertRaises(ValueError):
                    inspect_carchive_toc(io.BytesIO(self.carchive_fixture(entries)),
                                         max_declared_expanded_bytes=20)
        valid=self.carchive_fixture([("a",0,4,4,0,b"b")])
        for raw in (valid[:-1],valid+b"x",b"not archive"):
            with self.assertRaises(ValueError):
                inspect_carchive_toc(io.BytesIO(raw),max_declared_expanded_bytes=20)

    @staticmethod
    def pyz_fixture(rows=None, toc=None, payload=None):
        # Trusted fixture generation only. Production reader must never unmarshal.
        import marshal,struct,zlib
        data=zlib.compress(b"not executable code") if payload is None else payload
        if toc is None:
            toc=marshal.dumps(rows if rows is not None else
                              [("demo",(0,17,len(data))),("namespace",(3,17+len(data),0))],4)
        return b"PYZ\0\xf3\x0d\x0d\x0a"+struct.pack("!i",17+len(data))+b"\0"*5+data+toc

    def test_pyz_metadata_grammar_and_hash_without_code_loading(self):
        from ai_factory.oci_offline_evidence import inspect_pyz_toc
        result=inspect_pyz_toc(io.BytesIO(self.pyz_fixture()),max_read_bytes=4096)
        self.assertEqual([x["name"] for x in result["entries"]],["demo","namespace"])
        self.assertEqual(result["entries"][0]["sha256"],hashlib.sha256(b"not executable code").hexdigest())
        self.assertIsNone(result["entries"][1]["sha256"])
        self.assertFalse(result["embedded_inventory_verified"])
        self.assertFalse(result["release_authorized"])

    def test_pyz_rejects_unsafe_grammar_ranges_and_decompression(self):
        import marshal,struct,zlib
        from ai_factory.oci_offline_evidence import inspect_pyz_toc
        data=zlib.compress(b"not executable code")
        n=len(data)
        invalid=[
            self.pyz_fixture(rows=[("../escape",(0,17,n))]),
            self.pyz_fixture(rows=[("demo",(0,17,n)),("demo",(0,17,n))]),
            self.pyz_fixture(rows=[("demo",(0,17,n)),("other",(0,17,n))]),
            self.pyz_fixture(rows=[("demo",(0,16,n))]),
            self.pyz_fixture(rows=[("demo",(0,17,n+1))]),
            self.pyz_fixture(rows=[("demo",(3,17,n))]),
            self.pyz_fixture(rows=[("demo",(7,17,n))]),
            self.pyz_fixture(toc=marshal.dumps(compile("pass","fixture","exec"),4)),
            self.pyz_fixture(toc=b"\\x00"),
            self.pyz_fixture(toc=b"l"+struct.pack("<i",2147483647)),
            self.pyz_fixture(toc=b"["+struct.pack("<i",50001)),
            self.pyz_fixture(toc=b"r"+struct.pack("<i",0)),
            self.pyz_fixture()+b"x",
            self.pyz_fixture(payload=data[:-1]),
            self.pyz_fixture(payload=data+b"trailing"),
        ]
        for raw in invalid:
            with self.subTest(raw=raw[-20:]):
                with self.assertRaises(ValueError):
                    inspect_pyz_toc(io.BytesIO(raw),max_read_bytes=4096)
        with self.assertRaises(ValueError):
            inspect_pyz_toc(io.BytesIO(self.pyz_fixture(payload=zlib.compress(b"x"*10000))),
                            max_read_bytes=1000)

    def test_embedded_inventory_recurses_pyz_once_and_uses_aggregate_budget(self):
        import zlib
        from ai_factory.oci_offline_evidence import inspect_embedded_binary
        pyz=self.pyz_fixture()
        compressed=zlib.compress(pyz)
        raw=self.carchive_fixture([("PYZ.pyz",0,len(compressed),len(pyz),1,b"z"),
                                   ("base_library.zip",len(compressed),4,4,0,b"x")],
                                  payload=compressed+b"PK\x03\x04")
        report=inspect_embedded_binary(io.BytesIO(raw),max_read_bytes=8192)
        self.assertEqual(report["pyz_archives"][0]["entries"][0]["name"],"demo")
        self.assertEqual(report["entries"][0]["sha256"],hashlib.sha256(pyz).hexdigest())
        self.assertIn("base_library.zip",report["uninspected_nested_archives"])
        self.assertFalse(report["embedded_inventory_verified"])
        with self.assertRaises(ValueError):
            inspect_embedded_binary(io.BytesIO(raw),max_read_bytes=report["aggregate_read_bytes"]-1)

    def test_embedded_inventory_rejects_escape_link_and_corrupt_member(self):
        import zlib
        from ai_factory.oci_offline_evidence import inspect_embedded_binary
        for kind,payload,declared,flag in [(b"n",b"../../outside\0",14,0),
                                            (b"b",zlib.compress(b"demo")[:-1],4,1),
                                            (b"b",zlib.compress(b"demo"),3,1)]:
            with self.subTest(kind=kind,payload=payload):
                if flag==0:
                    declared=len(payload)
                raw=self.carchive_fixture([("member",0,len(payload),declared,flag,kind)],payload=payload)
                with self.assertRaises(ValueError):
                    inspect_embedded_binary(io.BytesIO(raw),max_read_bytes=8192)

    def test_embedded_mode_requires_pinned_manifest_and_logical_inventory(self):
        from ai_factory.oci_offline_evidence import verify
        with tempfile.TemporaryDirectory() as d:
            digest,_=fixture(Path(d))
            with self.assertRaisesRegex(ValueError,"pinned.*inventory"):
                verify(Path(d),digest,max_expanded_bytes=100000,max_compressed_bytes=100000,
                       logical_inventory=True,embedded_inventory=True)

    def test_invalid_or_incomplete_tar_end_is_not_verified(self):
        for end in ("invalid_header","single_zero"):
            with self.subTest(end=end), tempfile.TemporaryDirectory() as d:
                digest,_=fixture(Path(d),bad_end=end)
                with self.assertRaises(ValueError):
                    self.review(Path(d),digest)

    def test_pinned_embedded_inventory_full_oci_path_and_overlay_budget(self):
        R=tarfile.REGTYPE
        pyz=self.pyz_fixture()
        binary=self.carchive_fixture([("PYZ.pyz",0,len(pyz),len(pyz),0,b"z")],payload=pyz)
        path="usr/local/bin/openhands-agent-server"
        layers=[[] for _ in range(12)]+[[(path,R,binary,0o755)]]
        with tempfile.TemporaryDirectory() as d:
            report=self.inventory(Path(d),layers,embedded_binary=binary,max_read=250000)
            embedded=report["embedded_archive_review"]
            self.assertEqual(embedded["binary_sha256"],hashlib.sha256(binary).hexdigest())
            self.assertEqual(embedded["pyz_archives"][0]["entries"][0]["name"],"demo")
            self.assertEqual(report["aggregate_expanded_and_nested_read_bytes"],
                             report["expanded_bytes"]+embedded["aggregate_read_bytes"])
            self.assertFalse(report["release_authorized"])
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                self.inventory(Path(d),layers,embedded_binary=binary,
                               max_read=report["aggregate_expanded_and_nested_read_bytes"]-1)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"final pinned binary"):
                self.inventory(Path(d),layers+[[("usr/local/bin/.wh.openhands-agent-server",R,b"",0)]],
                               embedded_binary=binary,max_read=250000)

    def test_pax_metadata_size_is_bounded_before_tarfile_parse(self):
        from ai_factory import oci_offline_evidence as audit
        from unittest.mock import patch
        R=tarfile.REGTYPE
        # Use a small synthetic extended header and lower the policy bound,
        # so rejection must happen before tarfile allocates/parses its body.
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            digest,layer=fixture(root)
            store=root/"blobs/sha256"
            buf=io.BytesIO()
            with tarfile.open(fileobj=buf,mode="w",format=tarfile.PAX_FORMAT) as tar:
                info=tarfile.TarInfo("example")
                info.pax_headers={"comment":"x"*8192}
                tar.addfile(info)
            raw=buf.getvalue()
            packed=gzip.compress(raw,mtime=0)
            def put(data):
                h=hashlib.sha256(data).hexdigest()
                (store/h).write_bytes(data)
                return {"digest":"sha256:"+h,"size":len(data)}
            desc=put(packed)
            desc["mediaType"]=audit.LAYER_TYPE
            cfg=put(json.dumps({"os":"linux","architecture":"amd64","rootfs":{"type":"layers","diff_ids":["sha256:"+hashlib.sha256(raw).hexdigest()]}}).encode())
            cfg["mediaType"]=audit.CONFIG_TYPE
            manifest=put(json.dumps({"schemaVersion":2,"mediaType":audit.MANIFEST_TYPE,"config":cfg,"layers":[desc]}).encode())
            with patch.object(audit,"MAX_METADATA",4096):
                with self.assertRaisesRegex(ValueError,"extended tar metadata"):
                    audit.verify(root,manifest["digest"],max_compressed_bytes=100000,max_expanded_bytes=100000,logical_inventory=True)

    def test_embedded_inventory_rejects_unaccounted_data_gaps(self):
        import zlib
        from ai_factory.oci_offline_evidence import inspect_embedded_binary,inspect_pyz_toc
        raw=self.carchive_fixture([("member",1,4,4,0,b"b")],payload=b"Xdata")
        with self.assertRaisesRegex(ValueError,"unaccounted"):
            inspect_embedded_binary(io.BytesIO(raw),max_read_bytes=8192)
        data=zlib.compress(b"module")
        raw=self.pyz_fixture(rows=[("demo",(0,18,len(data)))],payload=b"X"+data)
        with self.assertRaisesRegex(ValueError,"unaccounted"):
            inspect_pyz_toc(io.BytesIO(raw),max_read_bytes=8192)

    def test_embedded_inventory_rejects_link_ancestors_and_missing_nul(self):
        from ai_factory.oci_offline_evidence import inspect_embedded_binary
        for entries,payload in [
            ([("alias",0,7,7,0,b"n"),("alias/child",7,1,1,0,b"x")],b"target\0x"),
            ([("alias",0,6,6,0,b"n")],b"target"),
            ([("a",0,2,2,0,b"n"),("b",2,2,2,0,b"n")],b"b\0a\0"),
        ]:
            with self.subTest(entries=entries):
                with self.assertRaises(ValueError):
                    inspect_embedded_binary(io.BytesIO(self.carchive_fixture(entries,payload=payload)),max_read_bytes=8192)

    def test_embedded_inventory_distinguishes_unknown_archives_and_native_files(self):
        from ai_factory.oci_offline_evidence import inspect_embedded_binary
        raw=self.carchive_fixture([("native.so",0,4,4,0,b"b"),("opaque",4,4,4,0,b"x")],
                                  payload=b"\x7fELFPK\x05\x06")
        report=inspect_embedded_binary(io.BytesIO(raw),max_read_bytes=8192)
        self.assertEqual(report["entries"][0]["content_kind"],"elf")
        self.assertEqual(report["entries"][1]["content_kind"],"unreviewed_archive")
        self.assertEqual(report["uninspected_nested_archives"],["opaque"])
        self.assertFalse(report["embedded_inventory_verified"])
        self.assertFalse(report["release_authorized"])
