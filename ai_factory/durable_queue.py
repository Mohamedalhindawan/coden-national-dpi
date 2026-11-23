"""Local SQLite job tracking and leasing for offline *synthetic* factory tasks.

NOT an executor or approval authority. It stores no task descriptions, prompts,
secrets or full artifacts; an expired lease or pending cancel request goes to NEEDS_REVIEW, never to an
automatically runnable state. Operator-controlled store and trusted caller only.
"""

from contextlib import closing
from hashlib import sha256
import math
import os
from pathlib import Path
import re
import sqlite3
import time
from uuid import uuid4

from . import checkpoint

DIGEST = re.compile(r'[a-f0-9]{64}\Z')
OUTCOMES = frozenset({'awaiting_human_review', 'failed', 'blocked'})


class DurableQueue:
    def __init__(self, db_path):
        self.path = Path(db_path)
        if self.path.is_symlink() or self.path.parent.is_symlink():
            raise ValueError('symlink queue database forbidden')
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with closing(self._connect()) as db:
            db.execute('''CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY, branch TEXT NOT NULL, commit_sha TEXT NOT NULL,
                task_sha256 TEXT NOT NULL, status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                lease_token TEXT, lease_until REAL, next_action TEXT,
                created_at REAL NOT NULL, updated_at REAL NOT NULL
            )''')
        os.chmod(self.path, 0o600)

    def _connect(self):
        if self.path.is_symlink():
            raise ValueError('symlink queue database forbidden')
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA busy_timeout=5000')
        db.execute('PRAGMA synchronous=FULL')
        db.execute('PRAGMA trusted_schema=OFF')
        return db

    @staticmethod
    def _now(value):
        now = time.time() if value is None else value
        if type(now) not in (int, float) or not math.isfinite(now) or now < 0:
            raise ValueError('invalid timestamp')
        return float(now)

    @staticmethod
    def _duration(value):
        if type(value) is not int or not 1 <= value <= 3600:
            raise ValueError('invalid lease duration')
        return value

    @staticmethod
    def _summary(row):
        if row is None:
            raise ValueError('unknown task')
        return dict(task_id=row['task_id'], branch=row['branch'], commit=row['commit_sha'],
                    task_sha256=row['task_sha256'], status=row['status'],
                    attempts=row['attempts'], next_action=row['next_action'],
                    execution_authorized=False)

    def enqueue(self, task_id, branch, commit, task_sha256):
        checkpoint._id(task_id)
        checkpoint._branch(branch)
        checkpoint._commit(commit)
        if not branch or not commit or not isinstance(task_sha256, str) or not DIGEST.fullmatch(task_sha256):
            raise ValueError('branch, commit and SHA-256 required')
        now = self._now(None)
        with closing(self._connect()) as db:
            try:
                with db:
                    db.execute('INSERT INTO tasks(task_id,branch,commit_sha,task_sha256,status,created_at,updated_at) '
                               'VALUES(?,?,?,?,?,?,?)',
                               (task_id, branch, commit, task_sha256, 'queued', now, now))
            except sqlite3.IntegrityError as exc:
                raise ValueError('task already exists') from exc
        return self.read(task_id)

    def read(self, task_id):
        checkpoint._id(task_id)
        with closing(self._connect()) as db:
            return self._summary(db.execute('SELECT * FROM tasks WHERE task_id=?', (task_id,)).fetchone())

    def claim(self, worker_id, *, now=None, lease_seconds=60, task_id=None):
        checkpoint._id(worker_id)
        if task_id is not None:
            checkpoint._id(task_id)
        stamp = self._now(now)
        self._duration(lease_seconds)
        with closing(self._connect()) as db:
            with db:
                db.execute('BEGIN IMMEDIATE')
                if task_id is None:
                    row = db.execute("SELECT task_id FROM tasks WHERE status='queued' "
                                     'ORDER BY created_at,task_id LIMIT 1').fetchone()
                else:
                    # Exact-task binding is crucial: a supervisor monitoring
                    # cancellation of task A must never kill task B's child.
                    row = db.execute(
                        "SELECT task_id FROM tasks WHERE status='queued' AND task_id=?",
                        (task_id,)
                    ).fetchone()
                if row is None:
                    return None
                token = uuid4().hex
                db.execute("UPDATE tasks SET status='leased', attempts=attempts+1, "
                           'lease_token=?,lease_until=?,updated_at=? WHERE task_id=?',
                           (token, stamp + lease_seconds, stamp, row['task_id']))
                info = self._summary(db.execute('SELECT * FROM tasks WHERE task_id=?',
                                                (row['task_id'],)).fetchone())
                return dict(info, worker_id=worker_id, lease_token=token,
                            lease_until=stamp + lease_seconds)

    def heartbeat(self, task_id, lease_token, *, now=None, extend_seconds=60):
        checkpoint._id(task_id)
        stamp = self._now(now)
        self._duration(extend_seconds)
        if not isinstance(lease_token, str) or not re.fullmatch(r'[a-f0-9]{32}', lease_token):
            raise ValueError('invalid lease token')
        with closing(self._connect()) as db:
            with db:
                db.execute('BEGIN IMMEDIATE')
                cur = db.execute("UPDATE tasks SET lease_until=MAX(lease_until,?),updated_at=? "
                                 "WHERE task_id=? AND status='leased' AND lease_token=? AND lease_until>=?",
                                 (stamp + extend_seconds, stamp, task_id, lease_token, stamp))
                if cur.rowcount != 1:
                    raise ValueError('invalid, stale or expired lease')
                return self._summary(db.execute('SELECT * FROM tasks WHERE task_id=?',
                                                (task_id,)).fetchone())

    def finish(self, task_id, lease_token, outcome, *, now=None):
        checkpoint._id(task_id)
        stamp = self._now(now)
        if outcome not in OUTCOMES:
            raise ValueError('not a permitted queue outcome')
        if not isinstance(lease_token, str) or not re.fullmatch(r'[a-f0-9]{32}', lease_token):
            raise ValueError('invalid lease token')
        with closing(self._connect()) as db:
            with db:
                db.execute('BEGIN IMMEDIATE')
                cur = db.execute('UPDATE tasks SET status=?,lease_token=NULL,lease_until=NULL, '
                                 'next_action=?,updated_at=? WHERE task_id=? AND status=? '
                                 'AND lease_token=? AND lease_until>=?',
                                 (outcome, 'human_review' if outcome == 'awaiting_human_review'
                                  else 'inspect_last_run', stamp, task_id, 'leased', lease_token, stamp))
                if cur.rowcount != 1:
                    raise ValueError('invalid or expired lease')
                return self._summary(db.execute('SELECT * FROM tasks WHERE task_id=?',
                                                (task_id,)).fetchone())

    def request_cancel(self, task_id, *, now=None):
        """Operator-only cancellation request; NEVER signal a process or retry.

        An unclaimed task can be safely marked cancelled. A leased task only
        receives a cancel REQUEST and must be stopped/reconciled by its trusted
        supervisor. Heartbeat/finish cannot complete a cancel_requested lease.
        BEGIN IMMEDIATE serializes this transition against competing claims.
        """
        checkpoint._id(task_id)
        stamp = self._now(now)
        with closing(self._connect()) as db:
            with db:
                db.execute('BEGIN IMMEDIATE')
                row = db.execute(
                    'SELECT * FROM tasks WHERE task_id=?', (task_id,)
                ).fetchone()
                if row is None:
                    raise ValueError('unknown task')
                state = row['status']
                token = row['lease_token']
                until = row['lease_until']
                if state in ('leased', 'cancel_requested'):
                    if (not isinstance(token, str)
                            or re.fullmatch(r'[a-f0-9]{32}', token) is None
                            or type(until) not in (float, int)
                            or not math.isfinite(until) or until < 0):
                        raise ValueError('untrusted running lease metadata')
                elif token is not None or until is not None:
                    raise ValueError('unexpected lease attached to non-running task')
                if state in ('cancelled', 'cancel_requested'):
                    # Purely idempotent read: do not alter a previous request.
                    return self._summary(row)
                if state == 'queued':
                    new_state = 'cancelled'
                    next_action = 'cancelled_before_execution'
                elif state == 'leased':
                    new_state = 'cancel_requested'
                    next_action = 'operator_stop_and_reconcile'
                else:
                    raise ValueError('task not cancellable from current state')
                cur = db.execute(
                    'UPDATE tasks SET status=?,next_action=?,updated_at=? '
                    'WHERE task_id=? AND status=?',
                    (new_state, next_action, stamp, task_id, state))
                if cur.rowcount != 1:
                    raise ValueError('cancellation race; manual reconciliation required')
                return self._summary(db.execute(
                    'SELECT * FROM tasks WHERE task_id=?', (task_id,)
                ).fetchone())

    def recover_expired(self, *, now=None):
        """Quarantine expired leases for human inspection; NEVER re-enqueue."""
        stamp = self._now(now)
        with closing(self._connect()) as db:
            with db:
                db.execute('BEGIN IMMEDIATE')
                count = db.execute("UPDATE tasks SET status='needs_review',lease_token=NULL,"
                                   "lease_until=NULL,next_action='inspect_last_run',updated_at=? "
                                   "WHERE status IN ('leased','cancel_requested') AND lease_until<?", (stamp, stamp)).rowcount
                return count
