import hashlib
import io
import tarfile
import unittest
from ai_factory.factory_python_archive import inventory


def fixture(entries):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w:gz') as tar:
        for name, data in entries:
            m = tarfile.TarInfo(name)
            m.size = len(data)
            tar.addfile(m, io.BytesIO(data))
    return output.getvalue()


class PythonArchiveTest(unittest.TestCase):
    def test_exact_archive_notice_and_native_inventory(self):
        raw = fixture([('python/LICENSE', b'notice'), ('python/lib/pip/_vendor/vendor.txt', b'packaging==26.3'), ('python/bin/python3.13', b'\x7fELFfixture')])
        out = inventory(raw, hashlib.sha256(raw).hexdigest())
        self.assertEqual(out['native'][0]['path'], 'python/bin/python3.13')
        self.assertEqual(len(out['text_evidence']), 2)
        self.assertFalse(out['release_authorized'])
        self.assertFalse(out['executed'])

    def test_wrong_hash_rejected(self):
        raw = fixture([('python/LICENSE', b'notice')])
        with self.assertRaises(ValueError):
            inventory(raw, '0'*64)

    def test_escape_rejected(self):
        raw = fixture([('python/../escape', b'x')])
        with self.assertRaises(ValueError):
            inventory(raw, hashlib.sha256(raw).hexdigest())

    def test_duplicate_rejected(self):
        raw = fixture([('python/LICENSE', b'a'), ('python/LICENSE', b'b')])
        with self.assertRaises(ValueError):
            inventory(raw, hashlib.sha256(raw).hexdigest())
