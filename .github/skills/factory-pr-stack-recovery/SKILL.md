---
name: factory-pr-stack-recovery
description: Recover and consolidate CODEN Factory's many stacked draft pull requests in dependency order without losing tested changes, bypassing CI or merging into main automatically.
---
# CODEN Factory — PR dependency recovery and low-conflict delivery

## Trigger
Use when a task is scattered across Draft PRs, multiple branches claim overlapping work, CI seems duplicated, or the factory cannot proceed because upstream changes are not merged. Status: **DRAFT**.

## Steps
1. Query the actual GitHub PR head SHA, **base branch**, draft/merged state, changed files and checks. Never assume a Draft PR's passing CI means its changes are on `main`.
2. Build a simple dependency DAG: each child depends on its true base SHA/branch. Distinguish sibling workstreams (OpenHands, real Qwen, source catalog, Supabase); avoid accidental unrelated squashing.
3. Check which files are already covered in the parent and which PR duplicates or conflicts. Prefer small, independently reviewable commits; reuse tested work and explicit cherry-pick/rebase only with operator-approved scope.
4. For every dependency, retain RED/GREEN CI links, source manifests, checksum, test matrix and unresolved security/review blockers. Do not claim success based on old CI from a different HEAD SHA.
5. Recommend a smallest-ready-first review order. Label blocked runtime issues (#162) and source admission (#159) separately; do not pretend review-only catalog files are runtime services.
6. Once each change is approved by a human, merge through the repository's own protected process and re-run checks on the actual combined HEAD. No automatic merge or irreversible release.

## Artifact
Return a compact table: PR, base branch, head SHA, CI result, review status, blocker, next action. On failures record a reproducible rollback route and BLOCKED. Human review required; no automatic merge, no force push to `main`, no disabling tests. Do not claim everything integrated into production until actual combined integration checks pass.
