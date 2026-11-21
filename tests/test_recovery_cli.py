"""Check offline recovery CLI never dispatches models or exposes credentials."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ai_factory import checkpoint
from test_recovery_policy import task, route


class RecoveryCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'decision.json'
        self.data = {
            'observation': {'kind': 'quota_exceeded'},
            'task': task(),
            'routes': [route()],
            'failed_provider': 'codex_sub',
        }

    def invoke(self, *args):
        self.source.write_text(json.dumps(self.data), encoding='utf-8')
        return subprocess.run([sys.executable, '-m', 'ai_factory.recovery_cli',
                               '--input', str(self.source), *args],
                              text=True, capture_output=True,
                              env=dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1])))

    def test_offline_proposal_without_execution(self):
        r = self.invoke()
        self.assertEqual(r.returncode, 0, r.stderr)
        result = json.loads(r.stdout)
        self.assertEqual(result['plan']['decision'], 'propose_fallback')
        self.assertFalse(result['plan']['execution_authorized'])
        self.assertNotIn('journal', result)

    def test_optional_recording_requires_operator_created_journal(self):
        store = self.root / 'journals'
        checkpoint.create(store, 'sample_1', branch='feat/demo', commit='d' * 40)
        r = self.invoke('--store', str(store), '--task-id', 'sample_1', '--event-key', 'error1')
        self.assertEqual(r.returncode, 0, r.stderr)
        result = json.loads(r.stdout)
        self.assertEqual(result['journal']['status'], 'paused')
        self.assertFalse(result['journal']['execution_authorized'])

    def test_refuses_missing_journal_or_partial_options(self):
        store = self.root / 'journals'
        self.assertNotEqual(self.invoke('--store', str(store)).returncode, 0)
        self.assertNotEqual(self.invoke('--store', str(store), '--task-id', 'missing').returncode, 0)

    def test_rejects_untrusted_extra_fields_and_does_not_echo_secret(self):
        self.data['routes'][0]['api_key'] = 'secret-never-log-me'
        r = self.invoke()
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn('secret-never-log-me', r.stderr + r.stdout)

    def test_input_size_bound_and_symlink_are_rejected(self):
        self.data['padding'] = 'a' * 50000
        self.assertNotEqual(self.invoke().returncode, 0)
        self.data.pop('padding')
        link = self.root / 'link.json'
        link.symlink_to(self.source)
        self.source.write_text(json.dumps(self.data))
        r = subprocess.run([sys.executable, '-m', 'ai_factory.recovery_cli', '--input', str(link)],
                           capture_output=True, text=True,
                           env=dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1])))
        self.assertNotEqual(r.returncode, 0)


if __name__ == '__main__':
    unittest.main()
