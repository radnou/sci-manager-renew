-- 016: Déficit foncier reportable tracker
-- Tracks annual rental deficits per SCI with 10-year prescription (art. 156-I-3° CGI)

CREATE TABLE IF NOT EXISTS deficit_reportable (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_sci UUID NOT NULL REFERENCES sci(id) ON DELETE CASCADE,
    annee_constatation INTEGER NOT NULL,
    deficit_interets NUMERIC(12,2) NOT NULL DEFAULT 0,
    deficit_charges NUMERIC(12,2) NOT NULL DEFAULT 0,
    impute_revenu_global NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_impute_foncier NUMERIC(12,2) NOT NULL DEFAULT 0,
    solde_restant NUMERIC(12,2) NOT NULL DEFAULT 0,
    annee_prescription INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(id_sci, annee_constatation)
);

ALTER TABLE deficit_reportable ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage deficit_reportable for their SCIs"
    ON deficit_reportable
    FOR ALL
    USING (
        id_sci IN (
            SELECT id_sci FROM associes WHERE user_id = auth.uid()
        )
    );
