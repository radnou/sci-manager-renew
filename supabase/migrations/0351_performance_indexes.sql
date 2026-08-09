-- Performance indexes identified by QA dogfooding audit 2026-04-11

-- 1. Dashboard alert query: loyers filtered by statut
-- Used by dashboard_service.get_alertes() and notification_cron.check_late_payments()
CREATE INDEX IF NOT EXISTS idx_loyers_id_sci_statut ON loyers(id_sci, statut);

-- 2. Bail/charge queries joining biens to SCIs
-- Used by notification_cron, regularisation_service, dashboard_service
CREATE INDEX IF NOT EXISTS idx_biens_id_sci_id ON biens(id_sci, id);

-- 3. Notification center pagination (ordered by created_at DESC)
-- Supersedes idx_notifications_user_id for ordered queries
CREATE INDEX IF NOT EXISTS idx_notifications_user_created ON notifications(user_id, created_at DESC);
