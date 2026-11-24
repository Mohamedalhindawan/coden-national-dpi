"""P1 process-loss drills using durable stores and the existing synthetic recipe."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ai_factory import checkpoint, durable_queue, offline_worker, project, reconcile

COMMIT = "d" * 40
BRANCH = "feat/p1-recovery"


class ProcessLossRecoveryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.tasks = self.root / "tasks"
        self.tasks.mkdir()
        self.journal = self.root / "journal"
        self.out = self.root / "outputs"
        self.out.mkdir()
        self.db = self.root / "queue.sqlite3"
        self.q = durable_queue.DurableQueue(self.db)
        task = json.loads(project.EXAMPLE.read_text(encoding="utf-8"))
        self.id = task["id"]
        (self.tasks / (self.id + ".json")).write_text(json.dumps(task), encoding="utf-8")

    def child(self, code):
        # Fixed first-party test program, no task-controlled shell or code.
        env = {k: os.environ[k] for k in ("PATH", "CODEN_REQUIRE_SANDBOX") if k in os.environ}
        env.update({"LANG": "C.UTF-8", "HOME": str(self.root)})
        completed = subprocess.run(
            [sys.executable, "-c", code, str(self.db), str(self.journal),
             str(self.tasks), str(self.out), self.id, BRANCH, COMMIT],
            env=env, capture_output=True, timeout=40, check=False)
        self.assertEqual(completed.returncode, 73, completed.stderr.decode(errors="replace")[:2000])

    def submit(self, q):
        return offline_worker.submit_idempotent(q, self.journal, self.tasks,
                                                self.id, branch=BRANCH, commit=COMMIT)

    def snapshot(self):
        return {str(p.relative_to(self.out)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.out.rglob("*") if p.is_file()}

    def test_process_loss_between_journal_and_enqueue_leaves_orphan(self):
        self.child("""
import os, sys
from ai_factory import durable_queue, offline_worker
db, journal, tasks, out, task_id, branch, commit = sys.argv[1:]
q = durable_queue.DurableQueue(db)
def fail(*args, **kwargs):
    os._exit(73)
q.enqueue = fail
offline_worker.submit_idempotent(q, journal, tasks, task_id, branch=branch, commit=commit)
""")
        reopened = durable_queue.DurableQueue(self.db)
        self.assertEqual(checkpoint.read(self.journal, self.id)["status"], "prepared")
        report = reconcile.scan(self.db, self.journal, task_dir=self.tasks)
        self.assertEqual(report["conditions"], {"orphan_journal": 1})
        self.assertFalse(report["safe_to_auto_retry"])
        with self.assertRaises((ValueError, FileExistsError)):
            self.submit(reopened)
        self.assertIsNone(reopened.claim("replacement"))
        self.assertEqual(self.snapshot(), {})

    def test_process_loss_after_real_artifact_before_finish_preserves_review(self):
        if not project.supported_host() and os.getenv("CODEN_REQUIRE_SANDBOX") != "1":
            self.skipTest("requires pinned Linux sandbox")
        self.submit(self.q)
        self.child("""
import os, sys
from ai_factory import durable_queue, offline_worker
db, journal, tasks, out, task_id, branch, commit = sys.argv[1:]
q = durable_queue.DurableQueue(db)
def fail(task_id, token, outcome, **kwargs):
    if outcome != "awaiting_human_review":
        os._exit(74)
    os._exit(73)
q.finish = fail
offline_worker.work_once(q, journal, tasks, out, worker_id="crash_worker", lease_seconds=60)
""")
        reopened = durable_queue.DurableQueue(self.db)
        self.assertEqual(reopened.read(self.id)["status"], "leased")
        self.assertEqual(checkpoint.read(self.journal, self.id)["status"], "awaiting_human_review")
        self.assertEqual(reconcile.scan(self.db, self.journal, self.tasks)["conditions"],
                         {"journal_ahead_of_queue": 1})
        candidates = list(self.out.glob("*/candidate.pyz"))
        self.assertEqual(len(candidates), 1)
        receipt = json.loads((candidates[0].parent / "review.json").read_text())
        self.assertEqual(receipt["sha256"], hashlib.sha256(candidates[0].read_bytes()).hexdigest())
        self.assertFalse(receipt["release_authorized"])
        before = self.snapshot()
        self.assertEqual(reopened.recover_expired(now=10**12), 1)
        self.assertEqual(self.submit(reopened)["status"], "needs_review")
        self.assertIsNone(offline_worker.work_once(reopened, self.journal, self.tasks,
                                                   self.out, worker_id="replacement"))
        self.assertEqual(reopened.read(self.id)["attempts"], 1)
        self.assertEqual(reconcile.scan(self.db, self.journal, self.tasks)["conditions"],
                         {"manual_review_required": 1})
        self.assertEqual(before, self.snapshot())
