# CODEN Security Incident Response — Draft SOP

**Status:** Unapproved template. **V4.0:** security and operations sections.

## Trigger and severity
Report suspected data exposure, secret leakage, account compromise, unauthorized access, malware, service disruption or unsafe agent actions. Assign severity only after triage; never assume a real production incident occurred.

## Procedure
1. **Intake:** capture report time, source, affected asset and reporter without copying secrets or citizen data into public issues.
2. **Contain:** notify authorized security owner; revoke or rotate exposed credentials only through approved channels.
3. **Preserve:** maintain access-controlled evidence, timeline and immutable references where feasible.
4. **Assess:** evaluate scope, legal notification obligations, affected data and third-party dependencies with qualified owners.
5. **Recover:** execute reviewed remediation, rollback and verification; require production approval.
6. **Review:** document root cause, lessons, preventive actions and owner.

## Mandatory controls
Do not place credentials, personal records, incident forensics or confidential details in public GitHub repositories. This document does not create an on-call team or monitoring system.
