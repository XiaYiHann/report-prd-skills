# Operational Readiness Checklist

Use this checklist for engineering reports. Its purpose is to make Linus-style maintainability concrete: interfaces, ownership, failure handling, and source-of-truth boundaries must be obvious.

## Required Operational Matrix

Engineering reports should include an operational readiness table with these columns:

| Component | Source-of-truth | Owner | Interface boundary | Failure mode | Runbook / rollback | Compatibility bridge retirement |
| --- | --- | --- | --- | --- | --- | --- |

## Required Questions

- What is the authoritative write path for each critical state?
- Which component owns the interface contract?
- Which API, schema, queue, or file is the public boundary?
- How does an operator detect the failure?
- What is the first recovery action?
- What is the rollback path?
- Which compatibility bridge exists, why does it exist, and what condition retires it?

## Audit Failures

Flag the report when it:

- claims stability without build, test, deploy, or rollback evidence.
- documents a compatibility bridge without a retirement condition.
- spreads source-of-truth across multiple layers.
- explains a strange interface instead of simplifying it.
- leaves on-call behavior as prose without a runbook or failure matrix.
