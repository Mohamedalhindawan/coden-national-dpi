"""Durable offline job *tracking* tests (queue does not execute tools/models)."""
import hashlib
import os
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from ai_factory import durable_queue

HASH = hashlib.sha256(b'synthetic-only').hexdigest()
COMMIT = 'c' * 40


class DurableQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'operator' / 'factory.sqlite3'
        self.queue = durable_queue.DurableQueue(self.path)

    def enqueue(self, task_id='sample_task'):
        return self.queue.enqueue(task_id, 'feat/offline', COMMIT, HASH)

    def test_persist_metadata_without_payload_or_auth(self):
        item = self.enqueue()
        self.assertEqual(item['status'], 'queued')
        self.assertFalse(item['execution_authorized'])
        self.assertEqual(durable_queue.DurableQueue(self.path).read('sample_task')['task_sha256'], HASH)
        db = self.path.read_bytes()
        self.assertNotIn(b'synthetic-only', db)
        self.assertEqual(os.stat(self.path).st_mode & 0o777, 0o600)

    def test_claim_is_exclusive_across_connections(self):
        self.enqueue()
        a = self.queue.claim('worker_a', now=1000, lease_seconds=30)
        b = durable_queue.DurableQueue(self.path).claim('worker_b', now=1000, lease_seconds=30)
        self.assertEqual(a['task_id'], 'sample_task')
        self.assertIsNone(b)
        self.assertFalse(a['execution_authorized'])
        self.assertEqual(self.queue.read('sample_task')['attempts'], 1)
        self.assertNotIn('lease_token', self.queue.read('sample_task'))

    def test_heartbeat_and_review_gate(self):
        self.enqueue()
        lease = self.queue.claim('worker_a', now=1000, lease_seconds=30)
        self.queue.heartbeat('sample_task', lease['lease_token'], now=1010, extend_seconds=60)
        with self.assertRaises(ValueError):
            self.queue.finish('sample_task', 'bad-token', 'awaiting_human_review', now=1011)
        done = self.queue.finish('sample_task', lease['lease_token'], 'awaiting_human_review', now=1035)
        self.assertEqual(done['status'], 'awaiting_human_review')
        self.assertFalse(done['execution_authorized'])
        self.assertIsNone(self.queue.claim('worker_b', now=1036))

    def test_crashed_worker_never_auto_requeues(self):
        self.enqueue()
        lease = self.queue.claim('worker_a', now=1000, lease_seconds=15)
        self.assertEqual(self.queue.recover_expired(now=1016), 1)
        r = self.queue.read('sample_task')
        self.assertEqual(r['status'], 'needs_review')
        self.assertEqual(r['next_action'], 'inspect_last_run')
        self.assertIsNone(self.queue.claim('worker_b', now=1030))
        with self.assertRaises(ValueError):
            self.queue.finish('sample_task', lease['lease_token'], 'awaiting_human_review', now=1030)

    def test_stale_leases_do_not_accept_heartbeat_or_finish(self):
        self.enqueue()
        lease = self.queue.claim('worker_a', now=1000, lease_seconds=10)
        with self.assertRaises(ValueError):
            self.queue.heartbeat('sample_task', lease['lease_token'], now=1011, extend_seconds=10)
        with self.assertRaises(ValueError):
            self.queue.finish('sample_task', lease['lease_token'], 'blocked', now=1011)

    def test_duplicate_enqueue_does_not_replace_work(self):
        self.enqueue()
        with self.assertRaises(ValueError):
            self.enqueue()
        self.assertEqual(self.queue.read('sample_task')['attempts'], 0)

    def test_reject_untrusted_status_and_invalid_inputs(self):
        for task_id in ('../escape', '', 'x'*65):
            with self.assertRaises(ValueError):
                self.queue.enqueue(task_id, 'feat/offline', COMMIT, HASH)
        with self.assertRaises(ValueError):
            self.queue.enqueue('ok', 'feat/offline', COMMIT, 'sha')
        self.enqueue()
        lease = self.queue.claim('worker_a', now=1000, lease_seconds=10)
        with self.assertRaises(ValueError):
            self.queue.finish('sample_task', lease['lease_token'], 'approved', now=1002)
        with self.assertRaises(ValueError):
            self.queue.claim('worker_b', now=1002, lease_seconds=0)

    def test_parallel_workers_cannot_claim_same_task(self):
        self.enqueue()
        out = []
        gate = threading.Barrier(3)
        def run(name):
            gate.wait()
            out.append(durable_queue.DurableQueue(self.path).claim(name, now=1000))
        a = threading.Thread(target=run, args=('a',))
        b = threading.Thread(target=run, args=('b',))
        a.start(); b.start(); gate.wait(); a.join(); b.join()
        self.assertEqual(sum(x is not None for x in out), 1)

    def test_database_symlink_rejected(self):
        link = Path(self.temp.name) / 'symlink.sqlite3'
        link.symlink_to(self.path)
        with self.assertRaises(ValueError):
            durable_queue.DurableQueue(link)

    def test_finish_blocked_without_approval(self):
        self.enqueue()
        lease = self.queue.claim('worker_a', now=1000)
        final = self.queue.finish('sample_task', lease['lease_token'], 'blocked', now=1002)
        self.assertEqual(final['status'], 'blocked')
        self.assertFalse(final['execution_authorized'])


if __name__ == '__main__':
    unittest.main()
