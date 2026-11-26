import hashlib
import io
import unittest
import zipfile
from ai_factory.factory_wheel_notice_audit import inspect_wheel, select_candidates


def wheel(name='demo-1.dist-info/LICENSE', data=b'MIT fixture'):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr(name, data)
        z.writestr('demo-1.dist-info/METADATA', 'Name: demo\nVersion: 1\n')
    return buf.getvalue()


class WheelNoticeTests(unittest.TestCase):
    def test_collect_notice_and_metadata_without_extracting(self):
        raw = wheel()
        result = inspect_wheel(raw, hashlib.sha256(raw).hexdigest())
        self.assertEqual(len(result), 2)
        self.assertIn('demo-1.dist-info/LICENSE', result)

    def test_reject_wrong_digest(self):
        with self.assertRaises(ValueError):
            inspect_wheel(wheel(), '0' * 64)

    def test_reject_traversal_even_if_not_notice(self):
        raw = wheel('../other.py')
        with self.assertRaises(ValueError):
            inspect_wheel(raw, hashlib.sha256(raw).hexdigest())

    def test_reject_non_registry_host(self):
        lock = {'package': [{'name': 'demo', 'version': '1', 'wheels': [{'url': 'https://example.com/demo.whl', 'hash': 'sha256:' + 'a' * 64}]}]}
        with self.assertRaises(ValueError):
            select_candidates(lock, {'demo': ('1', {'a' * 64})})

    def test_reject_missing_candidate(self):
        with self.assertRaises(ValueError):
            select_candidates({'package': []}, {'demo': ('1', {'a' * 64})})

    def test_reject_noncanonical_paths_and_file_ancestor_collisions(self):
        for names in (("demo/./file.py",), ("demo//file.py",),
                      ("./demo.py",), ("demo/\x1f.py",),
                      ("demo", "demo/file.py"), ("demo/file.py", "demo"),
                      ("demo/", "demo")):
            with self.subTest(names=names):
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w") as z:
                    z.writestr("demo-1.dist-info/METADATA", "Name: demo\\nVersion: 1\\n")
                    for name in names:
                        z.writestr(name, b"" if name.endswith("/") else b"x")
                raw = buf.getvalue()
                with self.assertRaises(ValueError):
                    inspect_wheel(raw, hashlib.sha256(raw).hexdigest())


def recorded_wheel(name="demo", payload=b"fixture" * 100, alter=None, extras=(), metadata=None):
    import base64
    import csv
    prefix = name + "-1.dist-info/"
    files = {name + "/__init__.py": payload,
             prefix + "METADATA": (f"Name: {name}\nVersion: 1\n".encode() if metadata is None else metadata),
             prefix + "WHEEL": b"Wheel-Version: 1.0\nTag: py3-none-any\n",
             prefix + "LICENSE": b"MIT fixture"}
    rows = [[p, "sha256=" + base64.urlsafe_b64encode(hashlib.sha256(b).digest()).decode().rstrip("="), str(len(b))]
            for p, b in files.items()]
    rows.append([prefix + "RECORD", "", ""])
    if alter is not None:
        alter(rows)
    record = io.StringIO(newline="")
    csv.writer(record, lineterminator="\n").writerows(rows)
    files[prefix + "RECORD"] = record.getvalue().encode()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p, b in [*files.items(), *extras]:
            z.writestr(p, b)
    return buf.getvalue(), sum(map(len, files.values()))


