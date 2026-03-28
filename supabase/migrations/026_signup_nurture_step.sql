-- 026_signup_nurture_step.sql
-- Track nurture email progress for signed-up users who haven't paid yet.
-- nurture_step: 0=none, 1=day1_sent, 2=day3_sent, 3=day7_sent

ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS nurture_step INTEGER DEFAULT 0;
