# CODEN AI Factory — GitHub Adopt-First Research Catalog

**Research date:** 2026-11-21  
**Status:** research candidates only; NOT installed, verified or approved for CODEN.  
**Origin:** CODEN GitHub adopt-first research from the owner's planning conversation.  
**Core intent:** make the CODEN AI Factory resilient to Codex quota/context exhaustion, modular across models and agent runtimes, and continuously improvable with measurable review gates.

**Priority definition:** P0 = first evaluation (not approval); P1 = compare/pilot if gap or overlap warrants; P2 = defer until justified. Priorities are recommendations, not evidence of security/legal approval.

## Architecture decision questions

1. Evaluate **OpenHands Agent Canvas + OpenHands SDK** for coding-agent runtime; also compare Hermes Agent, OpenCode and existing Codex.
2. Pilot **Hermes Agent** and **Hermes Self-Evolution** for bounded learning, skills and CAIE; do not allow uncontrolled self-modification.
3. Compare **OmniRoute, LiteLLM, Bifrost** as alternatives and select one primary model gateway; never assume gateways bypass official provider quotas or terms.
4. Use a durable queue, checkpoints and workers; benchmark existing PostgreSQL approach against **Hatchet/Temporal** before introducing another service.
5. Test targeted repo understanding with **Serena, ast-grep**, and existing code-index workflows.
6. Verify engineering quality with **Harbor**, independently held-out project tests, CI and code/security review.
7. Reuse the existing PR chains **#116 → #118 → #124 → #126**, and review **#117 → #125** independently; don't reimplement completed work.

## Full 105-repository candidate registry

The GitHub URLs below are upstream candidates. Verify each repository, current upstream revision, license, supply-chain profile, maintenance and deployability before adopting.

### Coding agents & runtimes (14)

