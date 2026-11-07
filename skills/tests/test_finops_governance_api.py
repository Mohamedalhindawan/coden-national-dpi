import io
import json
import tempfile
import unittest
from pathlib import Path

from skills.orchestration.finops import BudgetLedger, SpendRequest
from skills.orchestration.finops_governance import FinOpsGovernance
from skills.orchestration.operator_api import WorkflowOperatorAPI


class FinOpsGovernanceAPITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.ledger = BudgetLedger(root / "ledger.sqlite")
        self.reservation = self.ledger.reserve(SpendRequest(
            "spend-1", "project-a", "team-a", 2.0,
            "2026-11-07T10:00:00+00:00", run_id="run-1"))
        self.governance = FinOpsGovernance(self.ledger, root / "governance.sqlite")
        self.principals = {
            "maker": {"subject": "maker-1", "role": "finance_admin"},
            "checker": {"subject": "checker-1", "role": "finance_approver"},
            "viewer": {"subject": "viewer-1", "role": "operator"},
        }
        self.api = WorkflowOperatorAPI(
            control_plane=object(),
            authenticator=lambda environ: self.principals.get(environ.get("HTTP_AUTHORIZATION")),
            finops_governance=self.governance,
        )

    def tearDown(self):
        self.governance.close()
        self.tmp.cleanup()

    def request(self, method, path, token="maker", body=None):
        raw = json.dumps(body or {}).encode("utf-8")
        environ = {
            "REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": "",
            "CONTENT_LENGTH": str(len(raw)), "wsgi.input": io.BytesIO(raw),
            "HTTP_AUTHORIZATION": token,
        }
        captured = {}
        payload = b"".join(self.api(environ, lambda status, headers:
                                    captured.update(status=status, headers=dict(headers))))
        return int(captured["status"].split()[0]), json.loads(payload or b"{}"), captured["headers"]

    def test_submit_uses_authenticated_identity_and_ignores_body_role_claims(self):
        code, body, headers = self.request("POST", "/v1/finops/reconciliations", body={
            "request_id": "recon-api-1",
            "reservation_id": self.reservation["reservation_id"],
            "actual_usd": 1.25,
            "actor_id": "attacker",
            "role": "finance_admin",
        })
        self.assertEqual(code, 201)
        self.assertEqual(body["submitted_by"], "maker-1")
        self.assertEqual(body["status"], "pending")
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_submit_rejects_principal_without_finance_role(self):
        code, body, _ = self.request("POST", "/v1/finops/reconciliations", token="viewer", body={
            "request_id": "recon-api-2",
            "reservation_id": self.reservation["reservation_id"],
            "actual_usd": 1.0,
        })
        self.assertEqual(code, 403)
        self.assertEqual(body["error"], "forbidden")

    def test_maker_cannot_approve_own_request_but_checker_can(self):
        self.governance.submit_reconciliation(
            self.reservation["reservation_id"], 1.25, "maker-1",
            "finance_operator", "recon-api-3")
        code, body, _ = self.request(
            "POST", "/v1/finops/reconciliations/recon-api-3/approve", token="maker")
        self.assertEqual(code, 409)
        self.assertEqual(body["error"], "reconciliation_operation_rejected")
        code, body, _ = self.request(
            "POST", "/v1/finops/reconciliations/recon-api-3/approve", token="checker")
        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "approved")
        self.assertEqual(body["decided_by"], "checker-1")

    def test_list_and_audit_are_read_only_and_include_decisions(self):
        self.governance.submit_reconciliation(
            self.reservation["reservation_id"], 1.0, "maker-1",
            "finance_operator", "recon-api-4")
        self.governance.reject_reconciliation(
            "recon-api-4", "checker-1", "finance_approver")
        code, body, _ = self.request("GET", "/v1/finops/reconciliations")
        self.assertEqual(code, 200)
        self.assertEqual(body["requests"][0]["status"], "rejected")
        code, body, _ = self.request(
            "GET", "/v1/finops/reconciliations/recon-api-4/audit")
        self.assertEqual(code, 200)
        self.assertEqual([event["event_type"] for event in body["events"]],
                         ["reconciliation_submitted", "reconciliation_rejected"])

    def test_reject_endpoint_records_rejection_without_ledger_reconciliation(self):
        self.governance.submit_reconciliation(
            self.reservation["reservation_id"], 1.0, "maker-1",
            "finance_operator", "recon-api-5")
        code, body, _ = self.request(
            "POST", "/v1/finops/reconciliations/recon-api-5/reject", token="checker")
        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "rejected")
        self.assertEqual(self.ledger.reconciliation_snapshot(
            "project-a", "team-a", "daily", "2026-11-07")["reconciled_runs"], 0)

    def test_oversized_and_invalid_json_requests_are_rejected(self):
        code, _, _ = self.request("POST", "/v1/finops/reconciliations", body={
            "request_id": "x" * 20000,
        })
        self.assertEqual(code, 400)


if __name__ == "__main__":
    unittest.main()
