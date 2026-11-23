"""TDD: safe cancellation is an explicit OPERATOR request, not worker killing.

All tests use the existing real SQLite DurableQueue. Never execute a model,
never auto-requeue or treat a running process as safely terminated.
"""
import io
import json
import sqlite3
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from ai_factory.durable_queue import DurableQueue
from ai_factory import factory_worker_recovery_status as observer
from ai_factory import offline_worker

SHA = "c" * 40
HASH = "f" * 64


class SafeCancellationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.db = self.root / "operator" / "queue.sqlite3"
        self.q = DurableQueue(self.db)

    def add(self, task):
        return self.q.enqueue(task, "feat/synthetic", SHA, HASH)

    def test_queued_cancellation_is_terminal_unclaimable_and_idempotent(self):
        self.add("task_queued")
        self.add("task_other")
        first = self.q.request_cancel("task_queued", now=1000)
        self.assertEqual(first["status"], "cancelled")
        self.assertEqual(first["next_action"], "cancelled_before_execution")
        self.assertEqual(first["attempts"], 0)
        self.assertFalse(first["execution_authorized"])
        self.assertEqual(self.q.request_cancel("task_queued", now=1001), first)
        claimed = DurableQueue(self.db).claim("worker", now=1002)
        self.assertEqual(claimed["task_id"], "task_other")
        self.assertIsNone(DurableQueue(self.db).claim("worker2", now=1002))
        self.assertEqual(self.q.read("task_queued")["attempts"], 0)
        self.assertEqual(observer.snapshot(self.db, now=1002)["cancelled_before_start"], 1)

    def test_leased_cancellation_requests_manual_stop_never_claims_execution_stopped(self):
        self.add("running_task")
        lease = self.q.claim("worker_1", now=100, lease_seconds=90)
        notice = self.q.request_cancel("running_task", now=120)
        self.assertEqual(notice["status"], "cancel_requested")
        self.assertEqual(notice["next_action"], "operator_stop_and_reconcile")
        self.assertEqual(notice["attempts"], 1)
        self.assertFalse(notice["execution_authorized"])
        self.assertEqual(self.q.request_cancel("running_task", now=125), notice)
        with self.assertRaises(ValueError):
            self.q.heartbeat("running_task", lease["lease_token"], now=130)
        with self.assertRaises(ValueError):
            self.q.finish("running_task", lease["lease_token"], "awaiting_human_review", now=130)
        self.assertIsNone(self.q.claim("other_worker", now=130))
        details = observer.snapshot(self.db, now=150)
        self.assertEqual(details["cancel_requested_active"], 1)
        self.assertEqual(details["cancel_requested_expired"], 0)
        self.assertEqual(details["manual_attention_total"], 1)
        self.assertEqual(details["cancellation_support"], "REQUEST_ONLY_NO_PROCESS_TERMINATION")
        self.assertEqual(details["cancellation_process_termination_verified"], False)
        self.assertEqual(details["automatic_retry_authorized"], False)
        self.assertFalse(details["queue_modified"])

    def test_expired_cancel_request_quarantines_but_does_not_replay_or_mark_cancelled(self):
        self.add("running")
        self.q.claim("operator_1", now=100, lease_seconds=15)
        self.q.request_cancel("running", now=102)
        at_expiry = observer.snapshot(self.db, now=115)
        self.assertEqual(at_expiry["cancel_requested_active"], 1)
        self.assertEqual(at_expiry["cancel_requested_expired"], 0)
        past = observer.snapshot(self.db, now=116)
        self.assertEqual(past["cancel_requested_expired"], 1)
        self.assertEqual(past["manual_attention_total"], 1)
        self.assertEqual(self.q.recover_expired(now=116), 1)
        item = self.q.read("running")
        self.assertEqual(item["status"], "needs_review")
        self.assertEqual(item["next_action"], "inspect_last_run")
        self.assertEqual(self.q.recover_expired(now=117), 0)
        self.assertIsNone(self.q.claim("operator_2", now=117))
        self.assertEqual(observer.snapshot(self.db, now=117)["needs_review_quarantined"], 1)
        with self.assertRaises(ValueError):
            self.q.request_cancel("running", now=118)

    def test_finished_and_unknown_tasks_cannot_be_cancelled(self):
        self.add("complete")
        leased = self.q.claim("w", now=10, lease_seconds=60)
        self.q.finish("complete", leased["lease_token"], "awaiting_human_review", now=20)
        for value in ("complete", "does_not_exist", "../evil", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.q.request_cancel(value, now=21)
        self.add("blocked_task")
        leased = self.q.claim("worker", now=30, lease_seconds=30)
        self.q.finish("blocked_task", leased["lease_token"], "blocked", now=32)
        with self.assertRaises(ValueError):
            self.q.request_cancel("blocked_task", now=33)

    def test_bad_clock_and_malformed_states_are_not_mutated(self):
        self.add("safe")
        for stamp in (True, "100", -1, float("nan"), float("inf")):
            with self.subTest(stamp=stamp), self.assertRaises(ValueError):
                self.q.request_cancel("safe", now=stamp)
        self.assertEqual(self.q.read("safe")["status"], "queued")
        with sqlite3.connect(self.db) as db:
            db.execute("UPDATE tasks SET status='unknown' WHERE task_id='safe'")
        with self.assertRaises(ValueError):
            self.q.request_cancel("safe", now=100)
        self.assertEqual(self.q.read("safe")["status"], "unknown")

    def test_atomic_claim_vs_cancel_race_cannot_double_execute(self):
        self.add("race")
        gate = threading.Barrier(3)
        errors = []
        outputs = []

        def cancel():
            try:
                gate.wait()
                outputs.append(("cancel", DurableQueue(self.db).request_cancel("race", now=100)))
            except Exception as exc:
                errors.append(type(exc).__name__)

        def claim():
            try:
                gate.wait()
                outputs.append(("claim", DurableQueue(self.db).claim("worker", now=100)))
            except Exception as exc:
                errors.append(type(exc).__name__)

        t1 = threading.Thread(target=cancel)
        t2 = threading.Thread(target=claim)
        t1.start()
        t2.start()
        gate.wait()
        t1.join(timeout=10)
        t2.join(timeout=10)
        self.assertFalse(t1.is_alive())
        self.assertFalse(t2.is_alive())
        self.assertFalse(errors)
        item = self.q.read("race")
        self.assertIn(item["status"], ("cancel_requested", "cancelled"))
        self.assertEqual(len(outputs), 2)
        if item["status"] == "cancelled":
            self.assertIsNone(dict(outputs)["claim"])
            self.assertEqual(item["attempts"], 0)
        else:
            self.assertEqual(dict(outputs)["claim"]["task_id"], "race")
            self.assertEqual(item["attempts"], 1)
        self.assertIsNone(self.q.claim("second_worker", now=110))

    def test_operator_cli_requests_cancellation_without_worker_or_model(self):
        self.add("cli_queued")
        output = io.StringIO()
        with redirect_stdout(output):
            code = offline_worker.main([
                "--queue-db", str(self.db),
                "--journal", str(self.root / "operator" / "journal"),
                "--task-dir", str(self.root / "tasks"),
                "request-cancel", "cli_queued",
            ])
        self.assertEqual(code, 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["status"], "cancelled")
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(self.q.read("cli_queued")["status"], "cancelled")

    def test_no_sensitive_fields_in_readonly_cancellation_report(self):
        self.add("private_task_id")
        lease = self.q.claim("worker-secret", now=100, lease_seconds=20)
        self.q.request_cancel("private_task_id", now=101)
        data = json.dumps(observer.snapshot(self.db, now=121), sort_keys=True)
        for leaked in ("private_task_id", "worker-secret", lease["lease_token"], HASH, SHA):
            self.assertNotIn(leaked, data)
        self.assertIn('"cancel_requested_expired": 1', data)
        self.assertIn('"manual_attention_total": 1', data)

    def test_invalid_cancel_requested_without_lease_is_rejected_by_observer(self):
        self.add("fake")
        with sqlite3.connect(self.db) as db:
            db.execute("UPDATE tasks SET status='cancel_requested' WHERE task_id='fake'")
        with self.assertRaises(ValueError):
            observer.snapshot(self.db, now=100)


if __name__ == "__main__":
    unittest.main()
