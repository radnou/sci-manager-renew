-- 035_onboarding_profile.sql
-- Add onboarding profile JSONB column to subscriptions for user segmentation.
-- Schema: { role: string, volume: string, current_tool: string, priorities: string[] }

ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS onboarding_profile JSONB DEFAULT NULL;
