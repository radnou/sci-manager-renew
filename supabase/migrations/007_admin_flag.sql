-- Add is_admin flag to subscriptions table for admin panel access
-- We use a simple approach: admin users are tracked via user_metadata in Supabase Auth
-- But for RLS bypass, we need a queryable flag in the database.

CREATE TABLE IF NOT EXISTS admins (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

ALTER TABLE admins ENABLE ROW LEVEL SECURITY;

-- Only admins can read the admins table
CREATE POLICY admins_self_read ON admins FOR SELECT
  USING (user_id = auth.uid());

-- No insert/update/delete via API — managed via service_role only
