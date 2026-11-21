-- CODEN AI Factory Phase 0: private zero-cost task metadata and audit log.
-- Never alter the existing coden_internal workstreams/tasks/requirements.
-- This migration does not install a runtime, queue consumer or model.
-- Run against the existing Supabase Free project only after code review.
create schema if not exists coden_factory;

-- Private schema intentionally absent from the Data API's exposed schemas.
revoke all on schema coden_factory from public, anon, authenticated;
grant usage on schema coden_factory to service_role;

create table if not exists coden_factory.jobs (
  task_id text primary key
    check (task_id ~ '^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$'),
  title text not null
    check (char_length(title) between 1 and 160),
  repo_full_name text not null default 'Mohamedalhindawan/coden-national-dpi'
    check (repo_full_name = 'Mohamedalhindawan/coden-national-dpi'),
  task_sha256 text not null
    check (task_sha256 ~ '^[0-9a-f]{64}$'),
  source_commit text
    check (source_commit is null or source_commit ~ '^[0-9a-f]{40}$'),
  data_classification text not null default 'synthetic'
    check (data_classification = 'synthetic'),
  estimated_cost_usd numeric(10,4) not null default 0
    check (estimated_cost_usd = 0),
  provider_approved boolean not null default false
    check (provider_approved = false),
  execution_authorized boolean not null default false
    check (execution_authorized = false),
  status text not null default 'pending_review'
    check (status in ('pending_review', 'blocked', 'needs_review',
                     'failed', 'completed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists coden_factory.job_events (
  event_id bigint generated always as identity primary key,
  task_id text not null references coden_factory.jobs(task_id),
  event_kind text not null
    check (event_kind in ('created', 'checked', 'blocked', 'qa_recorded',
                         'review_required')),
  event_message text not null
    check (char_length(event_message) between 1 and 500),
  occurred_at timestamptz not null default now()
);

create index if not exists idx_coden_factory_jobs_status_created
  on coden_factory.jobs(status, created_at);

create index if not exists idx_coden_factory_events_task_time
  on coden_factory.job_events(task_id, occurred_at);

-- No direct browser/anonymous/authenticated client privileges.
revoke all on coden_factory.jobs from public, anon, authenticated;
revoke all on coden_factory.job_events from public, anon, authenticated;
alter table coden_factory.jobs enable row level security;
alter table coden_factory.jobs force row level security;
alter table coden_factory.job_events enable row level security;
alter table coden_factory.job_events force row level security;

-- An operator-managed backend may later access via a separately protected
-- service-role connection. Never expose this key in GitHub or web clients.
grant select, insert, update on coden_factory.jobs to service_role;
grant select, insert on coden_factory.job_events to service_role;
grant usage, select on sequence coden_factory.job_events_event_id_seq
  to service_role;

comment on schema coden_factory is
  'CODEN AI Factory Phase 0 metadata, isolated from coden_internal; no runnable queue';
comment on table coden_factory.jobs is
  'Synthetic-only zero-spend proposals; execution and provider approval are disabled';
comment on table coden_factory.job_events is
  'Operator-only event trail; agent-created tests and runtime results are not trusted';
