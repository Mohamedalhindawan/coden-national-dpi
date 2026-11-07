import io
import json
import tempfile
import unittest
from pathlib import Path

from skills.orchestration.queue import PersistentTaskQueue
from skills.orchestration.worker_runtime import WorkerAdmissionController
from skills.orchestration.worker_queue import WorkerQueueIntegration
from skills.orchestration.scheduler import DAGAwareScheduler
from skills.orchestration.control_plane import WorkflowControlPlane
from skills.orchestration.operator_api import WorkflowOperatorAPI
from skills.orchestration.observability import ObservabilityStore
from skills.orchestration.finops import BudgetLedger, BudgetLimit
from skills.orchestration.control_center import ControlCenter


class ObservabilityAPITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        queue = PersistentTaskQueue(root / "queue.sqlite")
        workers = WorkerAdmissionController(1, ["worker-a"], ["synthetic-test"])
        workers.register_worker("worker-a", ["synthetic-test"])
        scheduler = DAGAwareScheduler(queue, WorkerQueueIntegration(queue, workers), [])
        self.queue = queue
        self.metrics = ObservabilityStore(root / "metrics.sqlite")
        self.ledger = BudgetLedger(root / "finops.sqlite")
        self.ledger.set_budget(BudgetLimit("project-a", "daily", 10.0))
        self.ledger.set_budget(BudgetLimit("team-a", "daily", 5.0))
        self.metrics.record({
            "run_id":"run-1","task_id":"task-1","agent_id":"agent-a",
            "provider":"simulated","status":"succeeded","duration_ms":50,
            "input_tokens":10,"output_tokens":5,"cost_usd":0.01,
            "quality_score":1.0,"policy_violations":0,"retry_count":0,
            "evidence_ref":"artifact://run-1","project_id":"project-a",
            "team_id":"team-a","occurred_at":"2026-11-07T10:00:00+00:00"
        })
        self.center = ControlCenter(self.metrics, self.ledger)
        self.api = WorkflowOperatorAPI(
            WorkflowControlPlane(scheduler, workers),
            authenticator=lambda environ: ({"subject":"operator","role":"operator"}
                                           if environ.get("HTTP_AUTHORIZATION") else None),
            control_center=self.center,
        )

    def tearDown(self):
        self.queue.close()
        self.metrics.close()
        self.tmp.cleanup()

    def request(self, query="", token="operator"):
        environ = {"REQUEST_METHOD":"GET","PATH_INFO":"/v1/observability/snapshot",
                   "QUERY_STRING":query,"CONTENT_LENGTH":"0","wsgi.input":io.BytesIO(b""),
                   "HTTP_AUTHORIZATION":token}
        captured = {}
        payload = b"".join(self.api(environ, lambda status, headers:
                                   captured.update(status=status, headers=dict(headers))))
        return int(captured["status"].split()[0]), json.loads(payload or b"{}"), captured["headers"]

    def test_scoped_snapshot_requires_complete_scope_and_returns_no_store(self):
        code, body, headers = self.request(
            "project_id=project-a&team_id=team-a&period=daily&period_key=2026-11-07")
        self.assertEqual(code, 200)
        self.assertEqual(body["runs"]["total"], 1)
        self.assertEqual(body["scope"]["project_id"], "project-a")
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_snapshot_rejects_missing_or_invalid_scope(self):
        code, body, _ = self.request("project_id=project-a")
        self.assertEqual(code, 400)
        self.assertEqual(body["error"], "invalid_observability_scope")

    def test_snapshot_requires_authenticated_operator(self):
        code, body, _ = self.request(
            "project_id=project-a&team_id=team-a&period=daily&period_key=2026-11-07", token="")
        self.assertEqual(code, 401)
        self.assertEqual(body["error"], "unauthorized")


if __name__ == "__main__":
    unittest.main()
