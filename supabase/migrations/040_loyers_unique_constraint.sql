-- Migration 040: loyers unique constraint for NULL id_locataire
-- Replace single UNIQUE constraint with two partial unique indexes

ALTER TABLE loyers DROP CONSTRAINT IF EXISTS loyers_id_bien_id_locataire_date_loyer_key;

DROP INDEX IF EXISTS uq_loyers_bien_date_no_locataire;
CREATE UNIQUE INDEX uq_loyers_bien_date_no_locataire
  ON loyers (id_bien, date_loyer)
  WHERE id_locataire IS NULL;

DROP INDEX IF EXISTS uq_loyers_bien_locataire_date;
CREATE UNIQUE INDEX uq_loyers_bien_locataire_date
  ON loyers (id_bien, id_locataire, date_loyer)
  WHERE id_locataire IS NOT NULL;