class StrictWheelIntegrityTests(unittest.TestCase):
    def test_strict_receipt_binds_archive_digest_and_distribution_identity(self):
        from ai_factory.factory_wheel_notice_audit import WheelBudget
        raw, _ = recorded_wheel("fastmcp_slim",
                                metadata=b"Name: FastMCP-Slim\nVersion: 1\n")
        digest = hashlib.sha256(raw).hexdigest()
        result = inspect_wheel(raw, digest, budget=WheelBudget())
        self.assertEqual(result["wheel_sha256"], digest)
        self.assertEqual(result["distribution"], {"name": "fastmcp-slim", "version": "1"})
        self.assertTrue(result["record_verified"])
        self.assertFalse(result["release_authorized"])

    def test_strict_rejects_record_consistent_but_wrong_or_ambiguous_metadata_identity(self):
        from ai_factory.factory_wheel_notice_audit import WheelBudget
        for metadata in (b"Name: different\nVersion: 1\n",
                         b"Name: demo\nVersion: 2\n",
                         b"Name: demo\nName: demo\nVersion: 1\n",
                         b"Name: demo\nVersion: 1\nVersion: 1\n",
                         b"Name: demo\n",
                         b"Name: demo\nVersion: 1\n\n" + b"x" * (2 * 1024**2)):
            with self.subTest(metadata=metadata[:60]):
                raw, _ = recorded_wheel(metadata=metadata)
                budget = WheelBudget()
                with self.assertRaises(ValueError):
                    inspect_wheel(raw, hashlib.sha256(raw).hexdigest(), budget=budget)
                self.assertTrue(budget.failed)

    def test_three_wheels_share_one_nonresetting_budget(self):
        from ai_factory.factory_wheel_notice_audit import WheelBudget
        pairs = [recorded_wheel(name) for name in ("one", "two", "three")]
        cap = sum(size for _, size in pairs[:2])
        budget = WheelBudget(compressed_limit=sum(len(raw) for raw, _ in pairs), expanded_limit=cap)
        for raw, size in pairs[:2]:
            result = inspect_wheel(raw, hashlib.sha256(raw).hexdigest(), budget=budget)
            self.assertTrue(result["record_verified"])
            self.assertEqual(result["expanded_bytes"], size)
            self.assertNotIn("base64", str(result))
        self.assertEqual(budget.expanded_bytes, cap)
        with self.assertRaises(ValueError):
            inspect_wheel(pairs[2][0], hashlib.sha256(pairs[2][0]).hexdigest(), budget=budget)
        self.assertTrue(budget.failed)
        with self.assertRaises(ValueError):
            inspect_wheel(pairs[0][0], hashlib.sha256(pairs[0][0]).hexdigest(), budget=budget)
        self.assertEqual(budget.expanded_bytes, cap)

    def test_complete_record_and_reject_hash_size_missing_duplicate_and_unlisted(self):
        from ai_factory.factory_wheel_notice_audit import WheelBudget
        cases = (
            (lambda rows: rows[0].__setitem__(1, "sha256=" + "A"*43), ()),
            (lambda rows: rows[0].__setitem__(2, "999"), ()),
            (lambda rows: rows.pop(0), ()),
            (lambda rows: rows.append(rows[0][:]), ()),
            (lambda rows: rows[0].__setitem__(1, ""), ()),
            (lambda rows: rows[-1].__setitem__(1, "sha256="+"A"*43), ()),
            (lambda rows: rows.append(["ghost", "", ""]), ()),
            (None, (("unlisted.py", b"x"),)),
            (None, (("demo-1.dist-info/RECORD.jws", b"signature"),)),
        )
        for n, (alter, extras) in enumerate(cases):
            raw, _ = recorded_wheel(alter=alter, extras=extras)
            budget = WheelBudget(compressed_limit=1024**2, expanded_limit=1024**2)
            if n == len(cases)-1:
                self.assertTrue(inspect_wheel(raw, hashlib.sha256(raw).hexdigest(), budget=budget)["record_verified"])
            else:
                with self.subTest(n=n), self.assertRaises(ValueError):
                    inspect_wheel(raw, hashlib.sha256(raw).hexdigest(), budget=budget)
                self.assertTrue(budget.failed)

    def test_missing_record_and_unicode_collision_fail_closed(self):
        from ai_factory.factory_wheel_notice_audit import WheelBudget
        for raw in (wheel(), recorded_wheel(extras=(("caf\u00e9/a", b"x"), ("cafe\u0301/b", b"x")))[0]):
            with self.assertRaises(ValueError):
                inspect_wheel(raw, hashlib.sha256(raw).hexdigest(), budget=WheelBudget())

    def test_deflate_overrun_even_with_forged_declared_size_and_crc(self):
        import struct
        import zlib
        from ai_factory.factory_wheel_notice_audit import WheelBudget
        import base64
        def forge_record(rows):
            rows[0][1] = "sha256=" + base64.urlsafe_b64encode(hashlib.sha256(b"x").digest()).decode().rstrip("=")
            rows[0][2] = "1"
        raw, _ = recorded_wheel(payload=b"x"*20000, alter=forge_record)
        b = bytearray(raw)
        # First local and central file entry. Forge both declared size and CRC
        # of the prefix. Actual compressed stream still expands to 20,000 bytes.
        central = b.index(b"PK\x01\x02")
        crc = zlib.crc32(b"x")
        struct.pack_into("<I", b, 14, crc)
        struct.pack_into("<I", b, 22, 1)
        struct.pack_into("<I", b, central+16, crc)
        struct.pack_into("<I", b, central+24, 1)
        budget = WheelBudget()
        with self.assertRaisesRegex(ValueError, "actual wheel member size exceeds declaration"):
            inspect_wheel(bytes(b), hashlib.sha256(b).hexdigest(), budget=budget)
        self.assertTrue(budget.failed)

    def test_compressed_budget_cannot_be_reset_after_failure(self):
        from ai_factory.factory_wheel_notice_audit import WheelBudget
        raw, _ = recorded_wheel()
        budget = WheelBudget(compressed_limit=len(raw)-1, expanded_limit=1024**2)
        with self.assertRaises(ValueError):
            inspect_wheel(raw, hashlib.sha256(raw).hexdigest(), budget=budget)
        self.assertTrue(budget.failed)
        with self.assertRaises(ValueError):
            inspect_wheel(raw, hashlib.sha256(raw).hexdigest(), budget=budget)


