# CODEN Operator Dashboard 1.0

**Status:** Experimental static dashboard asset; not deployed.

## Asset

Open `index.html` in `skills/orchestration/operator-dashboard/` from a trusted local copy or host it behind the same trusted origin as the Operator API.

The dashboard is Arabic RTL and provides:
- Workflow state counters (pending, running, succeeded, failed, cancelled, blocked).
- Pause/resume controls.
- Worker capacity and capability table.
- Manual dispatch for a selected registered worker.\n- Project/team-scoped observability summary: run count, success rate, tokens, recorded cost, quality, policy violations, and legacy unattributed metric count.
- Configurable API base path.

## Security

The operator token is held only in the current page's JavaScript memory/input field and is not written to localStorage or sessionStorage. The page sends requests with `cache: no-store` and same-origin credentials. It does not load external scripts, fonts, stylesheets, analytics, or other remote resources. Dynamic API values are inserted with `textContent`, not HTML interpretation.

Serve the page over HTTPS from a trusted origin. Configure the host's authenticator to validate the Authorization header and return a trusted principal. Do not rely on this dashboard as an authentication system. Do not publish the API or dashboard openly without TLS, robust authentication, role-based authorization, rate limiting, CSRF/CORS review, and operational monitoring.

## API compatibility

The dashboard consumes the workflow routes and optional `/v1/observability/snapshot` route documented in `../operator-api/README.md`. The metrics panel requires project, team, period, and period key. Cost/token values are displayed as recorded by the local metrics store and must not be interpreted as verified live provider billing. Detailed event timelines, approvals, and per-task controls remain unavailable.

## Verification

Static asset contract test:

```bash
python -m unittest skills.tests.test_operator_dashboard -v
```

No browser-based runtime test or deployment is claimed by this change.
