# CODEN Golden Python Service — experimental starter

**Status:** Proposed *self-contained* template directory, NOT yet a standalone GitHub template repository or a deployed service.

This minimal starter demonstrates a Python 3.12 synthetic-only status summary with strict input validation and **zero third-party dependencies**.

## Validate a generated copy

```bash
python -m unittest discover -s tests -v
python -c "from coden_service.summary import summarize; print(summarize([]))"
```

Six starter tests cover valid summaries, duplicate-ID rejection and non-synthetic input denial. The starter includes a `.gitignore` to reduce accidental commits of local credentials and Python build artifacts; this is not a replacement for secret scanning. The CODEN root test suite also checks that a clean copy runs outside this repository. An optional workflow at `.github/workflows/ci.yml` becomes active only **after this directory is copied to a repository root**; GitHub does not run a workflow nested inside `templates/` in the parent CODEN repo.

## Candidate generation procedure (not performed)

1. Obtain approval for repository name, visibility, owner, license and code owners.
2. Copy this template's contents into the root of a **new, clean and trusted repository**. Do not copy production secrets or unrelated project history.
3. Run tests locally and in its own fresh GitHub Actions run.
4. If appropriate, use GitHub Settings → General → Template repository on the new repo. This is **not** the same as ChatGPT's document Template Creator.
5. Add exact project spec, acceptance tests, independent security review and any necessary product profiles before deploying.

**Adopt-first:** do not bundle FastAPI, Next.js, Flutter, Docker, model gateways or authentication libraries unless the specific generated project actually needs them; create separate reviewed profiles rather than a single oversized starter.

Related CODEN work: [Issue #143](https://github.com/Mohamedalhindawan/coden-national-dpi/issues/143), [RAG #123](https://github.com/Mohamedalhindawan/coden-national-dpi/issues/123).
