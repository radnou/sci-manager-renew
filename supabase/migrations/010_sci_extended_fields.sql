-- 010: Add extended SCI fields for legal compliance
-- adresse_siege, date_creation, capital_social, objet_social, rcs_ville

ALTER TABLE sci ADD COLUMN IF NOT EXISTS adresse_siege TEXT;
ALTER TABLE sci ADD COLUMN IF NOT EXISTS date_creation DATE;
ALTER TABLE sci ADD COLUMN IF NOT EXISTS capital_social NUMERIC(15,2);
ALTER TABLE sci ADD COLUMN IF NOT EXISTS objet_social TEXT;
ALTER TABLE sci ADD COLUMN IF NOT EXISTS rcs_ville VARCHAR(100);
