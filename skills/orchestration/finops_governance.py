"""Maker-checker workflow and append-only audit trail for FinOps reconciliations.

This is a local governance control layer, not an identity provider or a
transaction coordinator across the governance and ledger SQLite databases.
The host must authenticate principals and protect both database files.
"""
from datetime import datetime, timezone
import hashlib
import json
import sqlite3


class FinOpsGovernanceError(ValueError):
    pass


class FinOpsGovernance:
    SUBMIT_ROLES = {"finance_operator", "finance_admin"}
    APPROVE_ROLES = {"finance_approver", "finance_admin"}

    def __init__(self, ledger, database_path):
        if not hasattr(ledger, "reconcile"):
            raise FinOpsGovernanceError("a FinOps ledger is required")
        self.ledger = ledger
        self.db = sqlite3.connect(str(database_path), timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=30000")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS reconciliation_requests (
                request_id TEXT PRIMARY KEY,
                reservation_id TEXT NOT NULL,
                actual_usd REAL NOT NULL CHECK(actual_usd >= 0),
                submitted_by TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('pending','approved','rejected')),
                decided_by TEXT,
                created_at TEXT NOT NULL,
                decided_at TEXT
            );
            CREATE TABLE IF NOT EXISTS audit_events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                details_json TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                previous_hash TEXT,
                event_hash TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_finops_audit_request
                ON audit_events(request_id, sequence);
            CREATE TRIGGER IF NOT EXISTS finops_audit_no_update
                BEFORE UPDATE ON audit_events BEGIN
                    SELECT RAISE(ABORT, 'audit events are append-only');
                END;
            CREATE TRIGGER IF NOT EXISTS finops_audit_no_delete
                BEFORE DELETE ON audit_events BEGIN
                    SELECT RAISE(ABORT, 'audit events are append-only');
                END;
        """)
        self._migrate_audit_chain()
        self.db.commit()

    @staticmethod
    def _canonical_event(event):
        payload = {
            "sequence": event["sequence"],
            "request_id": event["request_id"],
            "event_type": event["event_type"],
            "actor_id": event["actor_id"],
            "details_json": event["details_json"],
            "occurred_at": event["occurred_at"],
            "previous_hash": event["previous_hash"],
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def _event_hash(cls, event):
        return hashlib.sha256(cls._canonical_event(event).encode("utf-8")).hexdigest()

    def _migrate_audit_chain(self):
        self.db.execute("DROP TRIGGER IF EXISTS finops_audit_no_update")
        self.db.execute("DROP TRIGGER IF EXISTS finops_audit_no_delete")
        columns = {row["name"] for row in self.db.execute("PRAGMA table_info(audit_events)")}
        if "previous_hash" not in columns:
            self.db.execute("ALTER TABLE audit_events ADD COLUMN previous_hash TEXT")
        if "event_hash" not in columns:
            self.db.execute("ALTER TABLE audit_events ADD COLUMN event_hash TEXT")
        rows = self.db.execute("SELECT * FROM audit_events ORDER BY sequence").fetchall()
        if any(row["previous_hash"] is None or row["event_hash"] is None for row in rows):
            previous = "0" * 64
            for row in rows:
                event = dict(row)
                event["previous_hash"] = previous
                digest = self._event_hash(event)
                self.db.execute(
                    "UPDATE audit_events SET previous_hash=?,event_hash=? WHERE sequence=?",
                    (previous, digest, row["sequence"]),
                )
                previous = digest
        self.db.executescript("""
            CREATE TRIGGER IF NOT EXISTS finops_audit_no_update
                BEFORE UPDATE ON audit_events BEGIN
                    SELECT RAISE(ABORT, 'audit events are append-only');
                END;
            CREATE TRIGGER IF NOT EXISTS finops_audit_no_delete
                BEFORE DELETE ON audit_events BEGIN
                    SELECT RAISE(ABORT, 'audit events are append-only');
                END;
        """)

    @staticmethod
    def _actor(actor_id, role, allowed):
        if not isinstance(actor_id, str) or not actor_id.strip():
            raise FinOpsGovernanceError("actor_id is required")
        if role not in allowed:
            raise FinOpsGovernanceError("actor role is not authorized")
        return actor_id.strip()

    def _audit(self, request_id, event_type, actor_id, details):
        sequence = self.db.execute(
            "SELECT COALESCE(MAX(sequence), 0) + 1 FROM audit_events"
        ).fetchone()[0]
        previous = self.db.execute(
            "SELECT event_hash FROM audit_events ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        previous_hash = previous["event_hash"] if previous else "0" * 64
        event = {
            "sequence": sequence,
            "request_id": request_id,
            "event_type": event_type,
            "actor_id": actor_id,
            "details_json": json.dumps(details, sort_keys=True, separators=(",", ":"), ensure_ascii=False),
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "previous_hash": previous_hash,
        }
        digest = self._event_hash(event)
        self.db.execute(
            """INSERT INTO audit_events
               (sequence,request_id,event_type,actor_id,details_json,occurred_at,previous_hash,event_hash)
               VALUES(?,?,?,?,?,?,?,?)""",
            (sequence, request_id, event_type, actor_id, event["details_json"],
             event["occurred_at"], previous_hash, digest),
        )

    def verify_audit_chain(self):
        rows = self.db.execute("SELECT * FROM audit_events ORDER BY sequence").fetchall()
        previous = "0" * 64
        expected_sequence = 1
        for row in rows:
            event = dict(row)
            if event["sequence"] != expected_sequence:
                return {"valid": False, "events_checked": expected_sequence - 1,
                        "reason": "sequence_gap", "sequence": event["sequence"]}
            if event["previous_hash"] != previous:
                return {"valid": False, "events_checked": expected_sequence - 1,
                        "reason": "previous_hash_mismatch", "sequence": event["sequence"]}
            if event["event_hash"] != self._event_hash(event):
                return {"valid": False, "events_checked": expected_sequence - 1,
                        "reason": "event_hash_mismatch", "sequence": event["sequence"]}
            previous = event["event_hash"]
            expected_sequence += 1
        return {"valid": True, "events_checked": len(rows), "head_hash": previous}

    @staticmethod
    def _request(row):
        return {key: row[key] for key in (
            "request_id", "reservation_id", "actual_usd", "submitted_by",
            "status", "decided_by", "created_at", "decided_at"
        )}

    def submit_reconciliation(self, reservation_id, actual_usd, actor_id, role, request_id):
        actor = self._actor(actor_id, role, self.SUBMIT_ROLES)
        if not isinstance(reservation_id, str) or not reservation_id.strip():
            raise FinOpsGovernanceError("reservation_id is required")
        if not isinstance(request_id, str) or not request_id.strip():
            raise FinOpsGovernanceError("request_id is required")
        try:
            amount = float(actual_usd)
        except (TypeError, ValueError):
            raise FinOpsGovernanceError("actual_usd must be a finite non-negative amount")
        if isinstance(actual_usd, bool) or amount < 0 or amount != amount or amount in (float("inf"), float("-inf")):
            raise FinOpsGovernanceError("actual_usd must be a finite non-negative amount")
        amount = round(amount, 8)
        self.db.execute("BEGIN IMMEDIATE")
        existing = self.db.execute(
            "SELECT * FROM reconciliation_requests WHERE request_id=?", (request_id,)
        ).fetchone()
        if existing:
            if (existing["reservation_id"] != reservation_id or existing["actual_usd"] != amount
                or existing["submitted_by"] != actor):
                self.db.rollback()
                raise FinOpsGovernanceError("request_id was already used with different details")
            self.db.commit()
            return self._request(existing)
        created = datetime.now(timezone.utc).isoformat()
        self.db.execute(
            """INSERT INTO reconciliation_requests
               (request_id,reservation_id,actual_usd,submitted_by,status,created_at)
               VALUES(?,?,?,?, 'pending', ?)""",
            (request_id, reservation_id, amount, actor, created),
        )
        self._audit(request_id, "reconciliation_submitted", actor,
                    {"reservation_id": reservation_id, "actual_usd": amount})
        row = self.db.execute(
            "SELECT * FROM reconciliation_requests WHERE request_id=?", (request_id,)
        ).fetchone()
        self.db.commit()
        return self._request(row)

    def approve_reconciliation(self, request_id, actor_id, role):
        actor = self._actor(actor_id, role, self.APPROVE_ROLES)
        self.db.execute("BEGIN IMMEDIATE")
        row = self.db.execute(
            "SELECT * FROM reconciliation_requests WHERE request_id=?", (request_id,)
        ).fetchone()
        if row is None:
            self.db.rollback()
            raise FinOpsGovernanceError("unknown reconciliation request")
        if row["status"] != "pending":
            self.db.rollback()
            raise FinOpsGovernanceError("reconciliation request is already decided")
        if row["submitted_by"] == actor:
            self.db.rollback()
            raise FinOpsGovernanceError("maker and checker must be different people")
        try:
            result = self.ledger.reconcile(row["reservation_id"], row["actual_usd"])
        except Exception as exc:
            self.db.rollback()
            raise FinOpsGovernanceError("ledger reconciliation was rejected") from exc
        decided = datetime.now(timezone.utc).isoformat()
        cursor = self.db.execute(
            "UPDATE reconciliation_requests SET status='approved',decided_by=?,decided_at=? "
            "WHERE request_id=? AND status='pending'",
            (actor, decided, request_id),
        )
        if cursor.rowcount != 1:
            self.db.rollback()
            raise FinOpsGovernanceError("reconciliation request changed during approval")
        self._audit(request_id, "reconciliation_approved", actor, result)
        final = self.db.execute(
            "SELECT * FROM reconciliation_requests WHERE request_id=?", (request_id,)
        ).fetchone()
        self.db.commit()
        return self._request(final)

    def reject_reconciliation(self, request_id, actor_id, role):
        actor = self._actor(actor_id, role, self.APPROVE_ROLES)
        self.db.execute("BEGIN IMMEDIATE")
        row = self.db.execute(
            "SELECT * FROM reconciliation_requests WHERE request_id=?", (request_id,)
        ).fetchone()
        if row is None:
            self.db.rollback()
            raise FinOpsGovernanceError("unknown reconciliation request")
        if row["status"] != "pending":
            self.db.rollback()
            raise FinOpsGovernanceError("reconciliation request is already decided")
        if row["submitted_by"] == actor:
            self.db.rollback()
            raise FinOpsGovernanceError("maker and checker must be different people")
        try:
            ledger_state = self.ledger.reservation_status(row["reservation_id"])
        except Exception as exc:
            self.db.rollback()
            raise FinOpsGovernanceError("reservation state cannot be verified; rejection is blocked") from exc
        if ledger_state["status"] != "reserved":
            self.db.rollback()
            raise FinOpsGovernanceError("reconciled ledger operation cannot be rejected")
        decided = datetime.now(timezone.utc).isoformat()
        cursor = self.db.execute(
            "UPDATE reconciliation_requests SET status='rejected',decided_by=?,decided_at=? "
            "WHERE request_id=? AND status='pending'",
            (actor, decided, request_id),
        )
        if cursor.rowcount != 1:
            self.db.rollback()
            raise FinOpsGovernanceError("reconciliation request changed during rejection")
        self._audit(request_id, "reconciliation_rejected", actor, {})
        final = self.db.execute(
            "SELECT * FROM reconciliation_requests WHERE request_id=?", (request_id,)
        ).fetchone()
        self.db.commit()
        return self._request(final)

    def list_requests(self, status=None):
        if status is not None and status not in {"pending", "approved", "rejected"}:
            raise FinOpsGovernanceError("invalid reconciliation status")
        if status:
            rows = self.db.execute("SELECT * FROM reconciliation_requests WHERE status=? ORDER BY created_at DESC, request_id", (status,)).fetchall()
        else:
            rows = self.db.execute("SELECT * FROM reconciliation_requests ORDER BY created_at DESC, request_id").fetchall()
        return [self._request(row) for row in rows]

    def audit_events(self, request_id):
        rows = self.db.execute(
            "SELECT * FROM audit_events WHERE request_id=? ORDER BY sequence", (request_id,)
        ).fetchall()
        return [{**dict(row), "details": json.loads(row["details_json"])} for row in rows]

    def close(self):
        self.db.close()