class BoundedElfOutputTests(unittest.TestCase):
    def test_bounded_subprocess_output_and_timeout_cleanup(self):
        import sys
        import tempfile
        import os
        from pathlib import Path
        from ai_factory.factory_python_elf import _bounded_command
        ok = _bounded_command([sys.executable, "-I", "-c", "print('ok')"], stdout_limit=16, stderr_limit=16, timeout=5)
        self.assertEqual(ok, "ok\n")
        for code in ("import sys; sys.stdout.write('x'*1000000)",
                     "import sys; sys.stderr.write('x'*1000000)",
                     "raise SystemExit(2)"):
            with self.subTest(code=code), self.assertRaises(ValueError):
                _bounded_command([sys.executable, "-I", "-c", code], stdout_limit=1024, stderr_limit=1024, timeout=5)
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp)/"pid"
            code = "import os,time,pathlib; pathlib.Path(%r).write_text(str(os.getpid())); time.sleep(60)" % str(marker)
            with self.assertRaises(ValueError):
                _bounded_command([sys.executable, "-I", "-c", code], stdout_limit=1024, stderr_limit=1024, timeout=1)
            self.assertTrue(marker.exists())
            with self.assertRaises(ProcessLookupError):
                os.kill(int(marker.read_text()), 0)

    def test_readelf_malformed_input_rejected(self):
        import tempfile
        from pathlib import Path
        from ai_factory.factory_python_elf import inspect_elf_file
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/"malformed"
            p.write_bytes(b"\x7fELF"+b"\0"*16)
            with self.assertRaises(ValueError):
                inspect_elf_file(p)


class IntegratedWheelBatchTests(unittest.TestCase):
    def test_three_wheels_one_budget_actual_native_metadata_and_cleanup(self):
        import tempfile
        from pathlib import Path
        from ai_factory.factory_wheel_notice_audit import inspect_wheel_batch
        pairs = [recorded_wheel("first"), recorded_wheel("second", payload=Path("/bin/true").read_bytes()),
                 recorded_wheel("third")]
        candidates = [(raw, hashlib.sha256(raw).hexdigest()) for raw, _ in pairs]
        with tempfile.TemporaryDirectory() as tmp:
            receipt = inspect_wheel_batch(candidates, scratch=Path(tmp), inspect_native=True, fixture_native=True)
            self.assertEqual(list(Path(tmp).iterdir()), [])
        self.assertEqual(receipt["compressed_bytes"], sum(len(raw) for raw, _ in pairs))
        self.assertEqual(receipt["expanded_bytes"], sum(size for _, size in pairs))
        self.assertEqual(len(receipt["wheels"]), 3)
        self.assertEqual(receipt["native_count"], 1)
        self.assertTrue(receipt["wheels"][1]["files"]["second/__init__.py"]["native"]["machine"])
        self.assertFalse(receipt["release_authorized"])
        self.assertFalse(receipt["legacy_signatures_verified"])
        self.assertNotIn("base64", str(receipt))

    def test_batch_native_failure_removes_temp_and_rejects_whole_batch(self):
        import tempfile
        from pathlib import Path
        from ai_factory.factory_wheel_notice_audit import inspect_wheel_batch
        pairs = [recorded_wheel("first"), recorded_wheel("broken", payload=b"\x7fELF"+b"\0"*16),
                 recorded_wheel("third")]
        candidates = [(raw, hashlib.sha256(raw).hexdigest()) for raw, _ in pairs]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                inspect_wheel_batch(candidates, scratch=Path(tmp), inspect_native=True, fixture_native=True)
            self.assertEqual(list(Path(tmp).iterdir()), [])


