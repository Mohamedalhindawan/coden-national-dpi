"""Persistent local task queue with leases and fenced worker ownership.

This is a single-host SQLite prototype. It stores JSON task envelopes and
receipts only; it does not execute task payloads or invoke external providers.
"""
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone


class QueueError(ValueError):
    pass


class PersistentTaskQueue:
    def __init__(self, database=":memory:"):
        self.db = sqlite3.connect(str(database), timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS queue_tasks (
            task_id TEXT PRIMARY KEY,
            payload_json TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            status TEXT NOT NULL,
            priority INTEGER NOT NULL,
            max_attempts INTEGER NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            worker_id TEXT,
            lease_token TEXT,
            lease_expires REAL,
            result_json TEXT,
            last_error TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS queue_claim_idx
        ON queue_tasks(status, priority DESC, created_at, task_id);
        CREATE TABLE IF NOT EXISTS queue_events (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL REFERENCES queue_tasks(task_id),
            event TEXT NOT NULL,
            actor TEXT NOT NULL,
            details_json TEXT NOT NULL,
            occurred_at REAL NOT NULL
        );
        CREATE TRIGGER IF NOT EXISTS queue_events_no_update
        BEFORE UPDATE ON queue_events BEGIN
            SELECT RAISE(ABORT, 'queue events are append-only');
        END;
        CREATE TRIGGER IF NOT EXISTS queue_events_no_delete
        BEFORE DELETE ON queue_events BEGIN
            SELECT RAISE(ABORT, 'queue events are append-only');
        END;
        """)

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).timestamp()

    @staticmethod
    def _json_object(value, label):
        if not isinstance(value, dict):
            raise QueueError(label + " must be a JSON object")
        try:
            return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise QueueError(label + " must contain valid JSON values") from exc

    def _row(self, task_id):
        row = self.db.execute("SELECT * FROM queue_tasks WHERE task_id=?", (task_id,)).fetchone()
        if row is None:
            raise QueueError("Unknown task: " + str(task_id))
        result = dict(row)
        result["payload"] = json.loads(result.pop("payload_json"))
        if result["result_json"] is not None:
            result["result"] = json.loads(result.pop("result_json"))
        else:
            result.pop("result_json")
            result["result"] = None
        return result

    def _event(self, task_id, event, actor, details, now):
        self.db.execute(
            "INSERT INTO queue_events(task_id,event,actor,details_json,occurred_at) VALUES(?,?,?,?,?)",
            (task_id, event, actor, json.dumps(details or {}, sort_keys=True), now),
        )

    def enqueue(self, task_id, payload, max_attempts=1, priority=0, now=None):
        if not isinstance(task_id, str) or not task_id.strip():
            raise QueueError("task_id is required")
        payload_json = self._json_object(payload, "payload")
        if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or not 1 <= max_attempts <= 4:
            raise QueueError("max_attempts must be an integer between 1 and 4")
        if isinstance(priority, bool) or not isinstance(priority, int) or not -100 <= priority <= 100:
            raise QueueError("priority must be an integer between -100 and 100")
        stamp = self._now() if now is None else float(now)
        digest = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            existing = self.db.execute("SELECT * FROM queue_tasks WHERE task_id=?", (task_id,)).fetchone()
            if existing:
                if existing["payload_hash"] != digest or existing["max_attempts"] != max_attempts or existing["priority"] != priority:
                    raise QueueError("Idempotency key already exists with different task parameters")
                self.db.execute("COMMIT")
                return self._row(task_id)
            self.db.execute(
                """INSERT INTO queue_tasks(task_id,payload_json,payload_hash,status,priority,max_attempts,
                   attempts,created_at,updated_at) VALUES(?,?,?,'pending',?,?,0,?,?)""",
                (task_id, payload_json, digest, priority, max_attempts, stamp, stamp),
            )
            self._event(task_id, "enqueued", "producer", {"payload_hash": digest}, stamp)
            self.db.execute("COMMIT")
            return self._row(task_id)
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def claim(self, worker_id, lease_seconds=60, now=None):
        if not isinstance(worker_id, str) or not worker_id.strip():
            raise QueueError("worker_id is required")
        if isinstance(lease_seconds, bool) or not isinstance(lease_seconds, (int, float)) or not 1 <= lease_seconds <= 3600:
            raise QueueError("lease_seconds must be between 1 and 3600")
        stamp = self._now() if now is None else float(now)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            expired = self.db.execute(
                "SELECT task_id,attempts,max_attempts FROM queue_tasks WHERE status='running' AND lease_expires<=?",
                (stamp,),
            ).fetchall()
            for row in expired:
                status = "pending" if row["attempts"] < row["max_attempts"] else "failed"
                self.db.execute(
                    """UPDATE queue_tasks SET status=?,worker_id=NULL,lease_token=NULL,lease_expires=NULL,
                       last_error='lease_expired',updated_at=? WHERE task_id=?""",
                    (status, stamp, row["task_id"]),
                )
                self._event(row["task_id"], "lease_expired", "queue", {"next_status": status}, stamp)
            row = self.db.execute(
                """SELECT task_id FROM queue_tasks WHERE status='pending' AND attempts<max_attempts
                   ORDER BY priority DESC,created_at,task_id LIMIT 1"""
            ).fetchone()
            if row is None:
                self.db.execute("COMMIT")
                return None
            token = uuid.uuid4().hex
            self.db.execute(
                """UPDATE queue_tasks SET status='running',worker_id=?,lease_token=?,lease_expires=?,
                   attempts=attempts+1,updated_at=? WHERE task_id=? AND status='pending'""",
                (worker_id, token, stamp + lease_seconds, stamp, row["task_id"]),
            )
            self._event(row["task_id"], "claimed", worker_id, {"lease_seconds": lease_seconds}, stamp)
            self.db.execute("COMMIT")
            return self._row(row["task_id"])
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def _owned(self, task_id, worker_id, lease_token, now):
        row = self.db.execute("SELECT * FROM queue_tasks WHERE task_id=?", (task_id,)).fetchone()
        if row is None or row["status"] != "running":
            raise QueueError("Task is not running")
        if row["worker_id"] != worker_id or not lease_token or row["lease_token"] != lease_token:
            raise QueueError("Worker lease ownership check failed")
        if row["lease_expires"] <= now:
            raise QueueError("Worker lease has expired")
        return row

    def heartbeat(self, task_id, worker_id, lease_token, lease_seconds=60, now=None):
        stamp = self._now() if now is None else float(now)
        if isinstance(lease_seconds, bool) or not isinstance(lease_seconds, (int, float)) or not 1 <= lease_seconds <= 3600:
            raise QueueError("lease_seconds must be between 1 and 3600")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self._owned(task_id, worker_id, lease_token, stamp)
            self.db.execute("UPDATE queue_tasks SET lease_expires=?,updated_at=? WHERE task_id=?",
                            (stamp + lease_seconds, stamp, task_id))
            self._event(task_id, "heartbeat", worker_id, {"lease_seconds": lease_seconds}, stamp)
            self.db.execute("COMMIT")
            return self._row(task_id)
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def complete(self, task_id, worker_id, result, lease_token, now=None):
        result_json = self._json_object(result, "result")
        stamp = self._now() if now is None else float(now)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self._owned(task_id, worker_id, lease_token, stamp)
            self.db.execute(
                """UPDATE queue_tasks SET status='succeeded',result_json=?,worker_id=NULL,
                   lease_token=NULL,lease_expires=NULL,updated_at=? WHERE task_id=?""",
                (result_json, stamp, task_id),
            )
            self._event(task_id, "succeeded", worker_id, {}, stamp)
            self.db.execute("COMMIT")
            return self._row(task_id)
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def fail(self, task_id, worker_id, error, lease_token, now=None):
        if not isinstance(error, str) or not error.strip():
            raise QueueError("A non-empty failure reason is required")
        stamp = self._now() if now is None else float(now)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self._owned(task_id, worker_id, lease_token, stamp)
            status = "pending" if row["attempts"] < row["max_attempts"] else "failed"
            self.db.execute(
                """UPDATE queue_tasks SET status=?,last_error=?,worker_id=NULL,lease_token=NULL,
                   lease_expires=NULL,updated_at=? WHERE task_id=?""",
                (status, error[:500], stamp, task_id),
            )
            self._event(task_id, "failed_attempt", worker_id, {"next_status": status}, stamp)
            self.db.execute("COMMIT")
            return self._row(task_id)
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def cancel(self, task_id, actor, now=None):
        if not isinstance(actor, str) or not actor.strip():
            raise QueueError("Cancellation actor is required")
        stamp = self._now() if now is None else float(now)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("SELECT status FROM queue_tasks WHERE task_id=?", (task_id,)).fetchone()
            if row is None:
                raise QueueError("Unknown task: " + task_id)
            if row["status"] not in {"pending", "running"}:
                raise QueueError("Only pending or running tasks can be cancelled")
            self.db.execute(
                """UPDATE queue_tasks SET status='cancelled',worker_id=NULL,lease_token=NULL,
                   lease_expires=NULL,updated_at=? WHERE task_id=?""", (stamp, task_id)
            )
            self._event(task_id, "cancelled", actor, {}, stamp)
            self.db.execute("COMMIT")
            return self._row(task_id)
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def get(self, task_id):
        return self._row(task_id)

    def list_tasks(self, status=None, limit=100):
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 500:
            raise QueueError("limit must be between 1 and 500")
        if status is not None and status not in {"pending", "running", "succeeded", "failed", "cancelled"}:
            raise QueueError("Invalid queue status")
        sql = "SELECT task_id FROM queue_tasks"
        params = ()
        if status:
            sql += " WHERE status=?"
            params = (status,)
        sql += " ORDER BY priority DESC,created_at,task_id LIMIT ?"
        rows = self.db.execute(sql, (*params, limit)).fetchall()
        return [self._row(row["task_id"]) for row in rows]

    def audit_log(self, task_id):
        rows = self.db.execute(
            "SELECT sequence,event,actor,details_json,occurred_at FROM queue_events WHERE task_id=? ORDER BY sequence",
            (task_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def close(self):
        self.db.close()
