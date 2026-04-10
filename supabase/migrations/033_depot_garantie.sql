-- Migration 033: Depot de garantie restitution tracking
-- Adds depot_restitue (boolean), date_restitution (date) to baux
-- Also extends statut constraint to include 'termine' (used by cloturer endpoint)

-- Add depot restitution tracking columns
ALTER TABLE baux ADD COLUMN IF NOT EXISTS depot_restitue BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE baux ADD COLUMN IF NOT EXISTS date_restitution DATE;

-- Fix baux statut constraint to include 'termine' (used by cloturer endpoint)
ALTER TABLE baux DROP CONSTRAINT IF EXISTS baux_statut_check;
ALTER TABLE baux ADD CONSTRAINT baux_statut_check
  CHECK (statut IN ('en_cours', 'expire', 'resilie', 'termine'));

-- Index for cron query: baux terminated without depot restitution
CREATE INDEX IF NOT EXISTS idx_baux_depot_restitution
  ON baux(statut, depot_restitue, date_fin)
  WHERE statut = 'termine' AND depot_restitue = FALSE;