class FullLogicalIOTests(unittest.TestCase):
    def test_repeated_reads_charged_and_partial_read_does_not_cross_limit(self):
        from ai_factory.factory_wheel_notice_audit import WheelBudget, _MeteredArchive
        budget = WheelBudget(expanded_limit=10, io_limit=10)
        reader = _MeteredArchive(b"abcdef", budget)
        self.assertEqual(reader.read(4), b"abcd")
        reader.seek(0)
        self.assertEqual(reader.read(4), b"abcd")
        self.assertEqual(budget.archive_read_bytes, 8)
        with self.assertRaises(ValueError):
            reader.read(3)
        self.assertEqual(reader.tell(), 4)
        self.assertEqual(budget.archive_read_bytes, 8)
        self.assertTrue(budget.failed)

    def test_archive_hash_zip_headers_and_member_reads_share_io_budget(self):
        from ai_factory.factory_wheel_notice_audit import WheelBudget
        raw, expanded = recorded_wheel()
        budget = WheelBudget()
        result = inspect_wheel(raw, hashlib.sha256(raw).hexdigest(), budget=budget)
        self.assertGreater(result["archive_read_bytes"], len(raw))
        self.assertEqual(result["logical_io_bytes"], result["archive_read_bytes"]+expanded)
        small = WheelBudget(io_limit=len(raw))
        with self.assertRaises(ValueError):
            inspect_wheel(raw, hashlib.sha256(raw).hexdigest(), budget=small)
        self.assertTrue(small.failed)
        self.assertLessEqual(small.logical_io_bytes, len(raw))

    def test_stored_member_read_rejected_before_slice(self):
        from ai_factory.factory_wheel_notice_audit import WheelBudget, _MeteredArchive, _member_blocks
        data = b"x"*100
        entry = zipfile.ZipInfo("object")
        entry.compress_type = zipfile.ZIP_STORED
        entry.file_size = len(data)
        budget = WheelBudget(expanded_limit=5)
        reader = _MeteredArchive(data,budget)
        with self.assertRaises(ValueError):
            list(_member_blocks(reader,entry,(0,len(data)),budget))
        self.assertEqual(budget.archive_read_bytes,0)

    def test_multidisk_eocd_and_trailing_data_rejected(self):
        import struct
        from ai_factory.factory_wheel_notice_audit import WheelBudget
        raw,_ = recorded_wheel()
        broken=bytearray(raw)
        end=broken.rindex(b"PK\x05\x06")
        struct.pack_into("<H",broken,end+4,1)
        for data in (bytes(broken),raw+b"trailing"):
            with self.subTest(length=len(data)),self.assertRaises(ValueError):
                inspect_wheel(data,hashlib.sha256(data).hexdigest(),budget=WheelBudget())

    def test_native_inspection_requires_explicit_fixture_scope(self):
        import tempfile
        from pathlib import Path
        from ai_factory.factory_wheel_notice_audit import inspect_wheel_batch
        pairs=[recorded_wheel(n) for n in ("one","two","three")]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,"native.*blocked"):
                inspect_wheel_batch([(raw,hashlib.sha256(raw).hexdigest()) for raw,_ in pairs],
                                    scratch=Path(tmp),inspect_native=True)
            self.assertEqual(list(Path(tmp).iterdir()),[])

    def test_reject_central_entry_start_disk_even_if_eocd_single_disk(self):
        import struct
        from ai_factory.factory_wheel_notice_audit import WheelBudget
        raw,_ = recorded_wheel()
        broken = bytearray(raw)
        central = broken.index(b"PK\x01\x02")
        struct.pack_into("<H",broken,central+34,1)
        data = bytes(broken)
        with self.assertRaises(ValueError):
            inspect_wheel(data,hashlib.sha256(data).hexdigest(),budget=WheelBudget())

    def test_shared_evidence_limit_rejects_second_wheel_before_return(self):
        from ai_factory.factory_wheel_notice_audit import WheelBudget
        raw,_=recorded_wheel("one")
        probe=WheelBudget()
        first=inspect_wheel(raw,hashlib.sha256(raw).hexdigest(),budget=probe)
        self.assertGreater(first["evidence_bytes"],0)
        budget=WheelBudget(evidence_limit=first["evidence_bytes"])
        inspect_wheel(raw,hashlib.sha256(raw).hexdigest(),budget=budget)
        raw2,_=recorded_wheel("two")
        with self.assertRaisesRegex(ValueError,"evidence.*limit"):
            inspect_wheel(raw2,hashlib.sha256(raw2).hexdigest(),budget=budget)
        self.assertTrue(budget.failed)
        self.assertEqual(budget.evidence_bytes,first["evidence_bytes"])


