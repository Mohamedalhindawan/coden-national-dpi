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
