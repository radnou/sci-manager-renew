-- Migration 018: Add congé (notice to quit) fields to baux table
-- Supports both locataire and bailleur congé types

ALTER TABLE baux ADD COLUMN IF NOT EXISTS date_conge DATE;
ALTER TABLE baux ADD COLUMN IF NOT EXISTS motif_conge TEXT;
ALTER TABLE baux ADD COLUMN IF NOT EXISTS type_conge VARCHAR(20);
