# CODEN Workflow API & Operator Interface 1.0

**Status:** Experimental / Draft. WSGI application component; no server is bundled.

## Routes

| Method | Path | Purpose |
|---|---|---|
| GET | `/v1/workflows/status` | Read workflow/worker snapshot |
| POST | `/v1/workflows/pause` | Stop new dispatch admissions |
| POST | `/v1/workflows/resume` | Resume dispatch admissions |
| POST | `/v1/workflows/dispatch` | Claim one DAG-ready task for a registered worker |
| GET | `/v1/workflows/tasks/{task_id}/audit` | Read queue event history |

Dispatch request body: `{"worker_id":"worker-a"}`. The response intentionally excludes payload contents and lease tokens.

## Authentication and authorization boundary

The application requires an injected `authenticator(environ)` function. It must return a trusted principal object with a non-empty `subject` and role `operator` or `admin`; otherwise requests receive 401. This module does not validate JWTs, API keys, sessions, or passwords itself. The hosting service must implement authentication, TLS, role assignment, rate limiting, network restrictions, and security monitoring. Do not expose this prototype directly to the public internet.

## Safety controls

- JSON request bodies are capped at 16 KiB and must be objects.
- Responses use `Cache-Control: no-store`, JSON content type, and `nosniff`.
- Dispatch responses omit task payloads and lease fencing tokens.
- Operations delegate to the existing control plane and its DAG/worker constraints.
- No endpoint executes payloads, invokes providers, or accesses external networks.

## Local integration

Mount `WorkflowOperatorAPI(control_plane, authenticator)` in a WSGI-compatible host. The authenticator is an application-supplied trust boundary, not a placeholder to accept arbitrary user input.

## Tests

```bash
python -m unittest skills.tests.test_operator_api -v
python -m unittest discover -s skills/tests -v
```

## Limitations

No browser dashboard, user directory, identity provider, token validation, CSRF protection, rate limiting, TLS termination, persistent operator sessions, distributed control, or production deployment is included. The operator interface is an API component only.
