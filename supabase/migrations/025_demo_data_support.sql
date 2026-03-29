-- 025_demo_data_support.sql
-- Add is_demo flag to entity tables for demo data lifecycle management
-- Each ALTER is wrapped to skip gracefully if table doesn't exist

DO $$ BEGIN
  ALTER TABLE sci ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN undefined_table THEN NULL;
END $$;

DO $$ BEGIN
  ALTER TABLE biens ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN undefined_table THEN NULL;
END $$;

DO $$ BEGIN
  ALTER TABLE baux ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN undefined_table THEN NULL;
END $$;

DO $$ BEGIN
  ALTER TABLE loyers ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN undefined_table THEN NULL;
END $$;

DO $$ BEGIN
  ALTER TABLE charges ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN undefined_table THEN NULL;
END $$;

DO $$ BEGIN
  ALTER TABLE locataires ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN undefined_table THEN NULL;
END $$;

DO $$ BEGIN
  ALTER TABLE assurances_pno ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN undefined_table THEN NULL;
END $$;

DO $$ BEGIN
  ALTER TABLE associes ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN undefined_table THEN NULL;
END $$;

-- Flag on subscriptions to track if demo has been seeded
DO $$ BEGIN
  ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS demo_seeded BOOLEAN DEFAULT FALSE;
EXCEPTION WHEN undefined_table THEN NULL;
END $$;

-- Partial indexes for fast cleanup (only index demo=true rows)
CREATE INDEX IF NOT EXISTS idx_sci_is_demo ON sci(is_demo) WHERE is_demo = TRUE;
CREATE INDEX IF NOT EXISTS idx_biens_is_demo ON biens(is_demo) WHERE is_demo = TRUE;
CREATE INDEX IF NOT EXISTS idx_loyers_is_demo ON loyers(is_demo) WHERE is_demo = TRUE;
CREATE INDEX IF NOT EXISTS idx_charges_is_demo ON charges(is_demo) WHERE is_demo = TRUE;
