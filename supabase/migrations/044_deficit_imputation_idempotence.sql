-- 044_deficit_imputation_idempotence.sql
-- Correctif CRITICAL-5 (audit externe du 2026-07-25).
--
-- Le GET du résumé fiscal exécutait un UPDATE sur `deficit_reportable` :
-- chaque affichage de la page ré-imputait le déficit foncier antérieur, jusqu'à
-- vider le solde reportable. Le résultat affiché changeait à chaque
-- consultation de la même année — un actif fiscal réel disparaissait et la
-- déclaration n'était pas reproductible.
--
-- Le calcul devient en lecture seule (`persist=False` par défaut) et
-- l'imputation passe par une clôture d'exercice explicite. Ces deux colonnes
-- rendent cette clôture idempotente : rejouer la clôture d'une année déjà
-- imputée ne modifie plus rien, et l'affichage réutilise le montant mémorisé
-- au lieu de le recalculer par-dessus un solde déjà décrémenté.
--
-- Idempotent : rejouable sans effet de bord.

begin;

alter table deficit_reportable
  add column if not exists annee_derniere_imputation integer;

alter table deficit_reportable
  add column if not exists montant_derniere_imputation numeric(12,2) not null default 0;

comment on column deficit_reportable.annee_derniere_imputation is
  'Année d''imputation déjà appliquée à cette ligne. Verrou d''idempotence de la clôture d''exercice (audit C5).';

comment on column deficit_reportable.montant_derniere_imputation is
  'Montant imputé lors de cette clôture. Réutilisé à l''affichage pour ne pas ré-imputer sur un solde déjà décrémenté.';

-- Lignes historiques : `solde_restant` a pu être décrémenté par les anciens GET
-- sans qu'aucune clôture n'ait eu lieu. On ne peut pas reconstituer ce qui a
-- été perdu depuis cette table seule — les deux colonnes restent donc à NULL/0,
-- ce qui fait repartir la mécanique proprement à la prochaine clôture.
-- Contrôle des lignes suspectes (solde entamé sans imputation tracée) :
--   select id, id_sci, annee_constatation, deficit_interets + deficit_charges as initial,
--          total_impute_foncier, solde_restant
--     from deficit_reportable
--    where total_impute_foncier > 0
--      and annee_derniere_imputation is null;

commit;
