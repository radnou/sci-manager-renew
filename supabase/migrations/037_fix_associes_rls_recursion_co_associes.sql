-- Fix infinite recursion in associes SELECT policy and allow co-associés to view each other
DROP POLICY IF EXISTS associes_member_select ON associes;

CREATE OR REPLACE FUNCTION public.get_user_sci_ids()
RETURNS SETOF uuid
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT id_sci FROM public.associes WHERE user_id = auth.uid();
$$;

CREATE POLICY associes_member_select ON associes FOR SELECT
  USING (id_sci IN (SELECT public.get_user_sci_ids()));
