-- Migration 023: Create admin_mrr_snapshots table for MRR tracking
-- Used by mrr_snapshot_service.py to persist daily MRR snapshots

CREATE TABLE IF NOT EXISTS admin_mrr_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_date DATE NOT NULL,
    total_mrr NUMERIC(12, 2) NOT NULL DEFAULT 0,
    mrr_by_plan JSONB NOT NULL DEFAULT '{}'::jsonb,
    active_subscribers INTEGER NOT NULL DEFAULT 0,
    arpu NUMERIC(12, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT admin_mrr_snapshots_snapshot_date_unique UNIQUE (snapshot_date)
);

-- Index for date-range queries used by get_mrr_trend()
CREATE INDEX IF NOT EXISTS idx_admin_mrr_snapshots_date
    ON admin_mrr_snapshots (snapshot_date DESC);

-- No RLS needed: this table is only accessed via service_role client (admin endpoints)
