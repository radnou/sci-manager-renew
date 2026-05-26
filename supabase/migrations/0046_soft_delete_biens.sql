-- 0046_soft_delete_biens.sql
-- Add soft delete timestamp to biens with 30-day grace period support.

alter table if exists biens
  add column if not exists deleted_at timestamptz null;

create index if not exists idx_biens_deleted_at on biens (deleted_at);
