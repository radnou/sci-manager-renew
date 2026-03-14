-- 011: Audit fixes — C10, C11, C17, V22, C12, C13
-- Applied: 2026-03-14

-- =============================================================================
-- C11 — Fix UNIQUE constraint on loyers (NULL id_locataire bypass)
-- Replace single UNIQUE(id_bien, id_locataire, date_loyer) with two partial
-- unique indexes that properly handle NULL id_locataire.
-- =============================================================================

ALTER TABLE loyers DROP CONSTRAINT IF EXISTS loyers_id_bien_id_locataire_date_loyer_key;

CREATE UNIQUE INDEX IF NOT EXISTS uq_loyers_bien_date_no_locataire
  ON loyers (id_bien, date_loyer)
  WHERE id_locataire IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_loyers_bien_locataire_date
  ON loyers (id_bien, id_locataire, date_loyer)
  WHERE id_locataire IS NOT NULL;

-- =============================================================================
-- C17 — Fix RLS on associes: allow seeing co-associés of own SCIs
-- Create a SECURITY DEFINER function to break the recursion cycle.
-- =============================================================================

CREATE OR REPLACE FUNCTION get_user_sci_ids()
RETURNS SETOF uuid
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT id_sci FROM associes WHERE user_id = auth.uid();
$$;

-- Drop old restrictive policy and replace with one using the helper function
DROP POLICY IF EXISTS associes_member_select ON associes;

CREATE POLICY associes_member_select ON associes FOR SELECT
  USING (id_sci IN (SELECT get_user_sci_ids()));

-- =============================================================================
-- V22 — Add missing UPDATE policy on documents_bien (gérant only)
-- =============================================================================

CREATE POLICY documents_bien_gerant_update ON documents_bien FOR UPDATE
USING (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = documents_bien.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
)
WITH CHECK (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = documents_bien.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
);

-- =============================================================================
-- C10 — Parts sociales: add nb_parts (integer) alongside percentage
-- Add nb_parts_total to sci, nb_parts to associes.
-- Keep existing 'part' (percentage) as derived/display field.
-- =============================================================================

ALTER TABLE sci ADD COLUMN IF NOT EXISTS nb_parts_total INTEGER DEFAULT 1000;
ALTER TABLE sci ADD COLUMN IF NOT EXISTS valeur_nominale_part NUMERIC(10,2) DEFAULT 1.00;

ALTER TABLE associes ADD COLUMN IF NOT EXISTS nb_parts INTEGER;

-- =============================================================================
-- C12 — Registre des mouvements de parts (Article 1865 Code civil)
-- =============================================================================

CREATE TABLE IF NOT EXISTS mouvements_parts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  id_sci UUID NOT NULL REFERENCES sci(id) ON DELETE CASCADE,
  date_mouvement DATE NOT NULL,
  type_mouvement TEXT NOT NULL CHECK (type_mouvement IN ('cession', 'apport', 'rachat', 'succession', 'donation')),
  cedant_id UUID REFERENCES associes(id) ON DELETE SET NULL,
  cessionnaire_id UUID REFERENCES associes(id) ON DELETE SET NULL,
  cedant_nom TEXT,
  cessionnaire_nom TEXT,
  nb_parts INTEGER NOT NULL CHECK (nb_parts > 0),
  prix_unitaire NUMERIC(10,2),
  prix_total NUMERIC(15,2),
  document_url TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

ALTER TABLE mouvements_parts ENABLE ROW LEVEL SECURITY;

CREATE POLICY mouvements_parts_member_select ON mouvements_parts FOR SELECT
  USING (id_sci IN (SELECT get_user_sci_ids()));

CREATE POLICY mouvements_parts_gerant_insert ON mouvements_parts FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM associes
      WHERE id_sci = mouvements_parts.id_sci
        AND user_id = auth.uid()
        AND role = 'gerant'
    )
  );

CREATE POLICY mouvements_parts_gerant_update ON mouvements_parts FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM associes
      WHERE id_sci = mouvements_parts.id_sci
        AND user_id = auth.uid()
        AND role = 'gerant'
    )
  );

CREATE POLICY mouvements_parts_gerant_delete ON mouvements_parts FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM associes
      WHERE id_sci = mouvements_parts.id_sci
        AND user_id = auth.uid()
        AND role = 'gerant'
    )
  );

-- =============================================================================
-- C13 — Registre des assemblées générales
-- =============================================================================

CREATE TABLE IF NOT EXISTS assemblees_generales (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  id_sci UUID NOT NULL REFERENCES sci(id) ON DELETE CASCADE,
  date_ag DATE NOT NULL,
  type_ag TEXT NOT NULL DEFAULT 'ordinaire' CHECK (type_ag IN ('ordinaire', 'extraordinaire')),
  exercice_annee INTEGER,
  ordre_du_jour TEXT,
  pv_url TEXT,
  quorum_atteint BOOLEAN DEFAULT FALSE,
  resolutions TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
  -- Une seule AG ordinaire par exercice par SCI
  UNIQUE (id_sci, type_ag, exercice_annee)
);

ALTER TABLE assemblees_generales ENABLE ROW LEVEL SECURITY;

CREATE POLICY ag_member_select ON assemblees_generales FOR SELECT
  USING (id_sci IN (SELECT get_user_sci_ids()));

CREATE POLICY ag_gerant_insert ON assemblees_generales FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM associes
      WHERE id_sci = assemblees_generales.id_sci
        AND user_id = auth.uid()
        AND role = 'gerant'
    )
  );

CREATE POLICY ag_gerant_update ON assemblees_generales FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM associes
      WHERE id_sci = assemblees_generales.id_sci
        AND user_id = auth.uid()
        AND role = 'gerant'
    )
  );

CREATE POLICY ag_gerant_delete ON assemblees_generales FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM associes
      WHERE id_sci = assemblees_generales.id_sci
        AND user_id = auth.uid()
        AND role = 'gerant'
    )
  );
