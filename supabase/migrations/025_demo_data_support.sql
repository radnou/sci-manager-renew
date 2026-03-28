-- 025_demo_data_support.sql
-- Add is_demo flag to entity tables for demo data lifecycle management

ALTER TABLE sci ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE biens ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE baux ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE loyers ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE charges ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE locataires ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE assurance_pno ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE associes ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;

-- Flag on subscriptions to track if demo has been seeded
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS demo_seeded BOOLEAN DEFAULT FALSE;

-- Partial indexes for fast cleanup (only index demo=true rows)
CREATE INDEX IF NOT EXISTS idx_sci_is_demo ON sci(is_demo) WHERE is_demo = TRUE;
CREATE INDEX IF NOT EXISTS idx_biens_is_demo ON biens(is_demo) WHERE is_demo = TRUE;
CREATE INDEX IF NOT EXISTS idx_loyers_is_demo ON loyers(is_demo) WHERE is_demo = TRUE;
CREATE INDEX IF NOT EXISTS idx_charges_is_demo ON charges(is_demo) WHERE is_demo = TRUE;
