-- 038_associes_rls_gerant_management.sql
-- Create SECURITY DEFINER function to check if the current user is a gérant of the SCI
CREATE OR REPLACE FUNCTION public.is_user_gerant_of_sci(target_sci_id uuid)
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.associes
    WHERE id_sci = target_sci_id AND user_id = auth.uid() AND role = 'gerant'
  );
$$;

-- Drop old policies
DROP POLICY IF EXISTS associes_member_insert ON associes;
DROP POLICY IF EXISTS associes_member_update ON associes;
DROP POLICY IF EXISTS associes_member_delete ON associes;

-- Recreate policies allowing a user to manage their own row, OR a gérant of the SCI to manage all rows in that SCI
CREATE POLICY associes_member_insert ON associes FOR INSERT
  WITH CHECK (user_id = auth.uid() OR public.is_user_gerant_of_sci(id_sci));

CREATE POLICY associes_member_update ON associes FOR UPDATE
  USING (user_id = auth.uid() OR public.is_user_gerant_of_sci(id_sci));

CREATE POLICY associes_member_delete ON associes FOR DELETE
  USING (user_id = auth.uid() OR public.is_user_gerant_of_sci(id_sci));
