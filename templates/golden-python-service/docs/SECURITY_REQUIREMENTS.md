# Security requirements — prototype only

- No production or personal data; use synthetic fixtures only.
- No secrets in repo, CI, issues, PR comments or model prompts.
- No outbound network, cloud inference, database writes or privileged operations in this starter.
- Changes require independent review and failing-first regression tests.
- CI uses commit-pinned GitHub actions and read-only token permissions.
- Select a valid license and verified maintainers **before** making a new reusable public repository. No license is bundled here by default.
- Plan SBOM, dependency update policy, secrets scanning, artifact provenance and rollback if expanding beyond stdlib.
- Generated repository tests do not imply authorization to process real beneficiaries, issue credentials, deploy or change governmental systems.
