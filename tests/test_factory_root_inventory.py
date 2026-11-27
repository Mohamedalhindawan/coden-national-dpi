import hashlib
import io
import tarfile
import unittest
from unittest.mock import patch
from ai_factory import factory_root_inventory as inv


def archive(rows):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode='w:gz') as tar:
        for name, body in rows:
            member = tarfile.TarInfo(name)
            member.size = len(body)
            tar.addfile(member, io.BytesIO(body))
    return out.getvalue()


class InventoryTests(unittest.TestCase):
    def test_exact_archive_reproduces_required_and_optional_members(self):
        rows = [('source/'+root+'/openhands/'+part+'/fixture.py', b'pass\n')
                for root, part in inv.ROOTS.items()]
        rows.append(('source/openhands-sdk/openhands/sdk/README.md', b'fixture'))
        raw = archive(rows)
        with patch.object(inv, 'ARCHIVE_SHA256', hashlib.sha256(raw).hexdigest()), \
             patch.object(inv, 'ARCHIVE_FILES', 5), patch.object(inv, 'PAYLOAD_FILES', 5):
            result = inv._derive(raw)
        self.assertTrue(result['roots']['openhands-sdk']['openhands/sdk/fixture.py']['required'])
        self.assertFalse(result['roots']['openhands-sdk']['openhands/sdk/README.md']['required'])
        self.assertFalse(result['build_authorized'])

    def test_modified_bytes_rejected_before_archive_parse(self):
        with self.assertRaises(ValueError):
            inv._derive(b'not a pinned archive')

    def test_unsafe_or_duplicate_members_rejected(self):
        for rows in ([('source/../outside', b'x')], [('source/a', b'x'), ('source/a', b'y')]):
            raw = archive(rows)
            with patch.object(inv, 'ARCHIVE_SHA256', hashlib.sha256(raw).hexdigest()), \
                 self.assertRaises(ValueError):
                inv._derive(raw)

    def test_missing_roots_rejected(self):
        raw = archive([('source/openhands-sdk/openhands/sdk/a.py', b'pass')])
        with patch.object(inv, 'ARCHIVE_SHA256', hashlib.sha256(raw).hexdigest()), \
             patch.object(inv, 'ARCHIVE_FILES', 1), patch.object(inv, 'PAYLOAD_FILES', 1), \
             self.assertRaises(ValueError):
            inv._derive(raw)
