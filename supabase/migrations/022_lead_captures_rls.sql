-- Enable RLS on lead_captures (was missing — only service role should access)
ALTER TABLE IF EXISTS lead_captures ENABLE ROW LEVEL SECURITY;

-- Service role can do everything
CREATE POLICY "service_role_all" ON lead_captures
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- No access for authenticated users or anon — leads are backend-only