class R2HistoricalReceiptComparisonTests(unittest.TestCase):
    """Fabricated receipts exercise comparison only, not package acquisition."""
    def fixture(self):
        specs = (
            ("jiter", "0.16.0", "c682bea068a90b764577bdb78a60a4c1d1606daf9cd4c893832a37c7cc9d9026",
             "jiter/jiter.cpython-313-x86_64-linux-gnu.so", 832152,
             "bbc712e9a00a2b01cfa40286d129cb43f019692d7bf94069f58ab1de6094d29e"),
            ("tokenizers", "0.23.2", "41c2f84d172449b4dadb9cdc508e3e364076613c35b16e76ecfe47a60d1e3305",
             "tokenizers/tokenizers.abi3.so", 11317624,
             "7c4ddf7ad4251a646d324151b4d698da59531fdd892ea3abd24a6f323fcb1d6b"),
            ("fastmcp-slim", "4.2.0", "174239bed3ac47275afa7fe82941a65f86ad0314205195766c92b138c6dcfebe",
             None, 0, None),
        )
        wheels = []
        historical = {"jiter": (343320, 885473, 9),
                      "tokenizers": (3386843, 11701061, 32),
                      "fastmcp-slim": (994236, 3507586, 288)}
        for name, version, digest, native, size, native_digest in specs:
            compressed, expanded, members = historical[name]
            files = {}
            for i in range(members - int(native is not None)):
                files[f"synthetic/{i}"] = {"sha256": "a"*64, "bytes": 0,
                                          "record_hash_verified": True, "elf_magic": False}
            if native:
                files[native] = {"sha256": native_digest, "bytes": size,
                                 "record_hash_verified": True, "elf_magic": True}
            retained = {
                "jiter": {
                    "jiter-0.16.0.dist-info/METADATA": (5212, "b1bcf7374eb4f4195f890ab610b6de54ae8766456df7ddf757f95d255097ef2e"),
                    "jiter-0.16.0.dist-info/licenses/LICENSE": (1091, "7c7134b9f7b978c03fca875517cf398db91f19bbb8109b6685e742aa3f57468e")},
                "tokenizers": {"tokenizers-0.23.2.dist-info/METADATA": (9830, "d2d200c0d0c48895b2c3b02cdd8c06c26dea8f9be38ef193e9b4dd5a566c89be")},
                "fastmcp-slim": {"fastmcp_slim-4.2.0.dist-info/METADATA": (11160, "df6b0719b4582d41663c1ef35cdc7f655dc809d16f144a4cea0589e7bc8ba3c1")},
            }[name]
            for i, (path, (length, sha)) in enumerate(retained.items(), start=2):
                files.pop(f"synthetic/{i}")
                files[path] = {"sha256": sha, "bytes": length,
                               "record_hash_verified": True, "elf_magic": False}
            files["synthetic/0"]["bytes"] = expanded - size - sum(x[0] for x in retained.values())
            wheels.append({"distribution": {"name": name, "version": version},
                           "wheel_sha256": digest, "files": files,
                           "record_verified": True, "native_internal_io_verified": False,
                           "release_authorized": False, "legacy_signatures_verified": False,
                           "compressed_bytes": compressed, "expanded_bytes": expanded})
        return {"wheels": wheels, "compressed_bytes": 4724399,
                "expanded_bytes": 16094120, "record_verified": True,
                "fixture_native": False, "native_count": 0, "native_output_bytes": 0,
                "native_input_reserved_bytes": 0, "native_internal_io_verified": False,
                "release_authorized": False, "legacy_signatures_verified": False}

    def test_exact_historical_comparison_never_grants_admission(self):
        from ai_factory.factory_wheel_notice_audit import compare_r2_historical_receipt
        result = compare_r2_historical_receipt(self.fixture())
        self.assertEqual(result["status"], "HISTORICAL_RECEIPT_MATCH_UNAPPROVED")
        self.assertEqual(result["matched_wheels"], 3)
        self.assertEqual(result["regular_files"], 329)
        self.assertFalse(result["receipt_origin_verified"])
        self.assertFalse(result["security_approved"])
        self.assertFalse(result["installation_authorized"])
        self.assertFalse(result["release_authorized"])

    def test_mismatch_and_overclaim_fail_closed(self):
        from ai_factory.factory_wheel_notice_audit import compare_r2_historical_receipt
        def native(r):
            return r["wheels"][0]["files"]["jiter/jiter.cpython-313-x86_64-linux-gnu.so"]
        mutations = (
            lambda r: r["wheels"][0].update(wheel_sha256="0"*64),
            lambda r: r["wheels"][0]["distribution"].update(version="0.16.1"),
            lambda r: r["wheels"].__setitem__(1, r["wheels"][0]),
            lambda r: native(r).update(sha256="0"*64),
            lambda r: native(r).update(bytes=832153),
            lambda r: native(r).update(elf_magic=False),
            lambda r: r["wheels"][2]["files"]["synthetic/0"].update(elf_magic=True),
            lambda r: r["wheels"][2]["files"].pop("synthetic/1"),
            lambda r: r.update(compressed_bytes=4724400),
            lambda r: r.update(expanded_bytes=16094121),
            lambda r: r.update(fixture_native=True),
            lambda r: r.update(record_verified=1),
            lambda r: r["wheels"][0].update(release_authorized=True),
        )
        for i, mutate in enumerate(mutations):
            with self.subTest(case=i):
                receipt = self.fixture()
                mutate(receipt)
                with self.assertRaises(ValueError):
                    compare_r2_historical_receipt(receipt)


    def test_redistribution_preserving_batch_totals_is_rejected(self):
        from ai_factory.factory_wheel_notice_audit import compare_r2_historical_receipt
        for field in ("compressed_bytes", "expanded_bytes", "members"):
            with self.subTest(field=field):
                receipt = self.fixture()
                first, second = receipt["wheels"][:2]
                if field == "members":
                    second["files"]["synthetic/moved"] = first["files"].pop("synthetic/1")
                else:
                    first[field] -= 1
                    second[field] += 1
                    if field == "expanded_bytes":
                        first["files"]["synthetic/0"]["bytes"] -= 1
                        second["files"]["synthetic/0"]["bytes"] += 1
                with self.assertRaises(ValueError):
                    compare_r2_historical_receipt(receipt)


    def test_retained_metadata_and_license_identity_cannot_be_forged(self):
        from ai_factory.factory_wheel_notice_audit import compare_r2_historical_receipt
        for index, path in (
            (0, "jiter-0.16.0.dist-info/METADATA"),
            (0, "jiter-0.16.0.dist-info/licenses/LICENSE"),
            (1, "tokenizers-0.23.2.dist-info/METADATA"),
            (2, "fastmcp_slim-4.2.0.dist-info/METADATA"),
        ):
            for change in ("hash", "record", "path"):
                with self.subTest(path=path, change=change):
                    receipt = self.fixture()
                    files = receipt["wheels"][index]["files"]
                    if change == "hash":
                        files[path]["sha256"] = "0"*64
                    elif change == "record":
                        files[path]["record_hash_verified"] = False
                    else:
                        files["synthetic/replaced"] = files.pop(path)
                    with self.assertRaises(ValueError):
                        compare_r2_historical_receipt(receipt)
