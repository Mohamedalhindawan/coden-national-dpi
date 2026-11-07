# CODEN Operator Dashboard 1.0

**Status:** Experimental static dashboard asset; not deployed.

## Asset

Open `index.html` in `skills/orchestration/operator-dashboard/` from a trusted local copy or host it behind the same trusted origin as the Operator API.

The dashboard is Arabic RTL and provides:
- Workflow state counters (pending, running, succeeded, failed, cancelled, blocked).
- Pause/resume controls.
- Worker capacity and capability table.
- Manual dispatch for a selected registered worker.
- Configurable API base path.

## Security

The operator token is held only in the current page's JavaScript memory/input field and is not written to localStorage or sessionStorage. The page sends requests with `cache: no-store` and same-origin credentials. It does not load external scripts, fonts, stylesheets, analytics, or other remote resources. Dynamic API values are inserted with `textContent`, not HTML interpretation.

Serve the page over HTTPS from a trusted origin. Configure the host's authenticator to validate the Authorization header and return a trusted principal. Do not rely on this dashboard as an authentication system. Do not publish the API or dashboard openly without TLS, robust authentication, role-based authorization, rate limiting, CSRF/CORS review, and operational monitoring.

## API compatibility

The dashboard consumes the routes documented in `../operator-api/README.md`. It displays only fields returned by the API and does not infer cost or token usage. The current API does not expose cost telemetry, detailed event timelines, approvals, or per-task controls.

## Verification

Static asset contract test:

```bash
python -m unittest skills.tests.test_operator_dashboard -v
```

No browser-based runtime test or deployment is claimed by this change.
