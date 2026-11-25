---
name: factory-independent-review
description: Independently verify CODEN agent outputs, real model provenance, hidden acceptance, SHA-256 artifacts and negative tests before any developer's result can be considered review-ready.
---
# CODEN Factory — Evidence-led independent reviewer

## Trigger
Use after the coding agent/model produces code, an artifact, workflow logs or a Draft PR. Keep generation and review logically separate; **DRAFT** guidance.

## Steps
1. Identify exact task ID, origin runner, commit, model ID, input contract, approved source pins and candidate output. Distinguish a real model run from a fake-sdk unit test or canned fixture.
2. Compute SHA-256 for received package and for each proposed code artifact. Match recorded hashes before viewing/extracting candidate contents; avoid import/exec/compile of unreviewed code.
3. Verify repository and paths are allowlisted, reject symlinks/traversal/overwrites, and inspect suspicious operations and dependency changes.
4. Test hidden acceptance (not disclosed to coding model), negative cases, lints/security checks and runtime sandbox evidence. A model's own generated tests cannot self-certify correctness.
5. Confirm `release_authorized=false`, `paid_calls=0`, no credentials/PII, no automatic source enable, no unauthorized deployment or merge.
6. Produce independent PASS/FAIL/BLOCKED with exact GitHub Actions run, evidence artifact, limitations, reviewer and the necessary next approval. Report failures rather than editing evidence to match expectations.

## Relevant existing evidence
Authentic Qwen candidate: Draft PR #164, generated package SHA-256 `e011e317dc06efb6870978d40e4d17263a308c30655a565518006af23b564573`; real catalog report Draft PR #165 keeps generated source quarantined. Do not claim code was production-admitted. Human review and **no automatic merge** are non-negotiable.
