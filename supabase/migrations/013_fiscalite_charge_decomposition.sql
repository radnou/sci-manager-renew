-- Migration 013: Add charge decomposition columns to fiscalite
-- These optional fields allow users to break down total_charges into
-- standard French real-estate expense categories (revenus fonciers).

ALTER TABLE fiscalite ADD COLUMN IF NOT EXISTS interets_emprunt NUMERIC DEFAULT 0;
ALTER TABLE fiscalite ADD COLUMN IF NOT EXISTS travaux NUMERIC DEFAULT 0;
ALTER TABLE fiscalite ADD COLUMN IF NOT EXISTS frais_gestion NUMERIC DEFAULT 0;
ALTER TABLE fiscalite ADD COLUMN IF NOT EXISTS assurance NUMERIC DEFAULT 0;
ALTER TABLE fiscalite ADD COLUMN IF NOT EXISTS taxe_fonciere NUMERIC DEFAULT 0;
ALTER TABLE fiscalite ADD COLUMN IF NOT EXISTS copropriete NUMERIC DEFAULT 0;
