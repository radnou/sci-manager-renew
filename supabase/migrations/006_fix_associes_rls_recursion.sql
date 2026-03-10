-- Fix infinite recursion in associes RLS policies
-- The old policies did EXISTS (SELECT 1 FROM associes WHERE ...) which triggers
-- the same RLS policy again, causing infinite recursion.
-- Fix: use direct user_id = auth.uid() check instead.

DROP POLICY IF EXISTS associes_member_select ON associes;
DROP POLICY IF EXISTS associes_member_update ON associes;
DROP POLICY IF EXISTS associes_member_delete ON associes;
DROP POLICY IF EXISTS associes_member_insert ON associes;

CREATE POLICY associes_member_select ON associes FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY associes_member_insert ON associes FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY associes_member_update ON associes FOR UPDATE
  USING (user_id = auth.uid());

CREATE POLICY associes_member_delete ON associes FOR DELETE
  USING (user_id = auth.uid());
