-- 009_auth_activated_sessions.sql
-- Table anti-replay pour /activate endpoint (pay-first auth flow)

CREATE TABLE IF NOT EXISTS activated_sessions (
    session_id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    activated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_activated_sessions_activated_at ON activated_sessions(activated_at);

ALTER TABLE activated_sessions ENABLE ROW LEVEL SECURITY;
-- No user policies — only accessible via service_role
