"""SQLite-backed budget reservations and spend controls; no billing/provider integration."""
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import sqlite3
import uuid


class BudgetError(ValueError):
    pass


@dataclass(frozen=True)
class BudgetLimit:
    scope_id: str
    period: str
    limit_usd: float


@dataclass(frozen=True)
class SpendRequest:
    request_id: str
    project_id: str
    team_id: str
    estimated_usd: float
    created_at: str
    run_id: str | None = None


class BudgetLedger:
    def __init__(self, database_path):
        self.database_path = str(database_path)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _initialize(self):
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS budgets (
                    scope_id TEXT NOT NULL,
                    period TEXT NOT NULL CHECK(period IN ('daily','monthly')),
                    limit_usd REAL NOT NULL CHECK(limit_usd >= 0),
                    PRIMARY KEY(scope_id, period)
                );
                CREATE TABLE IF NOT EXISTS reservations (
                    reservation_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL UNIQUE,
                    project_id TEXT NOT NULL,
                    team_id TEXT NOT NULL,
                    reserved_usd REAL NOT NULL CHECK(reserved_usd >= 0),
                    actual_usd REAL,
                    period_day TEXT NOT NULL,
                    period_month TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('reserved','reconciled')),
                    created_at TEXT NOT NULL,
                    run_id TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_res_project_day ON reservations(project_id, period_day);
                CREATE INDEX IF NOT EXISTS idx_res_team_day ON reservations(team_id, period_day);
                CREATE INDEX IF NOT EXISTS idx_res_project_month ON reservations(project_id, period_month);
                CREATE INDEX IF NOT EXISTS idx_res_team_month ON reservations(team_id, period_month);
            """)
            columns = {row["name"] for row in db.execute("PRAGMA table_info(reservations)")}
            if "run_id" not in columns:
                db.execute("ALTER TABLE reservations ADD COLUMN run_id TEXT")
            db.execute("CREATE INDEX IF NOT EXISTS idx_res_run_id ON reservations(run_id)")

    @staticmethod
    def _money(value, field):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise BudgetError(field + " must be a finite non-negative amount")
        return round(float(value), 8)

    def set_budget(self, budget):
        if not isinstance(budget, BudgetLimit) or not isinstance(budget.scope_id, str) or not budget.scope_id.strip():
            raise BudgetError("valid scope_id and BudgetLimit are required")
        if budget.period not in {"daily", "monthly"}:
            raise BudgetError("period must be daily or monthly")
        amount = self._money(budget.limit_usd, "limit_usd")
        with self._connect() as db:
            db.execute(
                "INSERT INTO budgets(scope_id,period,limit_usd) VALUES(?,?,?) "
                "ON CONFLICT(scope_id,period) DO UPDATE SET limit_usd=excluded.limit_usd",
                (budget.scope_id, budget.period, amount),
            )

    @staticmethod
    def _parse_time(value):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            raise BudgetError("created_at must be an ISO-8601 timestamp")
        if parsed.tzinfo is None:
            raise BudgetError("created_at must include a timezone")
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _period_key(period, instant):
        return instant.strftime("%Y-%m-%d" if period == "daily" else "%Y-%m")

    @staticmethod
    def _totals(db, scope_id, period, key):
        column = "period_day" if period == "daily" else "period_month"
        rows = db.execute(
            f"SELECT reserved_usd,actual_usd,status FROM reservations "
            f"WHERE {column}=? AND (project_id=? OR team_id=?)",
            (key, scope_id, scope_id),
        ).fetchall()
        reserved = sum(row["reserved_usd"] for row in rows if row["status"] == "reserved")
        actual = sum(row["actual_usd"] or 0.0 for row in rows if row["status"] == "reconciled")
        return round(reserved, 8), round(actual, 8)

    def reserve(self, request):
        if not isinstance(request, SpendRequest):
            raise BudgetError("request must be a SpendRequest")
        for field in ("request_id", "project_id", "team_id"):
            value = getattr(request, field)
            if not isinstance(value, str) or not value.strip():
                raise BudgetError(field + " is required")
        if request.run_id is not None and (not isinstance(request.run_id, str) or not request.run_id.strip()):
            raise BudgetError("run_id must be a non-empty string when supplied")
        amount = self._money(request.estimated_usd, "estimated_usd")
        instant = self._parse_time(request.created_at)
        day, month = instant.strftime("%Y-%m-%d"), instant.strftime("%Y-%m")
        scopes = (request.project_id, request.team_id)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT * FROM reservations WHERE request_id=?", (request.request_id,)).fetchone()
            if existing:
                if (existing["project_id"] != request.project_id or existing["team_id"] != request.team_id
                    or existing["reserved_usd"] != amount or existing["period_day"] != day or existing["run_id"] != request.run_id):
                    raise BudgetError("request_id was already used with different reservation details")
                return self._receipt(existing)
            for scope in scopes:
                for period, key in (("daily", day), ("monthly", month)):
                    budget = db.execute(
                        "SELECT limit_usd FROM budgets WHERE scope_id=? AND period=?",
                        (scope, period),
                    ).fetchone()
                    if budget is None:
                        continue
                    reserved, actual = self._totals(db, scope, period, key)
                    if round(reserved + actual + amount, 8) > budget["limit_usd"]:
                        raise BudgetError(f"{period} budget exceeded for scope {scope}")
            reservation_id = uuid.uuid4().hex
            db.execute(
                "INSERT INTO reservations (reservation_id,request_id,project_id,team_id,reserved_usd,actual_usd,period_day,period_month,status,created_at,run_id) VALUES(?,?,?,?,?,?,?,?,'reserved',?,?)",
                (reservation_id, request.request_id, request.project_id, request.team_id,
                 amount, None, day, month, instant.isoformat(), request.run_id),
            )
            row = db.execute("SELECT * FROM reservations WHERE reservation_id=?", (reservation_id,)).fetchone()
            return self._receipt(row)

    @staticmethod
    def _receipt(row):
        return {
            "reservation_id": row["reservation_id"],
            "request_id": row["request_id"],
            "project_id": row["project_id"],
            "team_id": row["team_id"],
            "reserved_usd": row["reserved_usd"],
            "status": row["status"],
            "run_id": row["run_id"],
        }

    def reconcile(self, reservation_id, actual_usd):
        actual = self._money(actual_usd, "actual_usd")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM reservations WHERE reservation_id=?", (reservation_id,)).fetchone()
            if row is None:
                raise BudgetError("unknown reservation")
            if row["status"] != "reserved":
                if row["actual_usd"] == actual:
                    return {"reservation_id": reservation_id, "actual_usd": actual, "status": "reconciled"}
                raise BudgetError("reservation already reconciled with different actual spend")
            if actual > row["reserved_usd"]:
                raise BudgetError("actual spend cannot exceed reserved amount")
            db.execute(
                "UPDATE reservations SET actual_usd=?,status='reconciled' WHERE reservation_id=?",
                (actual, reservation_id),
            )
            return {"reservation_id": reservation_id, "actual_usd": actual, "status": "reconciled"}

    def snapshot(self, scope_id, period, key):
        if period not in {"daily", "monthly"} or not isinstance(scope_id, str) or not scope_id.strip():
            raise BudgetError("valid scope and period are required")
        with self._connect() as db:
            budget = db.execute(
                "SELECT limit_usd FROM budgets WHERE scope_id=? AND period=?",
                (scope_id, period),
            ).fetchone()
            reserved, actual = self._totals(db, scope_id, period, key)
        limit = budget["limit_usd"] if budget else None
        consumed = round(reserved + actual, 8)
        return {
            "scope_id": scope_id, "period": period, "period_key": key,
            "limit_usd": limit, "reserved_usd": reserved, "actual_usd": actual,
            "consumed_usd": consumed,
            "remaining_usd": round(limit - consumed, 8) if limit is not None else None,
            "utilization_percent": round(consumed / limit * 100, 2) if limit else (100.0 if limit == 0 and consumed else 0.0) if limit == 0 else None,
        }

    def reconciliation_snapshot(self, project_id, team_id, period, key):
        if (not isinstance(project_id, str) or not project_id.strip()
            or not isinstance(team_id, str) or not team_id.strip()
            or period not in {"daily", "monthly"} or not isinstance(key, str) or not key.strip()):
            raise BudgetError("valid project, team, period and period key are required")
        column = "period_day" if period == "daily" else "period_month"
        with self._connect() as db:
            rows = db.execute(
                f"SELECT run_id,status,actual_usd FROM reservations WHERE project_id=? AND team_id=? AND {column}=?",
                (project_id, team_id, key),
            ).fetchall()
        linked = [row for row in rows if row["run_id"] is not None]
        reconciled = [row for row in linked if row["status"] == "reconciled"]
        return {
            "linked_runs": len({row["run_id"] for row in linked}),
            "reconciled_runs": len({row["run_id"] for row in reconciled}),
            "reconciled_actual_usd": round(sum(row["actual_usd"] or 0.0 for row in reconciled), 8),
            "unlinked_reservations": sum(row["run_id"] is None for row in rows),
            "pending_linked_reservations": sum(row["run_id"] is not None and row["status"] == "reserved" for row in rows),
        }

    def alerts(self, scope_id, period, key, thresholds=(80, 90, 100)):
        snapshot = self.snapshot(scope_id, period, key)
        if snapshot["limit_usd"] is None:
            return []
        pct = snapshot["utilization_percent"]
        return [
            {"scope_id": scope_id, "period": period, "period_key": key,
             "threshold_percent": threshold, "utilization_percent": pct,
             "consumed_usd": snapshot["consumed_usd"], "limit_usd": snapshot["limit_usd"]}
            for threshold in sorted(set(thresholds))
            if type(threshold) is int and 1 <= threshold <= 100 and pct >= threshold
        ]
