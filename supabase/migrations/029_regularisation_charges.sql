-- 028: Table de persistance des régularisations annuelles de charges
-- Loi ALUR art. 23 — obligation de régularisation annuelle

CREATE TABLE IF NOT EXISTS regularisations_charges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_bien UUID NOT NULL REFERENCES biens(id) ON DELETE CASCADE,
    id_bail UUID NOT NULL REFERENCES baux(id) ON DELETE CASCADE,
    annee INTEGER NOT NULL,
    total_provisions NUMERIC(10,2) NOT NULL DEFAULT 0,
    total_charges_reelles NUMERIC(10,2) NOT NULL DEFAULT 0,
    solde NUMERIC(10,2) NOT NULL DEFAULT 0,
    sens TEXT NOT NULL DEFAULT 'equilibre',
    statut TEXT NOT NULL DEFAULT 'brouillon',
    date_regularisation DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(id_bien, id_bail, annee)
);

-- RLS
ALTER TABLE regularisations_charges ENABLE ROW LEVEL SECURITY;

-- Read access: users who are associés of the SCI owning the bien
CREATE POLICY "regularisations_select" ON regularisations_charges
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM biens b
            JOIN associes a ON a.id_sci = b.id_sci
            WHERE b.id = regularisations_charges.id_bien
              AND a.user_id = auth.uid()
        )
    );

-- Write access: gérants only
CREATE POLICY "regularisations_insert" ON regularisations_charges
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM biens b
            JOIN associes a ON a.id_sci = b.id_sci
            WHERE b.id = regularisations_charges.id_bien
              AND a.user_id = auth.uid()
              AND a.role = 'gerant'
        )
    );

CREATE POLICY "regularisations_update" ON regularisations_charges
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM biens b
            JOIN associes a ON a.id_sci = b.id_sci
            WHERE b.id = regularisations_charges.id_bien
              AND a.user_id = auth.uid()
              AND a.role = 'gerant'
        )
    );

-- Index for common lookups
CREATE INDEX idx_regularisations_bien_bail ON regularisations_charges(id_bien, id_bail, annee);
