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


class OperatorAPITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        queue = PersistentTaskQueue(Path(self.tmp.name) / "queue.sqlite")
        workers = WorkerAdmissionController(1, ["worker-a"], ["synthetic-test"])
        workers.register_worker("worker-a", ["synthetic-test"])
        scheduler = DAGAwareScheduler(queue, WorkerQueueIntegration(queue, workers), [
            {"task_id": "task-1", "depends_on": [], "payload": {"kind": "synthetic-test"}}
        ])
        self.queue = queue
        self.api = WorkflowOperatorAPI(WorkflowControlPlane(scheduler, workers),
                                      authenticator=lambda environ: environ.get("HTTP_AUTHORIZATION"))

    def tearDown(self):
        self.queue.close()
        self.tmp.cleanup()

    def request(self, method, path, token="operator", body=None):
        raw = json.dumps(body or {}).encode()
        environ = {
            "REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": "",
            "CONTENT_LENGTH": str(len(raw)), "wsgi.input": io.BytesIO(raw),
            "HTTP_AUTHORIZATION": token,
        }
        captured = {}
        def start(status, headers):
            captured["status"] = status
            captured["headers"] = headers
        payload = b"".join(self.api(environ, start))
        return int(captured["status"].split()[0]), json.loads(payload or b"{}")

    def test_status_requires_authenticated_operator(self):
        code, _ = self.request("GET", "/v1/workflows/status", token="")
        self.assertEqual(code, 401)
        code, body = self.request("GET", "/v1/workflows/status")
        self.assertEqual(code, 200)
        self.assertIn("tasks", body)

    def test_pause_resume_and_dispatch_routes(self):
        self.assertEqual(self.request("POST", "/v1/workflows/pause")[0], 200)
        self.assertEqual(self.request("POST", "/v1/workflows/dispatch", body={"worker_id":"worker-a"})[0], 409)
        self.assertEqual(self.request("POST", "/v1/workflows/resume")[0], 200)
        code, body = self.request("POST", "/v1/workflows/dispatch", body={"worker_id":"worker-a"})
        self.assertEqual(code, 200)
        self.assertEqual(body["task_id"], "task-1")

    def test_unknown_route_and_invalid_json_are_safe_errors(self):
        self.assertEqual(self.request("GET", "/unknown")[0], 404)
        environ = {"REQUEST_METHOD":"POST", "PATH_INFO":"/v1/workflows/pause",
                   "CONTENT_LENGTH":"1", "wsgi.input":io.BytesIO(b"{"),
                   "HTTP_AUTHORIZATION":"operator"}
        result = {}
        response = b"".join(self.api(environ, lambda status, headers: result.update(status=status)))
        self.assertEqual(int(result["status"].split()[0]), 400)
        self.assertIn(b"invalid_json", response)
