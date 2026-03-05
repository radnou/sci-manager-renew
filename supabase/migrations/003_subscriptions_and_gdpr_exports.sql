-- 003_subscriptions_and_gdpr_exports.sql
-- Persist Stripe subscription state and GDPR export metadata.

create table if not exists subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null unique,
  stripe_customer_id text,
  stripe_subscription_id text unique,
  stripe_price_id text,
  mode text not null default 'subscription' check (mode in ('subscription', 'payment')),
  status text not null default 'pending',
  current_period_end timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_subscriptions_user_id on subscriptions (user_id);
create index if not exists idx_subscriptions_status on subscriptions (status);

-- Reuse trigger helper from 001_init.sql.
drop trigger if exists trg_subscriptions_updated_at on subscriptions;
create trigger trg_subscriptions_updated_at
before update on subscriptions
for each row execute function set_updated_at();

alter table subscriptions enable row level security;

drop policy if exists subscriptions_owner_select on subscriptions;
create policy subscriptions_owner_select on subscriptions
for select
using (user_id = auth.uid());

drop policy if exists subscriptions_owner_insert on subscriptions;
create policy subscriptions_owner_insert on subscriptions
for insert
with check (user_id = auth.uid());

drop policy if exists subscriptions_owner_update on subscriptions;
create policy subscriptions_owner_update on subscriptions
for update
using (user_id = auth.uid())
with check (user_id = auth.uid());

drop policy if exists subscriptions_owner_delete on subscriptions;
create policy subscriptions_owner_delete on subscriptions
for delete
using (user_id = auth.uid());

create table if not exists gdpr_exports (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  file_path text not null unique,
  size_bytes bigint not null check (size_bytes > 0),
  expires_at timestamptz not null,
  created_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_gdpr_exports_user_id on gdpr_exports (user_id);
create index if not exists idx_gdpr_exports_expires_at on gdpr_exports (expires_at);

alter table gdpr_exports enable row level security;

drop policy if exists gdpr_exports_owner_select on gdpr_exports;
create policy gdpr_exports_owner_select on gdpr_exports
for select
using (user_id = auth.uid());

drop policy if exists gdpr_exports_owner_insert on gdpr_exports;
create policy gdpr_exports_owner_insert on gdpr_exports
for insert
with check (user_id = auth.uid());

drop policy if exists gdpr_exports_owner_delete on gdpr_exports;
create policy gdpr_exports_owner_delete on gdpr_exports
for delete
using (user_id = auth.uid());
