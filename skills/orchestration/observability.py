"""Privacy-minimizing, append-only agent run metrics and scorecards."""
import json
import sqlite3
from datetime import datetime, timezone


class ObservabilityError(ValueError):
    pass


class ObservabilityStore:
    STATUSES = {"succeeded", "failed", "blocked", "cancelled"}

    def __init__(self, database=":memory:"):
        self.db = sqlite3.connect(str(database))
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS agent_metrics (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            status TEXT NOT NULL,
            duration_ms INTEGER NOT NULL,
            input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            cost_usd REAL NOT NULL,
            quality_score REAL NOT NULL,
            policy_violations INTEGER NOT NULL,
            retry_count INTEGER NOT NULL,
            evidence_ref TEXT NOT NULL,
            recorded_at TEXT NOT NULL
        );
        CREATE TRIGGER IF NOT EXISTS agent_metrics_no_update
        BEFORE UPDATE ON agent_metrics BEGIN
            SELECT RAISE(ABORT, 'metrics are append-only');
        END;
        CREATE TRIGGER IF NOT EXISTS agent_metrics_no_delete
        BEFORE DELETE ON agent_metrics BEGIN
            SELECT RAISE(ABORT, 'metrics are append-only');
        END;
        """)
        self.db.commit()

    @staticmethod
    def _nonnegative_int(record, key):
        value = record.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ObservabilityError(f"{key} must be a non-negative integer")
        return value

    def record(self, record):
        if not isinstance(record, dict):
            raise ObservabilityError("Metric record must be an object")
        required = ("run_id", "task_id", "agent_id", "provider", "status", "evidence_ref")
        if any(not isinstance(record.get(k), str) or not record[k].strip() for k in required):
            raise ObservabilityError("Required identity, provider, status and evidence fields are mandatory")
        if record["status"] not in self.STATUSES:
            raise ObservabilityError("Unsupported status")
        if record["status"] == "succeeded" and not record["evidence_ref"].strip():
            raise ObservabilityError("Successful runs require evidence_ref")
        duration = self._nonnegative_int(record, "duration_ms")
        input_tokens = self._nonnegative_int(record, "input_tokens")
        output_tokens = self._nonnegative_int(record, "output_tokens")
        violations = self._nonnegative_int(record, "policy_violations")
        retries = self._nonnegative_int(record, "retry_count")
        cost = record.get("cost_usd")
        quality = record.get("quality_score")
        if isinstance(cost, bool) or not isinstance(cost, (int, float)) or cost < 0:
            raise ObservabilityError("cost_usd must be non-negative")
        if isinstance(quality, bool) or not isinstance(quality, (int, float)) or not 0 <= quality <= 1:
            raise ObservabilityError("quality_score must be between 0 and 1")
        safe = {
            "run_id": record["run_id"], "task_id": record["task_id"],
            "agent_id": record["agent_id"], "provider": record["provider"],
            "status": record["status"], "duration_ms": duration,
            "input_tokens": input_tokens, "output_tokens": output_tokens,
            "cost_usd": float(cost), "quality_score": float(quality),
            "policy_violations": violations, "retry_count": retries,
            "evidence_ref": record["evidence_ref"],
        }
        self.db.execute(
            """INSERT INTO agent_metrics
            (run_id,task_id,agent_id,provider,status,duration_ms,input_tokens,output_tokens,
             cost_usd,quality_score,policy_violations,retry_count,evidence_ref,recorded_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            tuple(safe[k] for k in ("run_id","task_id","agent_id","provider","status","duration_ms",
                 "input_tokens","output_tokens","cost_usd","quality_score","policy_violations",
                 "retry_count","evidence_ref")) + (datetime.now(timezone.utc).isoformat(),)
        )
        self.db.commit()
        return safe

    def agent_summary(self, agent_id):
        rows = self.db.execute("SELECT * FROM agent_metrics WHERE agent_id=?", (agent_id,)).fetchall()
        count = len(rows)
        if not count:
            return {"agent_id": agent_id, "runs": 0, "success_rate": 0.0,
                    "total_cost_usd": 0.0, "average_quality": 0.0,
                    "average_duration_ms": 0.0, "total_tokens": 0,
                    "policy_violations": 0, "retry_count": 0}
        succeeded = sum(r["status"] == "succeeded" for r in rows)
        return {
            "agent_id": agent_id, "runs": count, "success_rate": succeeded / count,
            "total_cost_usd": sum(r["cost_usd"] for r in rows),
            "average_quality": sum(r["quality_score"] for r in rows) / count,
            "average_duration_ms": sum(r["duration_ms"] for r in rows) / count,
            "total_tokens": sum(r["input_tokens"] + r["output_tokens"] for r in rows),
            "policy_violations": sum(r["policy_violations"] for r in rows),
            "retry_count": sum(r["retry_count"] for r in rows),
        }

    def close(self):
        self.db.close()
