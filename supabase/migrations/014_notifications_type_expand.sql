-- 014: Expand notifications type check constraint
-- Add new notification types used by the cron system

ALTER TABLE notifications DROP CONSTRAINT IF EXISTS notifications_type_check;
ALTER TABLE notifications ADD CONSTRAINT notifications_type_check
  CHECK (type IN (
    'late_payment', 'status_change', 'document_ready', 'system', 'info',
    'bail_expiring', 'quittance_pending', 'pno_expiring', 'fiscal_deadline',
    'new_loyer', 'new_associe', 'subscription_expiring'
  ));
