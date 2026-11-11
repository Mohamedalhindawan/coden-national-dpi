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


## Specialist agents (proposed)

Four specialist definitions live under `.codex/agents/`: `architect.toml`, `developer.toml`, `qa.toml`, and `security.toml`. They are instruction profiles, **not running processes**. Their recognition and multi-agent availability must be checked against the actual installed Codex CLI version and configuration.

For a safe first mobile experiment, use a **single agent** with the six skills. Only enable multi-agent workflows after confirming the installed CLI supports this agent-definition format and observing a read-only test. Do not run parallel agents by default on a phone.

### Local validation after cloning

```sh
python - <<'PY'
import pathlib, tomllib
paths = sorted(pathlib.Path('.codex/agents').glob('*.toml'))
assert len(paths) == 4, paths
for path in paths:
    with path.open('rb') as handle:
        agent = tomllib.load(handle)
    assert agent['name'] == path.stem
    assert agent['description'] and agent['developer_instructions']
print('Validated 4 agent TOML files')
PY
```

This verifies TOML structure only, **not** Codex CLI compatibility, actual agent invocation, or model access. Requires Python 3.11+.
