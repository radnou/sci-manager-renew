-- Migration 017: événements bien + diagnostics
-- Adds event tracking for properties (repairs, works, incidents, inspections)
-- and diagnostic date fields for obligation tracking.

CREATE TABLE IF NOT EXISTS evenements_bien (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_bien UUID NOT NULL REFERENCES biens(id) ON DELETE CASCADE,
    type VARCHAR(30) NOT NULL CHECK (type IN (
        'reparation', 'travaux', 'sinistre', 'visite',
        'controle', 'diagnostic', 'autre'
    )),
    titre VARCHAR(200) NOT NULL,
    description TEXT,
    date_evenement DATE NOT NULL,
    montant NUMERIC(10,2),
    prestataire VARCHAR(200),
    deductible_fiscalement BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE evenements_bien ENABLE ROW LEVEL SECURITY;

-- RLS policies: access via associes membership (same pattern as other bien-related tables)
CREATE POLICY "evenements_bien_select" ON evenements_bien FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM biens b
        JOIN associes a ON a.id_sci = b.id_sci
        WHERE b.id = evenements_bien.id_bien
        AND a.user_id = auth.uid()
    )
);

CREATE POLICY "evenements_bien_insert" ON evenements_bien FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM biens b
        JOIN associes a ON a.id_sci = b.id_sci
        WHERE b.id = evenements_bien.id_bien
        AND a.user_id = auth.uid()
        AND a.role = 'gerant'
    )
);

CREATE POLICY "evenements_bien_update" ON evenements_bien FOR UPDATE USING (
    EXISTS (
        SELECT 1 FROM biens b
        JOIN associes a ON a.id_sci = b.id_sci
        WHERE b.id = evenements_bien.id_bien
        AND a.user_id = auth.uid()
        AND a.role = 'gerant'
    )
);

CREATE POLICY "evenements_bien_delete" ON evenements_bien FOR DELETE USING (
    EXISTS (
        SELECT 1 FROM biens b
        JOIN associes a ON a.id_sci = b.id_sci
        WHERE b.id = evenements_bien.id_bien
        AND a.user_id = auth.uid()
        AND a.role = 'gerant'
    )
);

-- Indexes for common queries
CREATE INDEX idx_evenements_bien_id_bien ON evenements_bien(id_bien);
CREATE INDEX idx_evenements_bien_date ON evenements_bien(date_evenement DESC);
CREATE INDEX idx_evenements_bien_type ON evenements_bien(type);

-- Add diagnostic dates to biens for obligation tracking
ALTER TABLE biens ADD COLUMN IF NOT EXISTS dpe_date DATE;
ALTER TABLE biens ADD COLUMN IF NOT EXISTS diagnostic_amiante_date DATE;
ALTER TABLE biens ADD COLUMN IF NOT EXISTS diagnostic_electricite_date DATE;
ALTER TABLE biens ADD COLUMN IF NOT EXISTS diagnostic_gaz_date DATE;
ALTER TABLE biens ADD COLUMN IF NOT EXISTS diagnostic_plomb_date DATE;
