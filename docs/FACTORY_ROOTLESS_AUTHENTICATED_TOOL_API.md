# CODEN AI Factory v1.0 — real authenticated OpenHands Bash API (operator-only)

**Status:** Draft PR #183, stacked on successful session-auth #182 and linked OpenHands/Qwen #181; no merge, no deployment, human review required. **P0 issue #162 stays open.** The approved master plan **v1.0** is unchanged.

## Tested outcome / acceptance scope

The existing actual signed source-built OpenHands server from upstream SHA `077f3fad6d31cd852be5c87176e0a93c3b446126` runs in an ephemeral Rootless Podman container. The same internal network contains a genuine, SHA-pinned Qwen2.5-Coder 0.5B model served by llama.cpp (the internal `ollama` alias is **not** an Ollama daemon). Neither container publishes a host port.

This step exercises the **real upstream built-in Bash tool API** through `POST /api/bash/execute_bash_command` as documented in upstream `openhands-agent-server/openhands/agent_server/bash_router.py` and `models.py`. The only allowed command is **operator-authored**, synthetically fixed and harmless:

```
printf CODEN_FACTORY_TOOL_EXECUTION_OK
```

This command has no network, filesystem writes, dependencies, credentials or arbitrary model-generated shell. The runner sends three HTTP requests from inside the OpenHands container using one-time `OH_SESSION_API_KEYS_0` authentication:

1. No key → expected HTTP **401**, must fail otherwise.
2. Incorrect key → expected HTTP **401**, must fail otherwise.
3. Correct one-time synthetic key → expected HTTP **200** plus a real BashOutput JSON with `exit_code=0` and exactly the expected synthetic stdout.

All requests and the response are confined to the sandbox; **raw response text, body, keys and other tool history are not uploaded**. Only strict review-only booleans and source/model identity hashes are allowed in the time-limited evidence artifact. The security contract in `ai_factory/factory_rootless_tool_api_proof.py` rejects unknown fields, missing/failed checks and any claims of auto-approval or model-generated commands.

The existing #182 proof is also rerun: pinned binary provenance/attestation and archived high/critical scoped scan, genuine Qwen inference connectivity, guest CPU/RAM/PID cgroups, read-only rootfs, capability drop, no new privileges, byte/inode-bounded temporary workspace, no unapproved environment keys, external IP/DNS TCP egress denied and independent teardown.

## Important NOT-YET-DONE boundary

A real OpenHands API executing a *prewritten operator command* is useful proof of the tool server, but **it is NOT a real official OpenHands SDK Conversation**, it is NOT the LLM deciding to call a tool, and it does not produce the independently verified three-file candidate. The tool endpoint executes only the literal source-controlled harmless command from this reviewable CI workflow.

Full transitive SDK/tool SBOM licensing review and operator-approved conversation lifecycle/watchdog, secure local model service authentication, identity-based network restrictions, comprehensive host/metadata egress audits and independent reviewer clearance all remain pending in #162. A successful API smoke test must not be described as autonomous coding ability.

**No human data, production mounts, GitHub tokens, paid provider, external API requests, release authorization or automatic merge.** The real SDK model/tool pilot remains **BLOCKED** pending remaining P0 review and explicit human operator sign-off.

## Evidence

CI: `.github/workflows/factory-rootless-authenticated-tool-api.yml`. Tests:

```bash
python -m unittest discover -s tests -p 'test_factory_rootless_tool_api.py' -v
```

Review the actual Actions run result and sanitized artifact. A unit-test PASS without a real container run is insufficient. Follow human review after independent verification.
