# Risk registry ↔ enterprise risk schema reconciliation (Issue #55)

**Status:** BLOCKED — human schema/instance ownership decision required. This is a read-only compatibility audit, not a migration, acceptance, or production risk register.

Sources reviewed 2026-11-10:
- [PR #46 schema](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/46): `schemas/enterprise/risk.schema.json` (draft 2020-12).
- [PR #51 registry](https://github.com/Mohamedalhindawan/coden-national-dpi/pull/51): `enterprise/risk/risk-register.yaml`.
- [Issue #55](https://github.com/Mohamedalhindawan/coden-national-dpi/issues/55).

## Confirmed incompatibilities

| #51 registry field | #46 schema | Required resolution |
|---|---|---|
| `id` | `risk_id` required | Explicit identifier mapping; preserve source IDs |
| `owner` | `risk_owner_id` optional, required for mitigating/accepted/closed | Map only authenticated, assigned owners; `unassigned` is not approval |
| `mitigation` | `mitigation_plan` | Explicit mapping |
| `severity: high` | `likelihood` and `impact` integers 1–5 required | Cannot infer two independent ratings from severity |
| `status: open` | Enum identified/assessing/mitigating/accepted/closed | Requires human-approved lifecycle mapping |
| `evidence` | No corresponding property; `additionalProperties: false` | Preserve as separate provenance, not silently drop |
| Missing `initiative_id` | Required | Assign validated initiative reference |
| Missing `description` on RISK-002 | Required | Obtain reviewed description |
| Missing `identified_at` | Required date-time | Obtain original identification timestamp; never invent |

The #51 document is a **registry template** with a `risks` array; #46 describes **one risk record**. Passing the full YAML object directly to the record schema is invalid even if individual records were remapped. Do not silently coerce ratings, lifecycle states, owners, timestamps, or evidence.

## Proposed safe integration contract (not approved)

1. Preserve the original YAML registry and its evidence URLs without modification.
2. Assign a human owner to define the canonical schema and approve a versioned mapping.
3. For each source record, emit a migration diagnostic listing missing/invalid fields; reject incomplete records rather than invent values.
4. Keep original `severity` and `evidence` as provenance outside the strict schema until an approved extension exists.
5. Validate migrated records with the #46 Draft202012 schema and format checking; use synthetic fixtures only.
6. Require explicit human sign-off before adopting any registry as the source of truth or merging stacked PRs.

## Acceptance gates

- [ ] Canonical schema/instance owner assigned by human reviewer.
- [ ] Lifecycle and severity mappings approved with no inferred risk scores.
- [ ] Complete synthetic fixtures validate against the exact #46 schema.
- [ ] Rejected incomplete fixtures have recorded diagnostics.
- [ ] CI on combined candidate branch and independent review completed.

No claim is made that #46 and #51 are compatible or merged.
