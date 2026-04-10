-- Migration 031: zone_tendue on biens + bail mobilite support
-- zone_tendue: affects préavis locataire (3 mois → 1 mois)
-- bail mobilite: short-term furnished (1-10 mois, étudiant/professionnel)

-- 1. Add zone_tendue to biens
ALTER TABLE biens ADD COLUMN IF NOT EXISTS zone_tendue BOOLEAN NOT NULL DEFAULT FALSE;

-- 2. Allow 'mobilite' as type_locatif value (already stored as text in DB)
-- No constraint change needed — type_locatif is a varchar/text column with no DB-level enum

-- Comment for clarity
COMMENT ON COLUMN biens.zone_tendue IS 'Zone tendue (loi Alur) — réduit le préavis locataire de 3 mois à 1 mois';
