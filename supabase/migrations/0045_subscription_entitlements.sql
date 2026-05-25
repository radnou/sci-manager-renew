-- 004_subscription_entitlements.sql
-- Persist resolved plan entitlements snapshots for runtime enforcement.

alter table if exists subscriptions
  add column if not exists plan_key text not null default 'free',
  add column if not exists entitlements_version integer not null default 1,
  add column if not exists max_scis integer,
  add column if not exists max_biens integer,
  add column if not exists features jsonb not null default '{}'::jsonb,
  add column if not exists is_active boolean not null default false;

create index if not exists idx_subscriptions_plan_key on subscriptions (plan_key);
create index if not exists idx_subscriptions_is_active on subscriptions (is_active);
