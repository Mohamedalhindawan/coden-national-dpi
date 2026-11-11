# CODEN V4.0 progress measurement — baseline gate (draft)

This is a **measurement tool, not the V4.0 master text or an approved requirements matrix**. Do not replace, shorten, or infer the signed V4.0 source from this file.

Before publishing a completion percentage:
1. Locate and checksum the exact approved full V4.0 master; record immutable source revision and approval.
2. Extract every atomic requirement across all eight phases; assign stable IDs, domain and nonzero weights with documented weighting rationale.
3. Review the inventory for omissions and duplicates; secure human approval of the denominator and weights.
4. Link each accepted requirement to independently reviewed implementation evidence, actual passing tests and human acceptance.
5. Supply the approved rows to `scripts.v4_progress.calculate`. It returns `None` for missing phases, missing domains, malformed weights, duplicate IDs, or unverified acceptance. A return value is **not** proof the inventory is exhaustive: that requires separate human review.

Domains: `governance_docs`, `ai_factory`, `tamam_dpi`, `security_ops`. The four domain percentages and global percentage use weighted denominators, not PR counts. No percentages are published until the full baseline is verified.

Tests use synthetic requirements only. No citizen records, merge, deployment, or financial actions.
