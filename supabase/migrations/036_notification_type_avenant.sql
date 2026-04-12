-- Migration 036: Add avenant_bail and conge_bail notification types
ALTER TABLE notifications DROP CONSTRAINT IF EXISTS notifications_type_check;
ALTER TABLE notifications ADD CONSTRAINT notifications_type_check
  CHECK (type IN (
    'late_payment', 'status_change', 'document_ready', 'system', 'info',
    'bail_expiring', 'quittance_pending', 'pno_expiring', 'fiscal_deadline',
    'new_loyer', 'new_associe', 'subscription_expiring',
    'bail_renewal', 'bail_conge_deadline', 'regularisation_charges',
    'depot_garantie_restitution',
    'avenant_bail', 'conge_bail', 'sinistre'
  ));
