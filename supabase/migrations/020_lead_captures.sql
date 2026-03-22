-- Lead capture table for funnel tracking (SEO tools → email → conversion)
CREATE TABLE IF NOT EXISTS lead_captures (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'unknown',  -- simulateur-cerfa, generateur-quittance, landing, etc.
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    nurture_step INT DEFAULT 0,
    converted_to_user_id UUID REFERENCES auth.users(id),
    converted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for dedup and conversion tracking
CREATE INDEX IF NOT EXISTS idx_lead_captures_email ON lead_captures(email);
CREATE INDEX IF NOT EXISTS idx_lead_captures_source ON lead_captures(source);

-- Guarantee tracking on subscriptions
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS guarantee_expires_at TIMESTAMPTZ;
