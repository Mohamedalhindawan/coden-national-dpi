import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ai_factory import factory_r2_build_preflight as review
from ai_factory import factory_build_materials as materials


class BuildPreflightTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.stage = Path(temp.name) / 'stage'
        self.source = Path(temp.name) / 'source'
        self.stage.mkdir()
        self.source.mkdir()
        self.raw = b'synthetic archive'
        self.source_pins = {name: (len(self.raw), hashlib.sha256(self.raw).hexdigest())
                            for name in review.SOURCE_PINS}
        self.tool_pins = {'fixture.whl': (7, hashlib.sha256(b'fixture').hexdigest())}
        for name in self.source_pins:
            (self.source / name).write_bytes(self.raw)
        self.stack = [patch.object(review, 'SOURCE_PINS', self.source_pins),
                      patch.object(materials, 'PINS', self.tool_pins),
                      patch.object(review, 'reproduce_inventory', return_value=b'fixture inventory')]
        for item in self.stack:
            item.start()
            self.addCleanup(item.stop)

    def test_complete_observation_does_not_authorize_build(self):
        (self.stage / 'fixture.whl').write_bytes(b'fixture')
        result = review.review_preflight(self.stage, self.source)
        self.assertTrue(result['input_bytes_complete'])
        self.assertTrue(result['source_inventory_reproduced'])
        for key in ('independent_review', 'immutable_mount_verified', 'amendment_adopted', 'build_authorized', 'installation_authorized', 'release_authorized'):
            self.assertIs(result[key], False)

    def test_missing_tool_does_not_hide_valid_source(self):
        result = review.review_preflight(self.stage, self.source)
        self.assertFalse(result['input_bytes_complete'])
        self.assertTrue(result['source_inventory_reproduced'])
        self.assertEqual(result['missing_build_materials'], ['fixture.whl'])

    def test_modified_or_missing_source_blocks(self):
        (self.stage / 'fixture.whl').write_bytes(b'fixture')
        path = self.source / review.R2_ARCHIVE
        path.write_bytes(b'other')
        self.assertFalse(review.review_preflight(self.stage, self.source)['input_bytes_complete'])
        path.unlink()
        self.assertFalse(review.review_preflight(self.stage, self.source)['source_inventory_reproduced'])

    def test_inventory_failure_blocks_even_when_pins_match(self):
        (self.stage / 'fixture.whl').write_bytes(b'fixture')
        with patch.object(review, 'reproduce_inventory', side_effect=ValueError('mismatch')):
            result = review.review_preflight(self.stage, self.source)
        self.assertFalse(result['input_bytes_complete'])
        self.assertFalse(result['source_inventory_reproduced'])

    def test_symlink_archive_is_not_accepted(self):
        path = self.source / review.R2_ARCHIVE
        path.unlink()
        path.symlink_to(self.source / next(name for name in self.source_pins if name != review.R2_ARCHIVE))
        result = review.review_preflight(self.stage, self.source)
        self.assertFalse(result['source_inventory_reproduced'])
        self.assertFalse(result['input_bytes_complete'])
