-- Migration 030: Cascading rent date (jour_loyer) settings
-- Adds jour_loyer at bien-level and SCI-level.
-- Resolution order: bien.jour_loyer ?? sci.jour_loyer ?? global_default (stored in localStorage) ?? 1

ALTER TABLE biens
    ADD COLUMN IF NOT EXISTS jour_loyer SMALLINT
        CHECK (jour_loyer BETWEEN 1 AND 28);

ALTER TABLE sci
    ADD COLUMN IF NOT EXISTS jour_loyer SMALLINT
        CHECK (jour_loyer BETWEEN 1 AND 28);

COMMENT ON COLUMN biens.jour_loyer IS
    'Jour du mois de génération du loyer (1-28). Hérite de sci.jour_loyer si NULL.';

COMMENT ON COLUMN sci.jour_loyer IS
    'Jour du mois de génération du loyer par défaut pour tous les biens de la SCI (1-28). Hérite du réglage global utilisateur si NULL.';
