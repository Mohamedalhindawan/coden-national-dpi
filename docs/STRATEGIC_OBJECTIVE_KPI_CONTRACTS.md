# Strategic objectives and KPI contracts

These Draft 2020-12 schemas add a portfolio-level strategic objective and an objective-linked KPI definition. Objectives may optionally reference an initiative. KPI definitions capture the metric name, unit, baseline, target, direction, measurement frequency, lifecycle status, and accountable owner.

## Governance boundaries

A KPI definition is not a measured result. No actual values, source-system evidence, calculation logic, target approval, or performance conclusions are represented by these contracts. Metric owners must define numerator/denominator, inclusion/exclusion rules, source, collection method, data quality, reporting period, and privacy classification before operational use.

The JSON Schema validates each record independently. Cross-record IDs are checked in tests against synthetic fixtures; production persistence must enforce foreign keys and authorization transactionally. Do not place personal or citizen-identifiable data in KPI records.

## Synthetic-only status

The included examples are synthetic. These contracts do not create a dashboard, ingestion pipeline, KPI calculation engine, or executive reporting service.
