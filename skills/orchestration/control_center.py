"""Read-only unified observability and budget snapshot for the CODEN control center."""
from datetime import date
import math


class ControlCenterError(ValueError):
    pass


class ControlCenter:
    STATUSES = ("succeeded", "failed", "blocked", "cancelled")

    def __init__(self, observability_store, budget_ledger):
        if not hasattr(observability_store, "db") or not hasattr(budget_ledger, "snapshot"):
            raise ControlCenterError("observability store and budget ledger are required")
        self.metrics = observability_store
        self.budgets = budget_ledger

    @staticmethod
    def _validate(project_id, team_id, period, period_key):
        if not isinstance(project_id, str) or not project_id.strip():
            raise ControlCenterError("project_id is required")
        if not isinstance(team_id, str) or not team_id.strip():
            raise ControlCenterError("team_id is required")
        if period not in {"daily", "monthly"}:
            raise ControlCenterError("period must be daily or monthly")
        try:
            if period == "daily":
                date.fromisoformat(period_key)
                if len(period_key) != 10:
                    raise ValueError()
            else:
                if not isinstance(period_key, str) or len(period_key) != 7:
                    raise ValueError()
                date.fromisoformat(period_key + "-01")
        except (ValueError, TypeError):
            raise ControlCenterError("period_key must be YYYY-MM-DD or YYYY-MM")

    def snapshot(self, project_id, team_id, period, period_key):
        self._validate(project_id, team_id, period, period_key)
        rows = self.metrics.db.execute(
            """SELECT run_id,agent_id,provider,status,duration_ms,input_tokens,output_tokens,
                      cost_usd,quality_score,policy_violations,retry_count
               FROM agent_metrics
               WHERE project_id=? AND team_id=? AND substr(recorded_at,1,?)=?
               ORDER BY sequence""",
            (project_id, team_id, 10 if period == "daily" else 7, period_key),
        ).fetchall()
        unattributed = self.metrics.db.execute(
            "SELECT COUNT(*) AS count FROM agent_metrics WHERE project_id IS NULL OR team_id IS NULL"
        ).fetchone()["count"]
        total = len(rows)
        counts = {status: sum(row["status"] == status for row in rows) for status in self.STATUSES}
        tokens_in = sum(row["input_tokens"] for row in rows)
        tokens_out = sum(row["output_tokens"] for row in rows)
        observed_cost = round(sum(row["cost_usd"] for row in rows), 8)
        agents = {}
        providers = {}
        for row in rows:
            agent = agents.setdefault(row["agent_id"], {
                "agent_id": row["agent_id"], "runs": 0, "succeeded": 0,
                "failed": 0, "blocked": 0, "cancelled": 0, "cost_usd": 0.0,
                "total_tokens": 0, "policy_violations": 0, "retry_count": 0,
                "quality_total": 0.0,
            })
            agent["runs"] += 1
            agent[row["status"]] += 1
            agent["cost_usd"] += row["cost_usd"]
            agent["total_tokens"] += row["input_tokens"] + row["output_tokens"]
            agent["policy_violations"] += row["policy_violations"]
            agent["retry_count"] += row["retry_count"]
            agent["quality_total"] += row["quality_score"]
            provider = providers.setdefault(row["provider"], {
                "provider": row["provider"], "runs": 0, "cost_usd": 0.0,
                "total_tokens": 0, "policy_violations": 0,
            })
            provider["runs"] += 1
            provider["cost_usd"] += row["cost_usd"]
            provider["total_tokens"] += row["input_tokens"] + row["output_tokens"]
            provider["policy_violations"] += row["policy_violations"]
        agent_rows = []
        for item in agents.values():
            item["cost_usd"] = round(item["cost_usd"], 8)
            item["average_quality"] = round(item.pop("quality_total") / item["runs"], 4)
            item["success_rate"] = round(item["succeeded"] / item["runs"], 4)
            agent_rows.append(item)
        provider_rows = []
        for item in providers.values():
            item["cost_usd"] = round(item["cost_usd"], 8)
            provider_rows.append(item)
        project_budget = self.budgets.snapshot(project_id, period, period_key)
        team_budget = self.budgets.snapshot(team_id, period, period_key)
        ledger_reconciliation = self.budgets.reconciliation_snapshot(
            project_id, team_id, period, period_key)
        linked_run_ids = set(ledger_reconciliation["run_ids"])
        observed_linked_cost = round(sum(
            row["cost_usd"] for row in rows if row["run_id"] in linked_run_ids
        ), 8)
        reconciled_cost = ledger_reconciliation["reconciled_actual_usd"]
        variance = round(reconciled_cost - observed_linked_cost, 8)
        if ledger_reconciliation["unlinked_reservations"] or ledger_reconciliation["pending_linked_reservations"]:
            reconciliation_status = "incomplete_review"
        elif abs(variance) > 0.00000001:
            reconciliation_status = "variance_review"
        else:
            reconciliation_status = "reconciled"
        cost_reconciliation = {
            "linked_runs": ledger_reconciliation["linked_runs"],
            "reconciled_runs": ledger_reconciliation["reconciled_runs"],
            "observed_metric_cost_usd": observed_linked_cost,
            "reconciled_ledger_cost_usd": reconciled_cost,
            "variance_usd": variance,
            "unlinked_reservations": ledger_reconciliation["unlinked_reservations"],
            "pending_linked_reservations": ledger_reconciliation["pending_linked_reservations"],
            "status": reconciliation_status,
            "data_note": "Comparison uses only run IDs linked in the FinOps ledger. Metric costs are recorded estimates/observations; ledger actuals are manual reconciliations, not verified provider invoices. The two values are not added together.",
        }
        return {
            "control_center_version": "2.0.0",
            "scope": {"project_id": project_id, "team_id": team_id,
                      "period": period, "period_key": period_key},
            "runs": {"total": total, **counts,
                     "success_rate": round(counts["succeeded"] / total, 4) if total else 0.0},
            "usage": {"input_tokens": tokens_in, "output_tokens": tokens_out,
                      "total_tokens": tokens_in + tokens_out,
                      "observed_cost_usd": observed_cost,
                      "average_quality": round(sum(r["quality_score"] for r in rows) / total, 4) if total else 0.0,
                      "average_duration_ms": round(sum(r["duration_ms"] for r in rows) / total, 2) if total else 0.0,
                      "policy_violations": sum(r["policy_violations"] for r in rows),
                      "retry_count": sum(r["retry_count"] for r in rows)},
            "agents": sorted(agent_rows, key=lambda item: item["agent_id"]),
            "providers": sorted(provider_rows, key=lambda item: item["provider"]),
            "unattributed_metrics": unattributed,
            "budget": {"project": project_budget, "team": team_budget},
            "cost_reconciliation": cost_reconciliation,
            "budget_alerts": {
                "project": self.budgets.alerts(project_id, period, period_key),
                "team": self.budgets.alerts(team_id, period, period_key),
            },
            "data_note": "Run metrics are filtered by exact project, team and UTC period; legacy unattributed records are excluded and counted separately. Budget values are ledger reservations and reconciled amounts. No live provider telemetry is implied.",
        }