| Project | Official GitHub candidate | Initial evaluation priority |
|---|---|---|
| OpenHands | [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands) | P0 |
| OpenHands Software Agent SDK | [OpenHands/software-agent-sdk](https://github.com/OpenHands/software-agent-sdk) | P0 |
| Hermes Agent | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | P0 |
| Hermes Self-Evolution | [NousResearch/hermes-agent-self-evolution](https://github.com/NousResearch/hermes-agent-self-evolution) | P1 |
| OpenCode | [anomalyco/opencode](https://github.com/anomalyco/opencode) | P0 |
| Codex | [openai/codex](https://github.com/openai/codex) | P0 |
| Cline | [cline/cline](https://github.com/cline/cline) | P1 |
| Roo Code | [RooCodeInc/Roo-Code](https://github.com/RooCodeInc/Roo-Code) | P1 |
| Aider | [Aider-AI/aider](https://github.com/Aider-AI/aider) | P1 |
| mini-SWE-agent | [SWE-agent/mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) | P0 |
| SWE-agent | [SWE-agent/SWE-agent](https://github.com/SWE-agent/SWE-agent) | P2 |
| Gemini CLI | [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) | P1 |
| Goose | [block/goose](https://github.com/block/goose) | P1 |
| Pi mono | [badlogic/pi-mono](https://github.com/badlogic/pi-mono) | P1 |

### Multi-agent frameworks (8)

| Project | Official GitHub candidate | Initial evaluation priority |
|---|---|---|
| OpenAI Agents SDK | [openai/openai-agents-python](https://github.com/openai/openai-agents-python) | P0 |
| LangGraph | [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | P0 |
| Microsoft Agent Framework | [microsoft/agent-framework](https://github.com/microsoft/agent-framework) | P1 |
| Google ADK | [google/adk-python](https://github.com/google/adk-python) | P1 |
| CrewAI | [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | P1 |
| Mastra | [mastra-ai/mastra](https://github.com/mastra-ai/mastra) | P1 |
| Pydantic AI | [pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) | P1 |
| Agent Orchestrator | [OrchestratorInc/agent-orchestrator](https://github.com/OrchestratorInc/agent-orchestrator) | P1 |

### Durable workflows & tasks (8)

| Project | Official GitHub candidate | Initial evaluation priority |
|---|---|---|
| Temporal | [temporalio/temporal](https://github.com/temporalio/temporal) | P1 |
| Hatchet | [hatchet-dev/hatchet](https://github.com/hatchet-dev/hatchet) | P0 |
| Restate | [restatedev/restate](https://github.com/restatedev/restate) | P1 |
| Trigger.dev | [triggerdotdev/trigger.dev](https://github.com/triggerdotdev/trigger.dev) | P1 |
| Inngest | [inngest/inngest](https://github.com/inngest/inngest) | P1 |
| Prefect | [PrefectHQ/prefect](https://github.com/PrefectHQ/prefect) | P1 |
| Kestra | [kestra-io/kestra](https://github.com/kestra-io/kestra) | P1 |
| n8n | [n8n-io/n8n](https://github.com/n8n-io/n8n) | P1 |

### Model gateways (5)

| Project | Official GitHub candidate | Initial evaluation priority |
|---|---|---|
| OmniRoute | [cheaper-inference/OmniRoute](https://github.com/cheaper-inference/OmniRoute) | P0 |
| LiteLLM | [BerriAI/litellm](https://github.com/BerriAI/litellm) | P0 |
| Bifrost | [maximhq/bifrost](https://github.com/maximhq/bifrost) | P0 |
| Portkey AI Gateway | [Portkey-AI/gateway](https://github.com/Portkey-AI/gateway) | P1 |
| New API | [QuantumNous/new-api](https://github.com/QuantumNous/new-api) | P1 |

### Local inference & serving (6)

| Project | Official GitHub candidate | Initial evaluation priority |
|---|---|---|
| llama.cpp | [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | P0 |
| Ollama | [ollama/ollama](https://github.com/ollama/ollama) | P0 |
| vLLM | [vllm-project/vllm](https://github.com/vllm-project/vllm) | P1 |
| SGLang | [sgl-project/sglang](https://github.com/sgl-project/sglang) | P1 |
| LMDeploy | [InternLM/lmdeploy](https://github.com/InternLM/lmdeploy) | P2 |
| vLLM Production Stack | [vllm-project/production-stack](https://github.com/vllm-project/production-stack) | P2 |

### Repository intelligence & MCP (10)

| Project | Official GitHub candidate | Initial evaluation priority |
|---|---|---|
| Serena | [oraios/serena](https://github.com/oraios/serena) | P0 |
| ast-grep | [ast-grep/ast-grep](https://github.com/ast-grep/ast-grep) | P0 |
| GitHub MCP Server | [github/github-mcp-server](https://github.com/github/github-mcp-server) | P0 |
| Context7 | [upstash/context7](https://github.com/upstash/context7) | P1 |
| Playwright MCP | [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | P0 |
| Repomix | [yamadashy/repomix](https://github.com/yamadashy/repomix) | P1 |
| Tree-sitter | [tree-sitter/tree-sitter](https://github.com/tree-sitter/tree-sitter) | P1 |
| FastMCP | [PrefectHQ/fastmcp](https://github.com/PrefectHQ/fastmcp) | P1 |
| MCP Servers | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | P1 |
| CodeGraphContext | [CodeGraphContext/CodeGraphContext](https://github.com/CodeGraphContext/CodeGraphContext) | P1 |

### Skills & specification engineering (10)

| Project | Official GitHub candidate | Initial evaluation priority |
|---|---|---|
| OpenAI Skills | [openai/skills](https://github.com/openai/skills) | P0 |
| Anthropic Skills | [anthropics/skills](https://github.com/anthropics/skills) | P1 |
| Superpowers | [obra/superpowers](https://github.com/obra/superpowers) | P0 |
| Spec Kit | [github/spec-kit](https://github.com/github/spec-kit) | P0 |
| OpenSpec | [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) | P1 |
| BMAD Method | [bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | P1 |
| Awesome Copilot | [github/awesome-copilot](https://github.com/github/awesome-copilot) | P1 |
| Vercel Agent Skills | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | P1 |
| Agent Skills Standard | [agentskills/agentskills](https://github.com/agentskills/agentskills) | P1 |
| cc-sdd | [gotalab/cc-sdd](https://github.com/gotalab/cc-sdd) | P1 |

### Memory & retrieval (8)

| Project | Official GitHub candidate | Initial evaluation priority |
|---|---|---|
| Mem0 | [mem0ai/mem0](https://github.com/mem0ai/mem0) | P1 |
| Letta | [letta-ai/letta](https://github.com/letta-ai/letta) | P1 |
| Graphiti | [getzep/graphiti](https://github.com/getzep/graphiti) | P1 |
| Cognee | [topoteretes/cognee](https://github.com/topoteretes/cognee) | P1 |
| pgvector | [pgvector/pgvector](https://github.com/pgvector/pgvector) | P0 |
| Qdrant | [qdrant/qdrant](https://github.com/qdrant/qdrant) | P2 |
| LlamaIndex | [run-llama/llama_index](https://github.com/run-llama/llama_index) | P1 |
| Haystack | [deepset-ai/haystack](https://github.com/deepset-ai/haystack) | P1 |

### Evaluations & tests (7)

| Project | Official GitHub candidate | Initial evaluation priority |
|---|---|---|
| Harbor | [harbor-framework/harbor](https://github.com/harbor-framework/harbor) | P0 |
| Terminal-Bench | [harbor-framework/terminal-bench](https://github.com/harbor-framework/terminal-bench) | P0 |
| SWE-bench Pro | [scaleapi/SWE-bench_Pro-os](https://github.com/scaleapi/SWE-bench_Pro-os) | P1 |
| SWE-bench | [swe-bench/SWE-bench](https://github.com/swe-bench/SWE-bench) | P1 |
| Inspect AI | [UKGovernmentBEIS/inspect_ai](https://github.com/UKGovernmentBEIS/inspect_ai) | P1 |
| promptfoo | [promptfoo/promptfoo](https://github.com/promptfoo/promptfoo) | P0 |
| DeepEval | [confident-ai/deepeval](https://github.com/confident-ai/deepeval) | P1 |

### Security, sandbox & supply chain (14)

| Project | Official GitHub candidate | Initial evaluation priority |
|---|---|---|
| OPA | [open-policy-agent/opa](https://github.com/open-policy-agent/opa) | P0 |
| OpenBao | [openbao/openbao](https://github.com/openbao/openbao) | P1 |
| Gitleaks | [gitleaks/gitleaks](https://github.com/gitleaks/gitleaks) | P0 |
| Semgrep | [semgrep/semgrep](https://github.com/semgrep/semgrep) | P0 |
| Trivy | [aquasecurity/trivy](https://github.com/aquasecurity/trivy) | P0 |
| OSV-Scanner | [google/osv-scanner](https://github.com/google/osv-scanner) | P0 |
| OpenSSF Scorecard | [ossf/scorecard](https://github.com/ossf/scorecard) | P1 |
| Syft | [anchore/syft](https://github.com/anchore/syft) | P0 |
| Cosign | [sigstore/cosign](https://github.com/sigstore/cosign) | P1 |
| bubblewrap | [containers/bubblewrap](https://github.com/containers/bubblewrap) | P0 |
| gVisor | [google/gvisor](https://github.com/google/gvisor) | P2 |
| Firecracker | [firecracker-microvm/firecracker](https://github.com/firecracker-microvm/firecracker) | P2 |
| E2B | [e2b-dev/E2B](https://github.com/e2b-dev/E2B) | P1 |
| Daytona | [daytonaio/daytona](https://github.com/daytonaio/daytona) | P1 |

### Observability & FinOps (8)

| Project | Official GitHub candidate | Initial evaluation priority |
|---|---|---|
| Langfuse | [langfuse/langfuse](https://github.com/langfuse/langfuse) | P0 |
| Phoenix | [Arize-ai/phoenix](https://github.com/Arize-ai/phoenix) | P1 |
| LangWatch | [langwatch/langwatch](https://github.com/langwatch/langwatch) | P1 |
| Helicone | [Helicone/helicone](https://github.com/Helicone/helicone) | P1 |
| OpenLIT | [openlit/openlit](https://github.com/openlit/openlit) | P1 |
| OpenTelemetry Collector | [open-telemetry/opentelemetry-collector](https://github.com/open-telemetry/opentelemetry-collector) | P0 |
| Grafana | [grafana/grafana](https://github.com/grafana/grafana) | P0 |
| Prometheus | [prometheus/prometheus](https://github.com/prometheus/prometheus) | P0 |

### Enterprise systems (later where needed) (7)

| Project | Official GitHub candidate | Initial evaluation priority |
|---|---|---|
| ERPNext | [frappe/erpnext](https://github.com/frappe/erpnext) | P2 |
| Plane | [makeplane/plane](https://github.com/makeplane/plane) | P1 |
| BookStack | [BookStackApp/BookStack](https://github.com/BookStackApp/BookStack) | P1 |
| Keycloak | [keycloak/keycloak](https://github.com/keycloak/keycloak) | P1 |
| Zammad | [zammad/zammad](https://github.com/zammad/zammad) | P2 |
| Metabase | [metabase/metabase](https://github.com/metabase/metabase) | P2 |
| Backstage | [backstage/backstage](https://github.com/backstage/backstage) | P2 |

## Acceptance and security gates

- Reconcile existing CODEN inventory and PR dependency graph; do not install all 105 tools.
- Identify `Adopt / Integrate / Customize / Trial / Hold / Reject` for each candidate, documenting *why*, overlap and exact upstream SHA/version.
- Verify licenses including AGPL and source-available/commercial restrictions, dependency provenance, CVEs, maintenance, and provider authentication terms.
- Never send citizen, identity or private data to unapproved upstreams; no secrets in logs; sandbox untrusted code.
- Require reproducible, task-level before/after benchmarks for quality, duration, token use, cost, and resilience.
- Demonstrate a **bounded** end-to-end coding task with real tests and PR, plus persisted checkpoint and recovery from mocked quota exhaustion.
- Restrict autonomous changes to reviewed branches; no merge, production deploy, spend or authorization change without human approval.
- Submit concise evidence on achieved vs blocked. Avoid undocumented global installs.

**Important:** The original research includes short usage descriptions; this registry preserves all 105 candidate names, upstream URLs, and evaluation priorities in an implementation-friendly format. The working source stays in the ChatGPT conversation artifact.
