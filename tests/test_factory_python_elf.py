import hashlib
import io
import shutil
import tarfile
import unittest
from pathlib import Path
from ai_factory.factory_python_elf import collect_elf


class PythonElfReviewTest(unittest.TestCase):
    def setUp(self):
        self.binary = Path('/bin/true').read_bytes()
        self.path = 'python/bin/python3.13'
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode='w:gz') as tar:
            entry = tarfile.TarInfo(self.path)
            entry.size = len(self.binary)
            tar.addfile(entry, io.BytesIO(self.binary))
        self.raw = buf.getvalue()
        self.record = {'path': self.path, 'bytes': len(self.binary),
                       'sha256': hashlib.sha256(self.binary).hexdigest(), 'kind': 'ELF'}

    def test_collects_real_elf_without_running_it(self):
        result = collect_elf(self.raw, [self.record])
        self.assertEqual(result[0]['sha256'], self.record['sha256'])
        self.assertTrue(result[0]['machine'])
        self.assertIn('libc.so.6', result[0]['needed'])

    def test_wrong_member_digest_fails(self):
        with self.assertRaises(ValueError):
            collect_elf(self.raw, [dict(self.record, sha256='0'*64)])

    def test_missing_member_fails(self):
        with self.assertRaises(ValueError):
            collect_elf(self.raw, [dict(self.record, path='python/missing')])

    def test_preserves_consumer_version_evidence(self):
        result = collect_elf(self.raw, [self.record])[0]
        self.assertIn('Version needs section', result['version_info'])
        self.assertIn('File: libc.so.6', result['version_info'])
        self.assertIn('Name: GLIBC_', result['version_info'])

    def test_preserves_dynamic_symbol_evidence(self):
        result = collect_elf(self.raw, [self.record])[0]
        self.assertIn("Symbol table '.dynsym'", result['dynamic_symbols'])
        self.assertRegex(result['dynamic_symbols'], r'UND\s+__libc_start_main@GLIBC_')
