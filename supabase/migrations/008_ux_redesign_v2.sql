-- 008_ux_redesign_v2.sql
-- UX Redesign V2: nouvelles tables (baux, bail_locataires, assurances_pno, frais_agence,
-- notification_preferences, documents_bien), colonnes enrichies, RLS gerant-only, data migration.

-- =============================================================================
-- 1. COLONNES AJOUTEES
-- =============================================================================

-- biens: enrichissement fiche bien
ALTER TABLE biens ADD COLUMN IF NOT EXISTS surface_m2 NUMERIC;
ALTER TABLE biens ADD COLUMN IF NOT EXISTS nb_pieces INTEGER;
ALTER TABLE biens ADD COLUMN IF NOT EXISTS dpe_classe TEXT CHECK (dpe_classe IN ('A','B','C','D','E','F','G'));
ALTER TABLE biens ADD COLUMN IF NOT EXISTS photo_url TEXT;
ALTER TABLE biens ADD COLUMN IF NOT EXISTS prix_acquisition NUMERIC(14,2);

-- locataires: telephone
ALTER TABLE locataires ADD COLUMN IF NOT EXISTS telephone TEXT;

-- subscriptions: onboarding flag
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE;

-- =============================================================================
-- 2. NOUVELLES TABLES
-- =============================================================================

-- Baux (remplace le lien date direct locataire-bien)
CREATE TABLE IF NOT EXISTS baux (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  id_bien UUID NOT NULL REFERENCES biens(id) ON DELETE CASCADE,
  date_debut DATE NOT NULL,
  date_fin DATE,
  loyer_hc NUMERIC(12,2) NOT NULL CHECK (loyer_hc >= 0),
  charges_locatives NUMERIC(12,2) DEFAULT 0 CHECK (charges_locatives >= 0),
  depot_garantie NUMERIC(12,2) DEFAULT 0 CHECK (depot_garantie >= 0),
  indice_irl_reference TEXT,
  date_revision DATE,
  etat_lieux_entree DATE,
  etat_lieux_sortie DATE,
  statut TEXT NOT NULL DEFAULT 'en_cours' CHECK (statut IN ('en_cours','expire','resilie')),
  document_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_baux_id_bien ON baux(id_bien);
CREATE INDEX IF NOT EXISTS idx_baux_statut ON baux(statut);

-- Jointure bail-locataires (colocation N:N)
CREATE TABLE IF NOT EXISTS bail_locataires (
  id_bail UUID NOT NULL REFERENCES baux(id) ON DELETE CASCADE,
  id_locataire UUID NOT NULL REFERENCES locataires(id) ON DELETE CASCADE,
  PRIMARY KEY (id_bail, id_locataire)
);

-- Assurance PNO (propriétaire non-occupant)
CREATE TABLE IF NOT EXISTS assurances_pno (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  id_bien UUID NOT NULL REFERENCES biens(id) ON DELETE CASCADE,
  compagnie TEXT NOT NULL,
  numero_contrat TEXT,
  montant_annuel NUMERIC(12,2) NOT NULL CHECK (montant_annuel >= 0),
  date_echeance DATE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_assurances_pno_id_bien ON assurances_pno(id_bien);

-- Frais d'agence (gestion locative)
CREATE TABLE IF NOT EXISTS frais_agence (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  id_bien UUID NOT NULL REFERENCES biens(id) ON DELETE CASCADE,
  nom_agence TEXT NOT NULL,
  contact TEXT,
  type_frais TEXT NOT NULL CHECK (type_frais IN ('pourcentage','fixe')),
  montant_ou_pourcentage NUMERIC(12,2) NOT NULL CHECK (montant_ou_pourcentage >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_frais_agence_id_bien ON frais_agence(id_bien);

-- Préférences notifications (user-level, per-type)
CREATE TABLE IF NOT EXISTS notification_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  type TEXT NOT NULL,
  email_enabled BOOLEAN DEFAULT FALSE,
  in_app_enabled BOOLEAN DEFAULT TRUE,
  UNIQUE(user_id, type)
);

CREATE INDEX IF NOT EXISTS idx_notification_prefs_user ON notification_preferences(user_id);

-- Documents attachés aux biens
CREATE TABLE IF NOT EXISTS documents_bien (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  id_bien UUID NOT NULL REFERENCES biens(id) ON DELETE CASCADE,
  categorie TEXT NOT NULL CHECK (categorie IN ('bail','diagnostic','etat_lieux','quittance','photo','autre')),
  nom TEXT NOT NULL,
  file_url TEXT NOT NULL,
  file_size INTEGER,
  uploaded_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_documents_bien_id_bien ON documents_bien(id_bien);

-- =============================================================================
-- 3. TRIGGERS updated_at
-- =============================================================================

DROP TRIGGER IF EXISTS trg_baux_updated_at ON baux;
CREATE TRIGGER trg_baux_updated_at
BEFORE UPDATE ON baux
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_assurances_pno_updated_at ON assurances_pno;
CREATE TRIGGER trg_assurances_pno_updated_at
BEFORE UPDATE ON assurances_pno
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_frais_agence_updated_at ON frais_agence;
CREATE TRIGGER trg_frais_agence_updated_at
BEFORE UPDATE ON frais_agence
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================================
-- 4. RLS POLICIES
-- =============================================================================

-- Enable RLS on all new tables
ALTER TABLE baux ENABLE ROW LEVEL SECURITY;
ALTER TABLE bail_locataires ENABLE ROW LEVEL SECURITY;
ALTER TABLE assurances_pno ENABLE ROW LEVEL SECURITY;
ALTER TABLE frais_agence ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents_bien ENABLE ROW LEVEL SECURITY;

-- ---- baux ----
CREATE POLICY baux_member_select ON baux FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = baux.id_bien AND a.user_id = auth.uid()
  )
);

CREATE POLICY baux_gerant_insert ON baux FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = baux.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
);

CREATE POLICY baux_gerant_update ON baux FOR UPDATE
USING (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = baux.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
)
WITH CHECK (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = baux.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
);

CREATE POLICY baux_gerant_delete ON baux FOR DELETE
USING (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = baux.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
);

-- ---- bail_locataires ----
CREATE POLICY bail_loc_member_select ON bail_locataires FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM baux bx
    JOIN biens b ON b.id = bx.id_bien
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE bx.id = bail_locataires.id_bail AND a.user_id = auth.uid()
  )
);

