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


def recorded_wheel(name="demo", payload=b"fixture" * 100, alter=None, extras=()):
    import base64
    import csv
    prefix = name + "-1.dist-info/"
    files = {name + "/__init__.py": payload,
             prefix + "METADATA": b"Name: demo\nVersion: 1\n",
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
