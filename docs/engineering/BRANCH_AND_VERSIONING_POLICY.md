# Branch and Versioning Policy

**Status:** Proposed repository policy; human approval required before enforcement.

## Branch model
- `main`: reviewed, releasable baseline; no routine direct commits.
- `feat/<short-name>`: bounded feature work.
- `fix/<short-name>`: defect or security correction.
- `docs/<short-name>`: documentation-only changes.
- `chore/<short-name>`: repository maintenance and tooling.

Branches should be short-lived and scoped to one issue or closely related change. Do not reuse stale branches without comparing them to current `main`.

## Pull request rules
1. Link an issue and state acceptance criteria.
2. Keep the diff focused; split unrelated code and documentation changes.
3. Require the applicable CI checks to pass.
4. Require human review before merge; authors must not self-approve their own consequential changes.
5. Resolve review comments and record any accepted risk.
6. Do not merge or deploy automatically as a result of an agent completing a task.
7. Use synthetic/public data only in the current prototype.
8. Do not add credentials, secrets, or personal/citizen data to Git.

## Merge strategy
Prefer squash merge for a bounded feature or fix, unless preserving a meaningful commit series is necessary. Keep the PR title and final commit message conventional and descriptive.

## Semantic versioning
For published CODEN software components using SemVer:
- **MAJOR:** incompatible public API or contract change.
- **MINOR:** backward-compatible functionality.
- **PATCH:** backward-compatible bug or security fix.

Before a component has a stable public API, use `0.y.z` and document breaking changes. Do not apply a software version to documents or data registries unless their own versioning policy defines it.

## Release evidence
Every release must record:
- component and version;
- source commit and PR;
- CI run and test evidence;
- dependency/SBOM and security review where applicable;
- migration and rollback notes;
- accountable human release approval.

## Enforcement note
This file is a proposed policy. Branch protection, required reviewers, required status checks, signed commits, and release permissions must be configured separately in GitHub settings by an authorized human.

## Recommended GitHub enforcement for `main` (proposal only)

These settings are recommended for an authorized repository administrator to review and apply:

1. Require pull requests before changes reach `main`; block routine direct pushes.
2. Require at least one approval from a human reviewer who is not the PR author.
3. Require approval of the latest push where GitHub offers that option.
4. Require conversation resolution before merge.
5. Require the `Prototype checks / contract-tests` status check after confirming its exact check name in the Actions UI.
6. Require the branch to be up to date before merging, if this does not create excessive merge friction.
7. Block force pushes and branch deletion for `main`.
8. Do not enable automatic merge for AI-generated changes by default.
9. For changes to identity, authorization, payments, benefit eligibility, sensitive data, production infrastructure, or release controls, require a second independent specialist review and explicit accountable-owner approval.
10. Review administrator/bypass permissions and keep them limited to named maintainers.

### Observed settings visibility (2026-11-07)

- The GitHub repository rulesets endpoint returned an empty list.
- The connected GitHub integration returned HTTP 403 for the classic branch-protection read endpoint; therefore the actual classic branch-protection state could not be verified here.
- No branch-protection or repository settings were changed by this PR.

**Do not mark branch protection as enabled until an authorized administrator verifies the settings in GitHub and records a screenshot/export or equivalent audit evidence.**
