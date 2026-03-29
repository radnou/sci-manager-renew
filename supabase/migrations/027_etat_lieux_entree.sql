-- État des lieux d'entrée — loi ALUR art. 3-2
-- etat_lieux_entree DATE already exists from migration 008_ux_redesign_v2
ALTER TABLE baux ADD COLUMN IF NOT EXISTS etat_lieux_entree_document_url TEXT;
ALTER TABLE baux ADD COLUMN IF NOT EXISTS etat_lieux_entree_notes TEXT;
