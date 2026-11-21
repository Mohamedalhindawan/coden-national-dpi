# CODEN AI Factory — Supabase Free Control Plane v0.1

**Status:** Applied to existing connected Supabase project `coden-enterprise` in the Free organization; **metadata control-plane only**. PR #150 remains Draft and unmerged; no models, Docker worker, Edge Functions, paid service, queue consumer, cloud credentials or production deployments were enabled.

## Existing environment

- The actual organization plan is **Free / tier_free**, verified on 2026-11-21.
- The project is `coden-enterprise` in region `eu-central-1`, status `ACTIVE_HEALTHY`. No new Supabase project or branch was created.
- The existing `coden_internal` private schema **already contains** enterprise workstreams, requirements, tasks, RBAC and audit structures from seven previous migrations. It was not changed.
- `public` contains no application tables at this checkpoint. An empty `public` listing does **not** imply that the database as a whole is empty.

## Exactly what was applied

The migration `supabase/migrations/20261121032502_coden_factory_control_plane.sql` mirrors the actual applied Supabase migration version and creates a new, isolated `coden_factory` schema with:

| Table | Purpose | Default/guard |
| --- | --- | --- |
| `coden_factory.jobs` | Synthetic task metadata, exact repo and digest | `pending_review`; cost 0, provider/execution approvals false |
| `coden_factory.job_events` | Bounded, append-only audit records | One task reference and safe event kind |

Guards:
- Both tables have RLS enabled **and forced**. `anon` and `authenticated` have no usage or table privileges. No client-facing RLS policies are installed. The purpose is private, backend-only access through an operator-managed service role, **never** a frontend key.
- Constraints reject `estimated_cost_usd != 0`, `data_classification != synthetic`, `provider_approved=true`, `execution_authorized=true`; task IDs/digests and event kinds are bounded.
- No server-side scheduling, provider routing, HTTP dispatch, model execution, permissions escalation, log shipping, API key management or background worker was added.
- The two new tables are separate from the existing `coden_internal.tasks` enterprise records and the existing GitHub/SQLite `ai_factory/durable_queue.py`. This is **not** a second executable queue.

## Verified evidence (live remote PostgreSQL)

1. Migration `coden_factory_control_plane`: Supabase returned `success:true`; server migration history lists version `20261121032502`.
2. Read-only catalog checks: `jobs` and `job_events` both have RLS enabled and forced; `anon` and `authenticated` lack schema `USAGE` and table `SELECT`; `service_role` has backend `SELECT`.
3. Created one harmless metadata-only smoke record `FREE-CLOUD-SMOKE-20261121`, with one `created` event and cost 0. Status remains `pending_review`; execution authorization and provider approval both remain false. No model, executor or GitHub workflow was triggered by this record.
4. Remote SQL `DO` guard assertions independently attempted four invalid records: positive cost, true provider approval, true execution authorization and private classification. Every attempt was rejected by a database CHECK constraint; no invalid rows were created.
5. [RED CI #44860909264](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44860909264): intentionally failed because the required migration file did not exist.
6. [GREEN CI #44860962482](https://github.com/Mohamedalhindawan/coden-national-dpi/actions/runs/44860962482): **188 tests executed, 1 skipped, PASS; OpenAPI PASS**. The four new static tests validate private schema/guards. **Static CI alone is not the live database proof**; the verification above came from direct Supabase SQL checks.

## Security advisor results

Supabase's security advisor reports `rls_enabled_no_policy` at INFO severity for the two **new, intentionally backend-only** tables. This is a deliberate deny-by-default design and not a public exposure. It also flagged two pre-existing `coden_internal` tables; these were not altered. Supabase reported a separate **password leak protection disabled** warning in Auth; follow a separately approved Auth security hardening process before broad user onboarding, not an opportunistic change to production login settings.

## What still blocks a free real agent run

- There is **no live Supabase-to-GitHub Actions credentials bridge**; GitHub Actions cannot safely poll the private database without an operator-supplied limited secret or an audited, JWT-verified Edge Function.
- Existing CODEN factory worker/supervisor is still a **separate Draft PR #140** and not running persistently.
- OpenHands SDK's gated operator bridge is **Draft PR #149**, stacked on multi-file reviewer Draft PR #148. Their mocked SDK tests and real bubblewrap tests do **not** show successful genuine OpenHands/Ollama model generation.
- Running a local Ollama model on hosted GitHub Actions CPU may be possible for a very small, pinned model and short synthetic task; the public runner's CPU/RAM/network and job time limits, model distribution license, checkout trust boundaries and GitHub fair-use policy must be verified. No guarantee of a free always-on agent.
- Any **free-tier** cloud provider quota must be monitored. Zero-cost database constraints do not prevent all possible infrastructure billing outside the schema. Do not activate paid features or auto-billing.

## Next controlled experiment

1. Independently review PR #150's private migration and decide how to authenticate a GitHub worker without publishing a service-role token. Keep secrets off public PR workflows.
2. On a trusted branch, implement a **read-only metadata intake check** with a synthetic fixture and strict job ID allowlist; store results in independent GitHub CI. Start by proving zero provider cost and no side effects.
3. Test a real, free-model run (if a provider actually offers an authorized free tier) or a tiny CPU model within a constrained runner, with a single synthetic multi-file task. If not available, report `BLOCKED` rather than implying a live model run.
4. Admit a real worker only after independent security review, resource ceilings and human approval. Do not merge or deploy automatically.

**Decision:** Supabase Free is now a real, verified **control-plane metadata foundation**. It is **not** an autonomously running software factory.
