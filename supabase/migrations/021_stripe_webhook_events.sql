-- Stripe webhook idempotency table
-- Stores processed event IDs to prevent duplicate processing (at-least-once delivery)

CREATE TABLE IF NOT EXISTS stripe_webhook_events (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast lookups by event_id (already UNIQUE, but explicit for clarity)
CREATE INDEX IF NOT EXISTS idx_stripe_webhook_events_event_id ON stripe_webhook_events(event_id);

-- Auto-cleanup: events older than 90 days can be purged (optional cron)
-- This keeps the table small while maintaining sufficient dedup window.
COMMENT ON TABLE stripe_webhook_events IS 'Idempotency store for Stripe webhook events. Safe to prune rows older than 90 days.';

-- No RLS needed: only accessed via service_role client from backend
ALTER TABLE stripe_webhook_events ENABLE ROW LEVEL SECURITY;

-- Service role has full access (no user-facing policies needed)
CREATE POLICY "service_role_full_access" ON stripe_webhook_events
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
