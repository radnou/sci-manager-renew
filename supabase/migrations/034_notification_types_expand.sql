-- Migration 034: Expand notification type check constraint
-- Adds types used by cron (bail_renewal, bail_conge_deadline, regularisation_charges)
-- and new depot_garantie_restitution alert type

ALTER TABLE notifications DROP CONSTRAINT IF EXISTS notifications_type_check;
ALTER TABLE notifications ADD CONSTRAINT notifications_type_check
  CHECK (type IN (
    'late_payment', 'status_change', 'document_ready', 'system', 'info',
    'bail_expiring', 'quittance_pending', 'pno_expiring', 'fiscal_deadline',
    'new_loyer', 'new_associe', 'subscription_expiring',
    'bail_renewal', 'bail_conge_deadline', 'regularisation_charges',
    'depot_garantie_restitution'
  ));
