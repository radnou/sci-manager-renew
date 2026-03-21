-- 015: Quittance legal compliance
-- SCI extended fields (Code de commerce R.123-237) + quittance sequential numbering

-- SCI legal fields (some already exist from migration 010, adding missing ones)
ALTER TABLE sci ADD COLUMN IF NOT EXISTS rcs_numero VARCHAR(20);
ALTER TABLE sci ADD COLUMN IF NOT EXISTS forme_juridique VARCHAR(30) DEFAULT 'SCI';
ALTER TABLE sci ADD COLUMN IF NOT EXISTS nom_gerant VARCHAR(100);

-- Quittance sequential numbering per SCI per month
CREATE TABLE IF NOT EXISTS quittance_compteur (
    sci_id UUID NOT NULL REFERENCES sci(id) ON DELETE CASCADE,
    annee_mois VARCHAR(6) NOT NULL,  -- e.g. '202603'
    dernier_numero INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (sci_id, annee_mois)
);

-- Enable RLS on quittance_compteur
ALTER TABLE quittance_compteur ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage quittance_compteur for their SCIs"
    ON quittance_compteur
    FOR ALL
    USING (
        sci_id IN (
            SELECT id_sci FROM associes WHERE user_id = auth.uid()
        )
    );

-- Loyer payment tracking
ALTER TABLE loyers ADD COLUMN IF NOT EXISTS date_paiement DATE;
ALTER TABLE loyers ADD COLUMN IF NOT EXISTS mode_paiement VARCHAR(30);
