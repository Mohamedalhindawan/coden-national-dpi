# CODEN Factory — Independent Artifact Evidence Verification

**State:** experimental, offline, **read-only** evidence validation.  
**Implementation:** `ai_factory/artifact_evidence.py`, `ai_factory/artifact_cli.py`.  
**Tests:** `tests/test_factory_artifact_evidence.py`, `tests/test_factory_artifact_cli.py`.  
**Runtime contract:** `ai_factory/runtime_contract.py`.

## What was missing?

The existing provider-neutral runtime contract accepted a **SHA-256 value reported by a model adapter**, but could not prove that a file with that digest actually exists. An agent could report success without producing the expected files, or a file could change after the agent produced the report.

This change adds an **independent filesystem comparison** for synthetic task artifacts. It still does not establish that the source code is correct, that tests passed, that the model was authorized, or that a release is approved.

## Evidence contract

There are four inputs:

1. `request.json`: the existing `coden.runtime.request.v1` task policy, synthetic-only.
2. `report.json`: a `coden.runtime.report.v1` report in `completed` status, with a 64-hex `artifact_sha256`.
3. `manifest.json`: a `coden.artifact.bundle.v1` **canonical file manifest** containing `task_id` and a sorted array of output records.
4. `--root`: an operator-owned directory containing the real files to verify, with no unlisted files.

Illustrative manifest for two files:

```json
{
  "schema": "coden.artifact.bundle.v1",
  "task_id": "demo_1",
  "files": [
    {"path": "app.py", "sha256": "<64 lowercase hex digest of app.py>", "bytes": 42},
    {"path": "docs/README.md", "sha256": "<64 lowercase hex digest of README.md>", "bytes": 23}
  ]
}
```

The illustrative lengths and placeholder digests are **not valid evidence** until computed from the actual files. Hash the canonical UTF-8 JSON manifest using:

```python
import hashlib, json
manifest = json.load(open("manifest.json", encoding="utf-8"))
canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False).encode("utf-8")
manifest_sha256 = hashlib.sha256(canonical).hexdigest()
```

This manifest SHA must match the model/runtime report's `artifact_sha256`. For each output file the verifier independently reads the bytes, checks actual size and SHA-256, and rejects any missing or extra files.

## Operator invocation

On a trusted local machine in repository root:

```bash
python -m ai_factory.artifact_cli \
  --request /private/evidence/request.json \
  --report /private/evidence/report.json \
  --manifest /private/evidence/manifest.json \
  --root /private/output-bundle
```

- **Exit 0:** the files listed in the manifest match the actual local artifact directory; the stdout assessment contains `artifact_verified: true`. **No human approval is implied.**
- **Exit 2:** invalid, missing, tampered, oversized or unreadable evidence. No raw file contents, prompts or credentials are echoed.
- No networking, provider requests, external services, releases, PR merges or artifact modifications.

## Explicit safety and scale limits

- Synthetic-only; no production, citizen, identity, health, finance or government PII.
- Maximum **32 regular files**, **1 MiB per file**, **8 MiB total**, up to **64 directories** and a bounded nesting depth. These are prototype limits, not future production requirements.
- Manifest entries have strict sorted safe relative paths; `../`, absolute paths, hidden dotfiles, duplicate entries, path injection and symlinks are refused.
- File/manifest hashes are **not digital signatures**, provenance attestation, license approval or test-quality evidence. An agent controlling both manifest and contents can produce matching hashes for incorrect or malicious code.
- Verifying files on an operator-controlled local filesystem is **not a race-free snapshot** against concurrent hostile writes. Quiesce the worker, secure the directory, and pin immutable artifact storage before using these checks for a security boundary.
- Source code is never executed by the verifier. It does **not** run hidden tests or perform independent security scanning.
- Final results deliberately return `release_approved: false`, `acceptance_tests_verified: false`, `cryptographically_signed: false`, and `execution_authorized: false`.

## Next Codex integration milestone

1. Make the *existing synthetic project pilot* export a canonical output manifest and report metadata after completion; do not let the project code approve its own release.
2. Run the verifier **outside the candidate execution sandbox** against a stable copy of generated files and record results as independent evidence.
3. Add tests that deliberately alter one output, remove one output, introduce a symlink and change metadata between creation and verification.
4. Extend to a **small synthetic multi-file project**, with hidden acceptance tests and an independent SAST/license gate. These separate gates remain unimplemented in this PR.
5. Later connect official, authorized model runtimes (e.g. OpenHands) and a selected gateway, using the same contract; all paid calls and data-routing policies still require human authorization.
