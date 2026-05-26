-- Migration 041: loyers unique constraint per calendar month
-- Replaces exact-date partial indexes with a single month-level unique constraint.
-- Drops partial indexes added in migration 040 in favour of one plain index.

DROP INDEX IF EXISTS uq_loyers_bien_date_no_locataire;
DROP INDEX IF EXISTS uq_loyers_bien_locataire_date;

CREATE UNIQUE INDEX uq_loyers_bien_month
  ON loyers (id_bien, date_trunc('month', date_loyer));