CREATE POLICY bail_loc_gerant_insert ON bail_locataires FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM baux bx
    JOIN biens b ON b.id = bx.id_bien
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE bx.id = bail_locataires.id_bail
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
);

CREATE POLICY bail_loc_gerant_delete ON bail_locataires FOR DELETE
USING (
  EXISTS (
    SELECT 1 FROM baux bx
    JOIN biens b ON b.id = bx.id_bien
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE bx.id = bail_locataires.id_bail
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
);

-- ---- assurances_pno ----
CREATE POLICY assurances_pno_member_select ON assurances_pno FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = assurances_pno.id_bien AND a.user_id = auth.uid()
  )
);

CREATE POLICY assurances_pno_gerant_insert ON assurances_pno FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = assurances_pno.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
);

CREATE POLICY assurances_pno_gerant_update ON assurances_pno FOR UPDATE
USING (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = assurances_pno.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
)
WITH CHECK (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = assurances_pno.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
);

CREATE POLICY assurances_pno_gerant_delete ON assurances_pno FOR DELETE
USING (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = assurances_pno.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
);

-- ---- frais_agence ----
CREATE POLICY frais_agence_member_select ON frais_agence FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = frais_agence.id_bien AND a.user_id = auth.uid()
  )
);

CREATE POLICY frais_agence_gerant_insert ON frais_agence FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = frais_agence.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
);

CREATE POLICY frais_agence_gerant_update ON frais_agence FOR UPDATE
USING (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = frais_agence.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
)
WITH CHECK (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = frais_agence.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
);

CREATE POLICY frais_agence_gerant_delete ON frais_agence FOR DELETE
USING (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = frais_agence.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
);

-- ---- notification_preferences (owner only) ----
CREATE POLICY notif_prefs_owner_select ON notification_preferences FOR SELECT
USING (user_id = auth.uid());

CREATE POLICY notif_prefs_owner_insert ON notification_preferences FOR INSERT
WITH CHECK (user_id = auth.uid());

CREATE POLICY notif_prefs_owner_update ON notification_preferences FOR UPDATE
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

CREATE POLICY notif_prefs_owner_delete ON notification_preferences FOR DELETE
USING (user_id = auth.uid());

-- ---- documents_bien ----
CREATE POLICY documents_bien_member_select ON documents_bien FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = documents_bien.id_bien AND a.user_id = auth.uid()
  )
);

CREATE POLICY documents_bien_gerant_insert ON documents_bien FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = documents_bien.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
);

CREATE POLICY documents_bien_gerant_delete ON documents_bien FOR DELETE
USING (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = documents_bien.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
);

-- =============================================================================
-- 5. DATA MIGRATION: locataires -> baux
-- =============================================================================

-- Créer un bail pour chaque locataire existant (si des locataires existent)
INSERT INTO baux (id_bien, date_debut, date_fin, loyer_hc, statut)
SELECT
  l.id_bien,
  l.date_debut,
  l.date_fin,
  COALESCE(b.loyer_cc, 0),
  CASE
    WHEN l.date_fin IS NOT NULL AND l.date_fin < CURRENT_DATE THEN 'expire'
    ELSE 'en_cours'
  END
FROM locataires l
JOIN biens b ON b.id = l.id_bien
WHERE NOT EXISTS (SELECT 1 FROM baux WHERE baux.id_bien = l.id_bien AND baux.date_debut = l.date_debut);

-- Créer les jointures bail_locataires
INSERT INTO bail_locataires (id_bail, id_locataire)
SELECT bx.id, l.id
FROM baux bx
JOIN locataires l ON l.id_bien = bx.id_bien AND l.date_debut = bx.date_debut
WHERE NOT EXISTS (
  SELECT 1 FROM bail_locataires bl
  WHERE bl.id_bail = bx.id AND bl.id_locataire = l.id
);

-- =============================================================================
-- 6. EXISTING USERS: bypass onboarding
-- =============================================================================

UPDATE subscriptions SET onboarding_completed = true WHERE status IN ('active', 'trialing');
