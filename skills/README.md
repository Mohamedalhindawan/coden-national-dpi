# CODEN Enterprise Skills Library

Version: 1.0.0  
Status: Draft for review  
Parent framework: CODEN Enterprise Operating & Engineering Playbook 2.2

This library contains **60 registered draft skill specifications** for CODEN teams and AI agents. The registry is the inventory of record. A skill is not approved merely because its file exists.

## Structure

- `registry.yaml`: inventory, IDs, owners, paths, and lifecycle status.
- `templates/SKILL_TEMPLATE.md`: required structure for new skills.
- `tests/test_registry.py`: automated checks for the 60-skill count, unique IDs, file existence, required sections, and draft status.
- `validation/`: scoring rubric, mandatory safety gates, benchmark protocol, and case template.
- `orchestration/`: multi-agent architecture, workforce roles, task contracts, permission matrix, state machine, operations runbook, and synthetic pilot scenarios.
- `01-strategy-governance/`: strategy and governance.
- `02-dpi-architecture/`: DPI and GovTech architecture.
- `03-product-management/`: product and service design.
- `04-software-architecture/`: software and solution architecture.
- `05-platform-engineering/`: platform and delivery engineering.
- `06-ai-agent-engineering/`: AI agent engineering.
- `07-ai-evaluation-governance/`: AI evaluation and governance.
- `08-devsecops/`: secure software delivery.
- `09-cybersecurity-architecture/`: cybersecurity architecture.
- `10-quality-engineering/`: quality engineering.
- `11-data-governance/`: data architecture, engineering, governance, privacy, and analytics.
- `12-cloud-finops-procurement/`: cloud, FinOps, financial modeling, procurement, and IP.
- `13-management-delivery/`: project and change management.

## Lifecycle

Draft → Reviewed → Tested → Approved → Published → Monitored → Updated/Retired.

Every skill must have an owner, version, scope, inputs, workflow, deliverables, quality gates, security controls, and evaluation evidence before approval.

## Safety and project boundaries

- This repository is a proposal/prototype workspace, not an approved national production environment.
- Use synthetic data only in the current Tamam prototype.
- Never place credentials, secrets, or real citizen records in skills or examples.
- AI agents must use least-privilege, short-lived access and isolated workspaces.
- Require human approval for production changes and high-impact decisions involving identity, benefits, money, health, legal rights, or citizen data.
- Do not assume any listed tool, cloud credit, partnership, certification, or government authority has been approved.

## How to add a skill

Copy the template, assign a unique ID, name an accountable owner, define acceptance tests, and submit the skill for review. Do not change a skill to Approved without evidence and an authorized reviewer.

## Validation

Run from the repository root:

```bash
python -m unittest discover -s skills/tests -v
```
