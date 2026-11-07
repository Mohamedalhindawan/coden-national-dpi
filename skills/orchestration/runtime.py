"""Minimal local CODEN orchestration control plane.

This runtime manages validated workflow state and audit events only. It does not
execute agents, call external tools, grant credentials, or perform side effects.
"""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from skills.orchestration.validator import validate_task

TERMINAL = {"COMPLETED", "FAILED", "BLOCKED", "CANCELLED"}
TRANSITIONS = {
    ("INTAKE", "submit"): "POLICY_CHECK",
    ("POLICY_CHECK", "allow"): "PLANNING",
    ("POLICY_CHECK", "deny"): "BLOCKED",
    ("PLANNING", "plan_accepted"): "READY",
    ("READY", "start"): "EXECUTING",
    ("EXECUTING", "tasks_done"): "VALIDATING",
    ("EXECUTING", "fatal_error"): "FAILED",
    ("EXECUTING", "policy_violation"): "BLOCKED",
    ("VALIDATING", "checks_pass"): "REVIEW_REQUIRED",
    ("VALIDATING", "checks_fail"): "PLANNING",
    ("REVIEW_REQUIRED", "human_approve"): "COMPLETED",
    ("REVIEW_REQUIRED", "human_reject"): "CANCELLED",
    ("REVIEW_REQUIRED", "human_request_changes"): "PLANNING",
}

class WorkflowError(ValueError):
    pass

class OrchestrationRuntime:
    def __init__(self, database=":memory:"):
        self.db = sqlite3.connect(str(database))
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            owner TEXT NOT NULL,
            state TEXT NOT NULL,
            task_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            approved_artifact_hash TEXT
        );
        CREATE TABLE IF NOT EXISTS audit_events (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL REFERENCES runs(run_id),
            event TEXT NOT NULL,
            from_state TEXT,
            to_state TEXT NOT NULL,
            actor TEXT NOT NULL,
            details_json TEXT NOT NULL,
            occurred_at TEXT NOT NULL
        );
        CREATE TRIGGER IF NOT EXISTS audit_events_no_update
        BEFORE UPDATE ON audit_events BEGIN
            SELECT RAISE(ABORT, 'audit events are append-only');
        END;
        CREATE TRIGGER IF NOT EXISTS audit_events_no_delete
        BEFORE DELETE ON audit_events BEGIN
            SELECT RAISE(ABORT, 'audit events are append-only');
        END;
        """)
        self.db.commit()

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def _event(self, run_id, event, before, after, actor, details=None):
        self.db.execute(
            "INSERT INTO audit_events(run_id,event,from_state,to_state,actor,details_json,occurred_at) VALUES(?,?,?,?,?,?,?)",
            (run_id, event, before, after, actor, json.dumps(details or {}, sort_keys=True), self._now()),
        )

    def create_run(self, task):
        checked = validate_task(task)
        if not checked["valid"]:
            raise WorkflowError("Invalid task: " + "; ".join(checked["errors"]))
        run_id = task["run_id"]
        now = self._now()
        try:
            self.db.execute(
                "INSERT INTO runs(run_id,owner,state,task_json,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                (run_id, task["owner"], "INTAKE", json.dumps(task, sort_keys=True), now, now),
            )
            self._event(run_id, "created", None, "INTAKE", task["owner"])
            self.db.commit()
        except sqlite3.IntegrityError as exc:
            self.db.rollback()
            raise WorkflowError(f"Run already exists: {run_id}") from exc
        return self.get_run(run_id)

    def transition(self, run_id, event, actor, details=None, artifact_hash=None):
        if not actor or not actor.strip():
            raise WorkflowError("Actor is required")
        row = self.db.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None:
            raise WorkflowError(f"Unknown run: {run_id}")
        before = row["state"]
        if before in TERMINAL:
            raise WorkflowError(f"Run is terminal: {before}")
        after = TRANSITIONS.get((before, event))
        if after is None:
            raise WorkflowError(f"Transition not allowed: {before} + {event}")
        if event in {"human_approve", "human_reject", "human_request_changes"}:
            if (details or {}).get("actor_type") != "independent_human" or actor == row["owner"]:
                raise WorkflowError("Review decision requires an independent human reviewer distinct from the task owner")
        if event == "human_approve":
            if not artifact_hash or len(artifact_hash) != 64:
                raise WorkflowError("Approval must bind to a 64-character artifact SHA-256")
            if not all(c in "0123456789abcdefABCDEF" for c in artifact_hash):
                raise WorkflowError("Artifact hash must be hexadecimal SHA-256")
        now = self._now()
        self.db.execute(
            "UPDATE runs SET state=?,updated_at=?,approved_artifact_hash=? WHERE run_id=?",
            (after, now, artifact_hash if event == "human_approve" else row["approved_artifact_hash"], run_id),
        )
        self._event(run_id, event, before, after, actor, details)
        self.db.commit()
        return self.get_run(run_id)

    def get_run(self, run_id):
        row = self.db.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None:
            raise WorkflowError(f"Unknown run: {run_id}")
        return dict(row)

    def audit_log(self, run_id):
        rows = self.db.execute(
            "SELECT sequence,event,from_state,to_state,actor,details_json,occurred_at FROM audit_events WHERE run_id=? ORDER BY sequence",
            (run_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def close(self):
        self.db.close()
