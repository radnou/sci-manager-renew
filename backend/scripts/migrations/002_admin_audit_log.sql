CREATE TABLE IF NOT EXISTS admin_audit_log (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    admin_action text NOT NULL,
    target_user_id text,
    details jsonb DEFAULT '{}',
    ip_address text,
    created_at timestamptz DEFAULT now()
);
CREATE INDEX idx_audit_log_created ON admin_audit_log(created_at DESC);
CREATE INDEX idx_audit_log_action ON admin_audit_log(admin_action);
