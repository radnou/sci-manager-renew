-- Migration 019: SCI & Bien lifecycle features
-- Adds dissolution fields to SCI, acquisition/cession fields to biens,
-- and expands evenements_bien types for lifecycle events.

-- ── SCI dissolution fields ──
ALTER TABLE sci ADD COLUMN IF NOT EXISTS statut VARCHAR(20) DEFAULT 'active' CHECK (statut IN ('active', 'en_dissolution', 'dissoute'));
ALTER TABLE sci ADD COLUMN IF NOT EXISTS date_dissolution DATE;
ALTER TABLE sci ADD COLUMN IF NOT EXISTS motif_dissolution TEXT;
ALTER TABLE sci ADD COLUMN IF NOT EXISTS liquidateur VARCHAR(100);

-- ── Bien acquisition & cession fields ──
ALTER TABLE biens ADD COLUMN IF NOT EXISTS frais_notaire NUMERIC(10,2);
ALTER TABLE biens ADD COLUMN IF NOT EXISTS frais_agence_acquisition NUMERIC(10,2);
ALTER TABLE biens ADD COLUMN IF NOT EXISTS prix_cession NUMERIC(12,2);
ALTER TABLE biens ADD COLUMN IF NOT EXISTS date_cession DATE;
ALTER TABLE biens ADD COLUMN IF NOT EXISTS acquereur VARCHAR(200);
ALTER TABLE biens ADD COLUMN IF NOT EXISTS frais_cession NUMERIC(10,2);

-- ── Expand evenements_bien types for lifecycle events ──
ALTER TABLE evenements_bien DROP CONSTRAINT IF EXISTS evenements_bien_type_check;
ALTER TABLE evenements_bien ADD CONSTRAINT evenements_bien_type_check CHECK (type IN (
    'reparation', 'travaux', 'sinistre', 'visite',
    'controle', 'diagnostic', 'autre',
    'acquisition', 'cession'
));

-- ── Associes: add nb_parts column for absolute part tracking ──
ALTER TABLE associes ADD COLUMN IF NOT EXISTS nb_parts INT;

-- ── Indexes ──
CREATE INDEX IF NOT EXISTS idx_sci_statut ON sci(statut);
CREATE INDEX IF NOT EXISTS idx_biens_date_cession ON biens(date_cession) WHERE date_cession IS NOT NULL;
