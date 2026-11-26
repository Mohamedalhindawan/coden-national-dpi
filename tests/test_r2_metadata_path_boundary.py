import hashlib
import tempfile
import unittest
from pathlib import Path
from ai_factory.modeb_import_probe import _check_metadata_digest


class MetadataPathBoundaryTest(unittest.TestCase):
    def test_regular_nested_path_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / 'nested' / 'metadata.json'
            target.parent.mkdir()
            target.write_bytes(b'{}')
            _check_metadata_digest(target, hashlib.sha256(b'{}').hexdigest())

    def test_intermediate_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / 'real'
            real.mkdir()
            (real / 'metadata.json').write_bytes(b'{}')
            (root / 'alias').symlink_to(real, target_is_directory=True)
            with self.assertRaises((OSError, ValueError)):
                _check_metadata_digest(root / 'alias' / 'metadata.json', hashlib.sha256(b'{}').hexdigest())

    def test_parent_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'nested').mkdir()
            (root / 'metadata.json').write_bytes(b'{}')
            with self.assertRaises((OSError, ValueError)):
                _check_metadata_digest(root / 'nested' / '..' / 'metadata.json', hashlib.sha256(b'{}').hexdigest())
