# coden-national-dpi

AI-Native Open-Source National Digital Public Infrastructure for Yemen.

## Project status

CODEN / YDS / Tamam is a proposal and prototype, not an approved national production system. Use synthetic data only. No real beneficiary records or payment decisions belong in the current demo.

## Start here

- [**Master engineering playbook**](CODEN_MASTER_ENGINEERING_PLAYBOOK.md) — full vision, 31-sector/DPI scope, workflow, and status
- [Project overview](docs/PROJECT_OVERVIEW.md)
- [Open-source reuse assessment](docs/OPEN_SOURCE_REUSE_ASSESSMENT.md)
- [Open-source reuse register and integration gates](docs/OPEN_SOURCE_REUSE_REGISTER.md)
- [Free-first AI agent workflow](docs/AGENT_WORKFLOW.md)
- [Free-first agent roadmap](docs/FREE_FIRST_AGENT_ROADMAP.md)
- [AI agent toolchain](docs/AI_AGENT_TOOLCHAIN.md)
- [First coding agent setup](docs/FIRST_CODING_AGENT_SETUP.md)
- [Prototype instructions](app/README.md)

## Current prototype

A small Arabic RTL browser demo for a synthetic social-assistance application. It runs locally in the browser and does not send records to a server. It does not provide real authentication, persistence, or official eligibility decisions.

## Principles

1. Reuse proven open-source systems where fit and licensing are verified.
2. Keep integrations modular and use documented APIs.
3. Start with a narrow workflow and synthetic data.
4. Require human review for high-impact identity, financial and social-benefit decisions.
5. Verify tests and security before claiming readiness.

## API contract draft

- [OpenAPI specification for the assistance workflow](api/openapi.yaml)

This is a contract draft only. No backend is implemented by adding this file. The contract intentionally restricts the current prototype to synthetic records and requires server-side authentication, authorization, validation, and audit events before any real deployment.
