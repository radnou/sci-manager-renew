-- Migration: bilans_mensuels
-- Stores monthly accounting snapshots per user/scope

CREATE TABLE IF NOT EXISTS bilans_mensuels (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  periode TEXT NOT NULL,           -- "2026-03" format YYYY-MM
  scope TEXT NOT NULL,             -- "portefeuille" | "sci" | "bien"
  scope_id UUID,                   -- NULL pour portefeuille, sci_id ou bien_id
  scope_nom TEXT,                  -- nom affiche (SCI nom, adresse bien, "Portefeuille")
  data JSONB NOT NULL,             -- snapshot des donnees calculees
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(user_id, periode, scope, scope_id)
);

-- Index for fast lookups by user + period
CREATE INDEX idx_bilans_mensuels_user_periode ON bilans_mensuels(user_id, periode);

ALTER TABLE bilans_mensuels ENABLE ROW LEVEL SECURITY;

-- RLS: user can only see own bilans
CREATE POLICY "bilans_owner_select" ON bilans_mensuels
  FOR SELECT USING (user_id = auth.uid());

-- Service role can do everything (cron writes)
CREATE POLICY "bilans_service_all" ON bilans_mensuels
  FOR ALL TO service_role USING (true) WITH CHECK (true);
