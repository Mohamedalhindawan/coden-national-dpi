## Summary

<!-- One short paragraph: what changed and why. -->

Closes #

## Scope and data

- [ ] One small task; unrelated changes are excluded.
- [ ] Synthetic or demo data only; no real citizen, beneficiary, identity, financial, or health data.
- [ ] No new dependency, paid service, or hosting unless explained below.

## Tests actually run

<!-- Exact commands and observed outcomes. Write "not run" plus the reason if a check was skipped. -->

| Command | Result |
|---|---|
| `python -m unittest discover -s tests -v` | |
| `python -m openapi_spec_validator api/openapi.yaml` | |

## Security and privacy

- [ ] No secrets, tokens, passwords, private keys, or personal data in code, logs, or screenshots.
- [ ] User-provided text is rendered as text, not HTML.
- [ ] No identity, payment, eligibility, or production behaviour changed without approval.
- [ ] Workflow permissions remain read-only unless justified.

## Documentation

- [ ] README or docs updated if behaviour, setup, or limitations changed.
- [ ] Known limitations and the next step are stated below.

## Human approval

Required before merge. The agent may prepare this change but must not merge it.

- [ ] A human has reviewed the diff, test evidence, and security notes.
- [ ] High-impact changes (identity, payments, eligibility, security, production) have explicit owner approval.
