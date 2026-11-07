# CODEN Enterprise Skills Library

Version: 1.0.0  
Status: Draft for review  
Parent framework: CODEN Enterprise Operating & Engineering Playbook 2.2

This library contains reusable, reviewable work instructions for CODEN teams and AI agents. A skill is not considered approved merely because its file exists.

## Structure

- `registry.yaml`: authoritative inventory and lifecycle status.
- `templates/SKILL_TEMPLATE.md`: required structure for new skills.
- `01-strategy-governance/`: strategy and enterprise architecture.
- `02-dpi-architecture/`: DPI and GovTech architecture.
- `03-product-management/`: digital product management.
- `04-software-architecture/`: software architecture.
- `05-platform-engineering/`: platform engineering.
- `06-ai-agent-engineering/`: AI agent engineering.
- `07-ai-evaluation-governance/`: AI evaluation and governance.
- `08-devsecops/`: DevSecOps.
- `09-cybersecurity-architecture/`: cybersecurity architecture.
- `10-quality-engineering/`: quality engineering.

## Lifecycle

Draft → Reviewed → Tested → Approved → Published → Monitored → Updated/Retired.

Every skill must have an owner, version, scope, inputs, workflow, deliverables, quality gates, security controls, and evaluation evidence before approval.

## Safety and project boundaries

- Treat this repository as a proposal/prototype workspace, not an approved national production environment.
- Use synthetic data only in the current Tamam prototype.
- Never place credentials, secrets, or real citizen records in skills or examples.
- AI agents must use least-privilege, short-lived access and isolated workspaces.
- Require human approval for production changes and high-impact decisions involving identity, benefits, money, health, legal rights, or citizen data.
- Do not assume any listed tool, cloud credit, partnership, certification, or government authority has been approved.

## How to add a skill

Copy the template, assign a unique ID, name an accountable owner, define acceptance tests, and submit the skill for review. Do not change a skill to Approved without evidence and an authorized reviewer.
