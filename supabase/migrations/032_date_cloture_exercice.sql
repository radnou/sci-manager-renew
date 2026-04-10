-- Migration 032: Add date_cloture_exercice to sci table
-- Fiscal year end date. NULL = calendar year (December 31).
-- For SCIs with non-standard fiscal years (e.g., 30/06, 31/03),
-- this date drives dynamic deadline computation in notification_cron.

ALTER TABLE sci ADD COLUMN IF NOT EXISTS date_cloture_exercice DATE;

COMMENT ON COLUMN sci.date_cloture_exercice IS
  'Date de clôture de l''exercice fiscal (NULL = 31 décembre). '
  'Utilisée pour calculer dynamiquement les échéances fiscales.';
