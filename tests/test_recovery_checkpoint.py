"""Verify that offline fallback recommendations only pause a persistent task."""
import tempfile
import unittest
from pathlib import Path
from ai_factory import checkpoint, recovery_checkpoint
from test_recovery_policy import task, route

SHA = 'b' * 40


class RecoveryCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Path(self.temp.name) / 'journals'
        checkpoint.create(self.store, 'factory_job_01', branch='feat/offline', commit=SHA)

    def apply(self, error, *, task_override=None, routes=None, event_key='reason1', failed_provider='codex_sub'):
        return recovery_checkpoint.record_recovery(
            self.store, 'factory_job_01', error, task_override or task(),
            [route()] if routes is None else routes,
            failed_provider=failed_provider, event_key=event_key,
        )

    def test_quota_exceeded_is_persisted_with_review_only(self):
        result = self.apply({'kind':'quota_exceeded'})
        self.assertEqual(result['journal']['status'], 'paused')
        self.assertEqual(result['journal']['pause_reason'], 'quota_exceeded')
        self.assertEqual(result['journal']['next_action'], 'review_fallback')
        self.assertEqual(result['plan']['decision'], 'propose_fallback')
        self.assertFalse(result['journal']['execution_authorized'])
        self.assertEqual(checkpoint.read(self.store, 'factory_job_01')['event_count'], 2)

    def test_rate_limit_keeps_distinct_reason(self):
        result = self.apply({'http_status': 429})
        self.assertEqual(result['journal']['pause_reason'], 'rate_limited')
        self.assertEqual(result['journal']['status'], 'paused')

    def test_unknown_auth_failure_blocks_without_provider_switch(self):
        result = self.apply({'http_status': 401})
        self.assertEqual(result['journal']['status'], 'blocked')
        self.assertEqual(result['plan']['candidate'], None)
        self.assertEqual(result['journal']['next_action'], 'manual_security_review')

    def test_ineligible_fallback_is_paused(self):
        result = self.apply({'kind':'quota_exceeded'}, routes=[route(approved=False)])
        self.assertEqual(result['plan']['decision'], 'pause')
        self.assertEqual(result['journal']['next_action'], 'wait_for_authorized_provider')

    def test_idempotent_duplicate_report_does_not_append_twice(self):
        first = self.apply({'kind':'quota_exceeded'}, event_key='same_failure')
        second = self.apply({'kind':'quota_exceeded'}, event_key='same_failure')
        self.assertEqual(first['journal']['event_count'], second['journal']['event_count'])
        with self.assertRaises(ValueError):
            self.apply({'kind':'worker_failed'}, event_key='same_failure')

    def test_reject_malicious_raw_provider_error_before_journal_write(self):
        with self.assertRaises(ValueError):
            self.apply({'kind':'quota_exceeded','raw_message':'api key leaked'})
        self.assertEqual(checkpoint.read(self.store, 'factory_job_01')['event_count'], 1)

    def test_cannot_pause_task_after_review_gate(self):
        checkpoint.record(self.store, 'factory_job_01', event='review_requested')
        with self.assertRaises(ValueError):
            self.apply({'kind':'quota_exceeded'})
        self.assertEqual(checkpoint.read(self.store, 'factory_job_01')['status'], 'awaiting_human_review')


if __name__ == '__main__':
    unittest.main()
