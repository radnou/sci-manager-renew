-- 012: Add type_bien column to biens table
-- Stores the building category (appartement, maison, immeuble, etc.)
-- Distinct from type_locatif which stores the rental type (nu, meuble, mixte)

ALTER TABLE biens ADD COLUMN IF NOT EXISTS type_bien TEXT
  CHECK (type_bien IS NULL OR type_bien IN ('appartement', 'maison', 'immeuble', 'local_commercial', 'parking', 'autre'));
