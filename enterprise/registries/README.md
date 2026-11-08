# CODEN V4.0 — Fifteen enterprise registries

**Status:** Registry design inventory, not 15 operational databases.

The V4.0 target registers are: agents, skills, models, tools, products, projects, components, DPI, APIs, vendors, services, risks, decisions, contracts and funding.

## Minimum record metadata
Unique ID, type, name, status, accountable human owner, created/updated timestamps, provenance, evidence links, approval status, sensitivity classification and change history.

## Current repository-level scaffolds
- Vendors: `enterprise/procurement/vendor-register.yaml`
- Contracts: `enterprise/contracts/contract-register.yaml`
- Risks: proposed in separate PR #51
- Skills: proposed in separate PR #50
- DPI: proposed in separate PR #52

All remaining registers require scoped designs and acceptance tests before operational use. Do not assume the separate PRs are merged.
