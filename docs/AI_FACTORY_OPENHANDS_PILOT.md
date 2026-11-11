# CODEN AI Factory — OpenHands first upstream pilot

**Status:** preparation only; OpenHands is **not installed or running** in CODEN. This branch does not change production, enable paid services, or execute third-party code.

## Why this pilot
Evaluate the existing [OpenHands](https://github.com/All-Hands-AI/OpenHands) agent runtime before writing our own. Compare a single bounded coding task against CODEN's existing synthetic-only intake and GitHub Actions quality gates.

## Prerequisites (human-operated)
- Laptop with an isolated Docker-compatible environment and sufficient free RAM/disk.
- Disposable repository containing **synthetic data only**.
- A separately provisioned model endpoint; verify pricing and approve any spend **before** enabling it.
- A dedicated GitHub identity with **no access to CODEN production repositories**. Prefer no GitHub credentials during the first trial.
- Read the current OpenHands upstream installation guide and release notes; pin a reviewed release and image digest. Never run arbitrary install scripts or unpinned images.

## Execution gates
1. **Review:** confirm current upstream license, release, image digest, known security advisories, and runtime prerequisites.
2. **Isolation:** use a disposable VM or isolated machine, not a privileged container sharing the laptop's Docker socket and home directory. Review any required Docker socket access before proceeding.
3. **Secrets:** no personal GitHub token, production API key, citizen data, or access to the CODEN repository.
4. **Task:** in a throwaway repository, ask the agent to add one small function and tests. Record baseline tests and final tests.
5. **Evidence:** collect commit SHA, changed paths, test logs, runtime permissions, token/cost metrics, and failure modes. Do not claim completion without logs.
6. **Review:** a human checks the diff and determines whether a **separate draft PR** is warranted. No automatic merge or deployment.

## Pilot scorecard
| Gate | Pass criteria |
| --- | --- |
| Reproducibility | Pinned upstream version and reproducible installation |
| Isolation | No production credentials, no sensitive host mounts |
| Task execution | Small synthetic change with reviewable diff |
| Tests | Baseline and post-change test logs captured |
| Security | No unauthorized network/filesystem/GitHub actions |
| Cost | Approved ceiling and actual usage documented |
| Human approval | No merge/deploy or write to CODEN without approval |

## Next engineering step
After the laptop OS and hardware are known, produce an OS-specific pinned deployment plan **in a separate PR**, with a reviewed threat model. This preparation does not require adding OpenHands source code to CODEN or forking the upstream repository.
