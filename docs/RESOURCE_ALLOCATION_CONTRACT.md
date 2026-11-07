# Resource allocation contract

This contract records a proposed or approved allocation of a named resource to an initiative for a date-bounded period. It captures the allocation percentage and the role expected for that assignment.

## Approval boundary

Allocations in `proposed` state are planning records only. Records in `approved`, `active`, or `completed` state must identify `approved_by`. The schema does not authenticate the approver, establish delegated authority, or enforce separation of duties; those checks belong in the service and policy layer.

## Capacity and scheduling limitations

- `allocation_percent` is an individual record value from 1 to 100.
- This schema does not calculate aggregate utilization, prevent overlapping assignments, or guarantee that a resource is available.
- Date-range ordering and cross-record references must be enforced by application logic; JSON Schema validates date formats but does not compare dates.
- No payroll, HR, procurement, financial commitment, or real agent provisioning is performed.

## Data handling

Use synthetic identifiers in fixtures. Production records require access controls, retention rules, auditable changes, and privacy review. Changes should be versioned rather than silently overwriting approved allocation history.
