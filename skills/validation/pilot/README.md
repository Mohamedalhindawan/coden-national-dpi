# Pilot Benchmark — Five Skills

Status: Test design prepared; agent execution not yet performed.

All scenarios are fictional and use synthetic data. They are designed for a non-production Tamam demonstration only. No real identity provider, payment rail, government registry, or citizen record may be accessed.

| Skill | Case | Scenario class | Core evidence |
|---|---|---|---|
| PRD-01 | PRD-01-T01 | Normal + edge | Problem framing, measurable outcomes, accessibility, acceptance criteria |
| DPI-02 | DPI-02-T01 | Adversarial | Data minimization, assurance, recovery, exclusion, legal basis |
| AI-01 | AI-01-T01 | Adversarial + failure | Tool boundaries, prompt injection handling, approvals, kill switch |
| SEC-02 | SEC-02-T01 | Threat scenario | Threat model, controls, residual risk, incident escalation |
| QA-01 | QA-01-T01 | Failure + release | Traceability, negative tests, synthetic data, honest release gate |

## Execution protocol
Run each case against the skill in a clean, isolated session. Record model/agent version, system instructions, tool permissions, input fixture, raw output, tool trace, score, reviewer, cost, and latency. Do not compare model scores unless conditions are held constant.

## Current status
- Skill-file desk review: completed for the five selected files.
- Structural gap remediation: four files updated; DPI-02 already contained the required section headings.
- Scenario definitions: drafted below.
- Agent execution and scoring: pending.
- Lifecycle: all five remain Draft.
