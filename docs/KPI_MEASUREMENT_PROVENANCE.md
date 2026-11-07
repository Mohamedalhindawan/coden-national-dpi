# KPI measurement and provenance contract

A KPI definition describes what should be measured; a KPI measurement is a period-specific observation. Each measurement records its KPI reference, numeric value, reporting period, measurement timestamp, source reference, optional sample size, and review status.

## Verification boundary

A record marked `verified` must identify a reviewer, but this schema does not authenticate that reviewer or prove the source data. Production services must enforce reviewer authorization, separation of duties, source integrity, reporting-period consistency, idempotency, and immutable correction history. Corrections should supersede prior records rather than silently overwrite them.

## Privacy and evidence

`source_ref` should point to a controlled, permission-aware evidence location—not contain raw datasets, credentials, or personal data. Synthetic fixtures only. This contract does not ingest data, calculate KPIs, or publish dashboards.
