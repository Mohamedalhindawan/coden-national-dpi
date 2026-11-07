"""Minimal WSGI operator API for the local workflow control plane.

Authentication is injected by the host application. This module never parses
or stores bearer credentials and is not a standalone internet-facing server.
"""
import json
import re
from urllib.parse import parse_qs


class OperatorAPIError(ValueError):
    pass


class WorkflowOperatorAPI:
    MAX_BODY_BYTES = 16 * 1024

    def __init__(self, control_plane, authenticator, control_center=None, finops_governance=None):
        if not callable(authenticator):
            raise OperatorAPIError("An authentication provider is required")
        self.control_plane = control_plane
        self.authenticator = authenticator
        self.control_center = control_center
        self.finops_governance = finops_governance

    @staticmethod
    def _response(start_response, status, payload):
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        start_response(status, [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
            ("X-Content-Type-Options", "nosniff"),
        ])
        return [body]

    def _principal(self, environ):
        try:
            principal = self.authenticator(environ)
        except Exception:
            principal = None
        if not isinstance(principal, dict):
            return None
        subject = principal.get("subject")
        if not isinstance(subject, str) or not subject.strip() or len(subject) > 256:
            return None
        if principal.get("role") not in {"operator", "admin", "finance_operator", "finance_approver", "finance_admin"}:
            return None
        return {**principal, "subject": subject.strip()}

    def _body(self, environ):
        raw_length = environ.get("CONTENT_LENGTH", "") or "0"
        try:
            length = int(raw_length)
        except (TypeError, ValueError):
            raise OperatorAPIError("invalid_content_length")
        if length < 0 or length > self.MAX_BODY_BYTES:
            raise OperatorAPIError("request_body_too_large")
        stream = environ.get("wsgi.input")
        if length and stream is None:
            raise OperatorAPIError("invalid_request_body")
        raw = stream.read(length) if length else b"{}"
        if not isinstance(raw, bytes) or (length and len(raw) != length):
            raise OperatorAPIError("invalid_request_body")
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise OperatorAPIError("invalid_json")
        if not isinstance(value, dict):
            raise OperatorAPIError("json_object_required")
        return value

    def __call__(self, environ, start_response):
        principal = self._principal(environ)
        if principal is None:
            return self._response(start_response, "401 Unauthorized", {"error": "unauthorized"})
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")
        try:
            if path.startswith("/v1/finops/reconciliations"):
                if self.finops_governance is None:
                    return self._response(start_response, "404 Not Found", {"error": "not_found"})
                role, actor_id = principal.get("role"), principal.get("subject")
                finance_roles = {"finance_operator", "finance_approver", "finance_admin"}
                if method == "GET" and path == "/v1/finops/reconciliations":
                    if role not in finance_roles:
                        return self._response(start_response, "403 Forbidden", {"error": "forbidden"})
                    return self._response(start_response, "200 OK", {"requests": self.finops_governance.list_requests()})
                audit_match = re.fullmatch(r"/v1/finops/reconciliations/([A-Za-z0-9_.:-]+)/audit", path)
                if method == "GET" and audit_match:
                    if role not in finance_roles:
                        return self._response(start_response, "403 Forbidden", {"error": "forbidden"})
                    rid = audit_match.group(1)
                    events = self.finops_governance.audit_events(rid)
                    if not events:
                        return self._response(start_response, "404 Not Found", {"error": "not_found"})
                    return self._response(start_response, "200 OK", {"request_id": rid, "events": events})
                if method == "POST" and path == "/v1/finops/reconciliations":
                    if role not in {"finance_operator", "finance_admin"}:
                        return self._response(start_response, "403 Forbidden", {"error": "forbidden"})
                    if environ.get("CONTENT_TYPE", "").split(";", 1)[0].strip().lower() != "application/json":
                        return self._response(start_response, "415 Unsupported Media Type", {"error": "unsupported_media_type"})
                    body = self._body(environ)
                    try:
                        result = self.finops_governance.submit_reconciliation(body.get("reservation_id"), body.get("actual_usd"), actor_id, role, body.get("request_id"))
                    except ValueError:
                        return self._response(start_response, "400 Bad Request", {"error": "invalid_reconciliation_request"})
                    return self._response(start_response, "201 Created", result)
                decision = re.fullmatch(r"/v1/finops/reconciliations/([A-Za-z0-9_.:-]+)/(approve|reject)", path)
                if method == "POST" and decision:
                    if role not in {"finance_approver", "finance_admin"}:
                        return self._response(start_response, "403 Forbidden", {"error": "forbidden"})
                    if environ.get("CONTENT_TYPE", "").split(";", 1)[0].strip().lower() != "application/json":
                        return self._response(start_response, "415 Unsupported Media Type", {"error": "unsupported_media_type"})
                    self._body(environ)
                    rid, action = decision.groups()
                    try:
                        result = self.finops_governance.approve_reconciliation(rid, actor_id, role) if action == "approve" else self.finops_governance.reject_reconciliation(rid, actor_id, role)
                    except ValueError:
                        return self._response(start_response, "409 Conflict", {"error": "reconciliation_operation_rejected"})
                    return self._response(start_response, "200 OK", result)
                return self._response(start_response, "404 Not Found", {"error": "not_found"})
            if method == "GET" and path == "/v1/workflows/status":
                return self._response(start_response, "200 OK", self.control_plane.snapshot())
            if method == "GET" and path == "/v1/observability/snapshot":
                if self.control_center is None:
                    return self._response(start_response, "404 Not Found", {"error": "not_found"})
                query = parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=True)
                required = ("project_id", "team_id", "period", "period_key")
                values = {key: query.get(key, [""])[0] for key in required}
                if any(not value.strip() for value in values.values()):
                    return self._response(start_response, "400 Bad Request", {"error": "invalid_observability_scope"})
                try:
                    report = self.control_center.snapshot(**values)
                except (ValueError, KeyError):
                    return self._response(start_response, "400 Bad Request", {"error": "invalid_observability_scope"})
                return self._response(start_response, "200 OK", report)
            if method == "POST" and path in {
                "/v1/workflows/pause", "/v1/workflows/resume", "/v1/workflows/dispatch"
            }:
                body = self._body(environ)
                if path.endswith("/pause"):
                    return self._response(start_response, "200 OK", self.control_plane.pause())
                if path.endswith("/resume"):
                    return self._response(start_response, "200 OK", self.control_plane.resume())
                worker_id = body.get("worker_id")
                if not isinstance(worker_id, str) or not worker_id.strip():
                    return self._response(start_response, "400 Bad Request", {"error": "worker_id_required"})
                claim = self.control_plane.dispatch(worker_id)
                if claim is None:
                    return self._response(start_response, "204 No Content", {})
                return self._response(start_response, "200 OK", {
                    "task_id": claim["task_id"], "worker_id": claim["worker_id"],
                    "lease_expires": claim["lease_expires"], "attempts": claim["attempts"],
                })
            match = re.fullmatch(r"/v1/workflows/tasks/([A-Za-z0-9_.:-]+)/audit", path)
            if method == "GET" and match:
                return self._response(start_response, "200 OK", {
                    "task_id": match.group(1), "events": self.control_plane.task_audit(match.group(1))
                })
            if method not in {"GET", "POST"}:
                return self._response(start_response, "405 Method Not Allowed", {"error": "method_not_allowed"})
            return self._response(start_response, "404 Not Found", {"error": "not_found"})
        except OperatorAPIError as exc:
            return self._response(start_response, "400 Bad Request", {"error": str(exc)})
        except ValueError as exc:
            message = str(exc)
            status = "409 Conflict" if "paused" in message.lower() or "admission" in message.lower() else "400 Bad Request"
            return self._response(start_response, status, {"error": "workflow_operation_rejected"})
