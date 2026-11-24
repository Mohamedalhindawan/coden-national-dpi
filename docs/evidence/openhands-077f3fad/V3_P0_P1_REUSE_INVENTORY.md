# v3.0 P0/P1 reuse and integration inventory
Date: 2026-11-24
Status: inventory of existing candidates, not merge approval.
Baseline: PR #191 head d7164f3feb161c4f73451f87e99f87002eef9811. Roadmap decision: docs/CODEN_AI_FACTORY_V3_ADOPTION_DECISION.md. v1.0 frozen; full reconciliation pending.

| PR | Exact head | Existing candidate and prior tests | Presence in #191 baseline | Remaining work |
|---|---|---|---|---|
| #140 | a05708cf8cdd0a17eb610d7d413ee2b2c28eeb49 | Offline single-task worker/supervisor, 21 focused tests stated in PR, prototype run 44856695316 success | Both ai_factory/offline_worker.py and worker_supervisor.py absent (404) | Review before integration, test cross-store crash reconciliation and cancellation; not continuous or auto-retry |
| #148 | 56e2ccac37b850a45f75e31a425e7c83dc2318c8 | Independent three-file acceptance, prototype run 44858334203 success | ai_factory/openhands_multifile_review.py blob 7cc2b688c603ed24e49d860589ca1eabe657cf1c present | Exercise on real approved agent output, visible and withheld cases, no execution of agent-authored tests |
| #149 | ac25d97d5e0466f724c96f2ef64bae7d6f93639c | Operator-gated SDK bridge, mock SDK only, prototype 44859735130 success | ai_factory/openhands_sdk_operator.py blob 10c54ac30af3b0e20b6e9bfb438951f375f29cc7 present | Adapt only after reviewing RemoteWorkspace contract, actual verified runtime and explicit operator approval |
| #150 | f27e82740b187c513012476f69944f2518c43d43 | Free private Supabase control-plane migration, schema CI 44861239359 success | Migration 20261121032502_coden_factory_control_plane.sql and runbook absent (404) | Review live database evidence and schema before integration; no remote mutation or credential bridge authorized by this inventory |
| #151 | 786d63fefcb253b34ce2acf00bdc9608fcf837d0 | CPU inference trial 45211669944 success | ai_factory/free_cpu_receipt.py absent (404) | Reuse verified later Qwen3 evidence; compare receipt compatibility rather than rebuilding or blindly copying |

All five PRs remain Draft and unmerged as checked. Presence of individual files does not establish equality to the original branch or complete integration; compare exact blobs before any reuse. Prior workflow success is historical, not current integrated-system proof.
P0: preserve R2 and resolve synthetic envelope, actual build approval/license and candidate isolation, separate live-session approval, independent #148 acceptance. P1 (v3 sections 21–30, 123, 145, 151): reuse #140/#150 with explicit integration plan, idempotent task admission and lease ownership, cross-store recovery, persistent hosting, test bounded retries, timeout, cancellation, worker restart, duplicate side-effect prevention, backups and alerts. No continuous hosting or Supabase connection changes authorized by this record. No main merge, deployment or paid API.
