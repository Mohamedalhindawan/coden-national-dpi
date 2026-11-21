"""Durable single-host control plane for one project in a private directory."""

import argparse
import json

import time
from pathlib import Path

from skills.orchestration.control_plane import WorkflowControlPlane
from skills.orchestration.model_gateway import (
    GatewayPolicy,
    ModelGateway,
    ModelProfile,
    ModelRequest,
)
from skills.orchestration.queue import PersistentTaskQueue
from skills.orchestration.scheduler import DAGAwareScheduler
from skills.orchestration.worker_queue import WorkerQueueIntegration
from skills.orchestration.worker_runtime import WorkerAdmissionController

from .project import encoded, read_text, valid

CAPABILITIES = dict(
    orchestrator="reasoning",
    architecture="architecture",
    coding="coding",
    security="security_review",
    testing="testing",
    documentation="documentation",
    devops="reasoning",
    review="reasoning",
)


class Operations:
    def __init__(self, root, task=None):
        self.root = Path(root)
        if task is not None:
            if not valid(task):
                raise ValueError("invalid synthetic project")
            self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        db = self.root / "factory.sqlite"
        if task is None and not db.is_file():
            raise ValueError("submit project first")
        self.queue = PersistentTaskQueue(db)
        try:
            self._open(task)
        except Exception:
            self.close()
            raise

    def _open(self, task):
        db = self.queue.db
        db.executescript("""
          CREATE TABLE IF NOT EXISTS project(id INTEGER PRIMARY KEY CHECK(id=1), spec TEXT NOT NULL, paused INTEGER DEFAULT 0);
          CREATE TABLE IF NOT EXISTS calls(role TEXT PRIMARY KEY, started REAL NOT NULL, receipt TEXT NOT NULL);
        """)
        if task is not None:
            db.execute(
                "INSERT OR IGNORE INTO project(id,spec) VALUES(1,?)", (encoded(task),)
            )
        row = db.execute("SELECT spec FROM project WHERE id=1").fetchone()
        if not row or (task is not None and row[0] != encoded(task)):
            raise ValueError("directory belongs to another specification")
        self.task = json.loads(row[0])
        workers = WorkerAdmissionController(1, ["local"], ["specialist"])
        workers.register_worker("local", ["specialist"], max_concurrency=1)
        stages = []
        for role in CAPABILITIES:
            stages.append(
                dict(
                    task_id=role,
                    depends_on=[stages[-1]["task_id"]] if stages else [],
                    payload={"kind": "specialist"},
                )
            )
        integration = WorkerQueueIntegration(self.queue, workers)
        self.scheduler = DAGAwareScheduler(self.queue, integration, stages)
        self.control = WorkflowControlPlane(self.scheduler, workers)

    def close(self):
        self.queue.close()

    def pause(self, paused):
        self.queue.db.execute("UPDATE project SET paused=? WHERE id=1", (int(paused),))

    def paused(self):
        return bool(
            self.queue.db.execute("SELECT paused FROM project WHERE id=1").fetchone()[0]
        )

    def claim(self):
        if self.paused():
            return None
        return self.control.dispatch("local", lease_seconds=240)

    def reserve(self, claim, prompt_bytes):
        role = claim["task_id"]
        # Upper bound for byte-level tokenization plus delimiters. No paid route registered.
        gateway = ModelGateway()
        gateway.register_model(
            ModelProfile(
                "qwen-coder", "local-cpu", tuple(CAPABILITIES.values()), 2048, 0, 0
            )
        )
        receipt = gateway.route(
            ModelRequest(
                role,
                self.task["id"],
                CAPABILITIES[role],
                prompt_bytes + 16,
                192,
                0,
                "synthetic",
            ),
            GatewayPolicy(),
        )
        cur = self.queue.db.execute(
            """INSERT OR IGNORE INTO calls(role,started,receipt)
            SELECT task_id,?,? FROM queue_tasks WHERE task_id=? AND status='running'
            AND lease_token=? AND lease_expires>? AND (SELECT paused FROM project WHERE id=1)=0""",
            (time.time(), encoded(receipt), role, claim["lease_token"], time.time()),
        )
        if cur.rowcount != 1:
            raise ValueError("model call unavailable or already reserved")
        return receipt

    def complete(self, claim, result):
        self.scheduler.complete(claim, result)

    def fail(self, claim, error):
        self.scheduler.fail(claim, error)

    def result(self, role):
        return self.queue.get(role)["result"]

    def status(self):
        snapshot = self.control.snapshot()
        snapshot.pop(
            "workers"
        )  # worker slots are process-local; report durable leases instead
        snapshot.update(
            paused=self.paused(),
            states=self.scheduler.states(),
            api_cost_usd=0,
            reserved_calls=self.queue.db.execute(
                "SELECT count(*) FROM calls"
            ).fetchone()[0],
        )
        return snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["submit", "status", "pause", "resume", "audit"]
    )
    parser.add_argument("directory", type=Path)
    parser.add_argument("--task", type=Path)
    args = parser.parse_args()
    if args.command == "submit" and not args.task:
        parser.error("submit requires --task")
    task = json.loads(read_text(args.task, 32768)) if args.command == "submit" else None
    ops = Operations(args.directory, task)
    try:
        if args.command in ("pause", "resume"):
            ops.pause(args.command == "pause")
        report = ops.status()
        if args.command == "audit":
            report["events"] = {
                r: ops.control.task_audit(r)
                for r in CAPABILITIES
                if ops.queue.db.execute(
                    "SELECT 1 FROM queue_tasks WHERE task_id=?", (r,)
                ).fetchone()
            }
        print(encoded(report))
    finally:
        ops.close()


if __name__ == "__main__":
    main()
