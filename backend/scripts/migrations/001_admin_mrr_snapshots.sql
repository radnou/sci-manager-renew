CREATE TABLE IF NOT EXISTS admin_mrr_snapshots (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    snapshot_date date NOT NULL UNIQUE,
    total_mrr numeric(10,2) NOT NULL DEFAULT 0,
    mrr_by_plan jsonb NOT NULL DEFAULT '{}',
    active_subscribers integer NOT NULL DEFAULT 0,
    arpu numeric(10,2) NOT NULL DEFAULT 0,
    created_at timestamptz DEFAULT now()
);
CREATE INDEX idx_mrr_snapshots_date ON admin_mrr_snapshots(snapshot_date DESC);
