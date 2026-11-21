# Example project specification — CODEN synthetic service

**Status:** DRAFT / DEMO. Replace for each independently reviewed project. This is not a production GovTech system.

## User story
Given a bounded list of synthetic tasks, the service returns deterministic counts for queued, in-progress, blocked and completed tasks.

## Acceptance criteria
1. Python 3.12 standard library only. No network, database, model calls or disk writes in the example function.
2. At most 100 items per call; each item has exactly task_id, status and classification.
3. Classification must be synthetic. Invalid fields, status, task ID and duplicate task IDs (including conflicting statuses) are rejected.
4. A fresh, generated repository passes `python -m unittest discover -s tests -v` without installation.
5. Passing tests authorizes **neither** repository deployment nor production handling.

## Productization backlog (NOT IMPLEMENTED)
- Replace this demo with a product-specific, threat-modeled spec and real acceptance suite.
- Independently verify source licenses and supply chain before adopting dependencies.
- Establish human code owner, release and data classification approvals.
