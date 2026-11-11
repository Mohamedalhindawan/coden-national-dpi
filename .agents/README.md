# CODEN Codex project skills (mobile-first)

Codex CLI project skills live under `.agents/skills/<skill-name>/SKILL.md`. The six focused entry points in this directory are:
- test-driven-development
- systematic-debugging
- software-architecture
- code-review
- github-workflow
- security-review

These **do not install Codex CLI**, start an agent, supply model credentials, or grant GitHub access. They guide Codex once it is launched in this repository. Read root `AGENTS.md` first.

## Android / Termux verification

After installing compatible Codex CLI and cloning the repository in Termux:

```sh
cd coden-national-dpi
find .agents/skills -name SKILL.md -type f
python -m unittest discover -s tests -v
```

Codex CLI support on Android/Termux is version-dependent. Do not treat these files as proof that CLI or model routing works on the phone.

## Avoid duplication

Open PR #26 proposes an enterprise skills library under `skills/`; PR #50 proposes `ai-enterprise/skills/`. These six files are short **Codex discovery entry points**, not replacements for those broader libraries. Reconcile and link to accepted skills after those PRs are reviewed; do not merge overlapping catalogs blindly.

## Safety

Use synthetic demo data. No secrets in repository or prompts. No autonomous merge, deployment, paid API, or permission escalation. Report real test evidence and human approval requirements.
