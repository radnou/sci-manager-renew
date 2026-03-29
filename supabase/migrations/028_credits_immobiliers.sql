-- 028_credits_immobiliers.sql
-- Crédit immobilier tracking per bien (mortgage/loan amortization)

CREATE TABLE IF NOT EXISTS credits_immobiliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_bien UUID NOT NULL REFERENCES biens(id) ON DELETE CASCADE,
    banque TEXT NOT NULL,
    numero_contrat TEXT,
    montant_emprunte NUMERIC(12,2) NOT NULL CHECK (montant_emprunte > 0),
    taux_nominal NUMERIC(5,3) NOT NULL CHECK (taux_nominal >= 0),
    taux_assurance NUMERIC(5,3) DEFAULT 0 CHECK (taux_assurance >= 0),
    duree_mois INTEGER NOT NULL CHECK (duree_mois > 0),
    date_debut DATE NOT NULL,
    mensualite NUMERIC(10,2) NOT NULL CHECK (mensualite > 0),
    capital_restant_du NUMERIC(12,2),
    type_credit TEXT DEFAULT 'amortissable' CHECK (type_credit IN ('amortissable', 'in_fine', 'relais')),
    statut TEXT DEFAULT 'en_cours' CHECK (statut IN ('en_cours', 'rembourse', 'restructure')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_credits_immobiliers_id_bien ON credits_immobiliers(id_bien);
CREATE INDEX IF NOT EXISTS idx_credits_immobiliers_statut ON credits_immobiliers(statut);

-- Updated_at trigger
DROP TRIGGER IF EXISTS trg_credits_immobiliers_updated_at ON credits_immobiliers;
CREATE TRIGGER trg_credits_immobiliers_updated_at
BEFORE UPDATE ON credits_immobiliers
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================================
-- RLS POLICIES (same pattern as assurances_pno)
-- =============================================================================

ALTER TABLE credits_immobiliers ENABLE ROW LEVEL SECURITY;

CREATE POLICY credits_immobiliers_member_select ON credits_immobiliers FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = credits_immobiliers.id_bien AND a.user_id = auth.uid()
  )
);

CREATE POLICY credits_immobiliers_gerant_insert ON credits_immobiliers FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = credits_immobiliers.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
);

CREATE POLICY credits_immobiliers_gerant_update ON credits_immobiliers FOR UPDATE
USING (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = credits_immobiliers.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
)
WITH CHECK (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = credits_immobiliers.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
);

CREATE POLICY credits_immobiliers_gerant_delete ON credits_immobiliers FOR DELETE
USING (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = credits_immobiliers.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
);
