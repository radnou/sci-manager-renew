-- 043_security_fix_c1_c3_rls.sql
-- Correctif de sécurité suite à l'audit externe du 2026-07-25.
--
-- C1 (CRITICAL) — Contournement total du paiement.
--   Les policies `subscriptions_owner_insert/update/delete` ne contraignaient que
--   `user_id = auth.uid()`. Les colonnes `status`, `is_active`, `plan_key`,
--   `max_scis`, `max_biens`, `features` étaient donc librement écrivables par
--   l'utilisateur via PostgREST exposé publiquement.
--   Exploit reproduit en production le 2026-07-25 :
--     POST /rest/v1/subscriptions {status:"active", plan_key:"pilotage"} -> 201
--     POST /api/v1/scis           -> passe de 402 à 422 (paywall franchi)
--   Correctif : l'écriture sur `subscriptions` devient service_role uniquement.
--   Les écritures légitimes (webhook Stripe, seed démo, onboarding, admin)
--   passent déjà ou passent désormais par le client service_role côté backend.
--
-- C3 (CRITICAL) — Élévation de privilège sur `associes`.
--   a) INSERT : la branche `user_id = auth.uid()` ne contraignait pas `id_sci`,
--      permettant de s'auto-insérer comme gérant dans la SCI d'un autre tenant.
--   b) UPDATE : absence de `WITH CHECK` -> PostgreSQL réutilise l'expression
--      `USING`, donc `role` n'était pas contraint : un associé pouvait se
--      promouvoir gérant (PATCH {role:"gerant"}).
--   Correctif : la gestion des associés est réservée au gérant de la SCI.
--
-- Idempotent : rejouable sans effet de bord.

begin;

-- ============================================================
-- C1 — subscriptions : écriture réservée au service_role
-- ============================================================

-- La lecture par le propriétaire reste autorisée (nécessaire au frontend).
drop policy if exists subscriptions_owner_select on subscriptions;
create policy subscriptions_owner_select on subscriptions
for select
using (user_id = auth.uid());

-- Suppression des policies d'écriture utilisateur (vecteur de C1).
-- Aucune policy d'écriture pour `authenticated`/`anon` = deny-all.
-- `service_role` bypasse RLS et conserve donc l'accès complet.
drop policy if exists subscriptions_owner_insert on subscriptions;
drop policy if exists subscriptions_owner_update on subscriptions;
drop policy if exists subscriptions_owner_delete on subscriptions;

-- Défense en profondeur : retirer explicitement les privilèges d'écriture
-- accordés par défaut aux rôles PostgREST.
revoke insert, update, delete on subscriptions from anon, authenticated;

-- ============================================================
-- C3 — associes : gestion réservée aux rôles de gouvernance
-- ============================================================

-- Le référentiel de rôles réel du produit comporte 4 valeurs
-- (cf. frontend/src/lib/high-value/associes.ts) :
--   gerant, co_gerant, associe, usufruitier
-- Le co-gérant dispose des mêmes pouvoirs de gestion que le gérant : la
-- fonction 038 `is_user_gerant_of_sci` ne testait que role = 'gerant', ce qui
-- aurait privé les co-gérants de toute gestion des associés.
-- On la redéfinit pour couvrir les deux rôles de gouvernance.
create or replace function public.is_user_gerant_of_sci(target_sci_id uuid)
returns boolean
language sql
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.associes
    where id_sci = target_sci_id
      and user_id = auth.uid()
      and role in ('gerant', 'co_gerant')
  );
$$;

-- (a) INSERT : seul un gérant de la SCI cible peut ajouter un associé.
--     La création initiale de la SCI n'est pas impactée : `api/v1/scis.py`
--     insère la SCI et la ligne gérant via le client service_role.
drop policy if exists associes_member_insert on associes;
create policy associes_member_insert on associes for insert
  with check (public.is_user_gerant_of_sci(id_sci));

-- (b) UPDATE : `WITH CHECK` explicite pour empêcher l'auto-promotion.
--     Sans lui, PostgreSQL réutilise `USING` et laisse passer le changement
--     de `role` sur sa propre ligne.
drop policy if exists associes_member_update on associes;
create policy associes_member_update on associes for update
  using (public.is_user_gerant_of_sci(id_sci))
  with check (public.is_user_gerant_of_sci(id_sci));

-- (c) DELETE : même règle.
drop policy if exists associes_member_delete on associes;
create policy associes_member_delete on associes for delete
  using (public.is_user_gerant_of_sci(id_sci));

-- Contrainte de domaine sur `role` : empêche toute valeur hors référentiel,
-- y compris via le client service_role.
-- NB : la contrainte est ajoutée en NOT VALID puis validée séparément, afin
-- que la migration n'échoue pas si des lignes historiques portent un rôle
-- hors référentiel. La validation signalera alors les lignes à corriger sans
-- bloquer le correctif de sécurité C1/C3, qui est prioritaire.
do $$
begin
  if not exists (
    select 1 from pg_constraint where conname = 'associes_role_check'
  ) then
    alter table associes
      add constraint associes_role_check
      check (role in ('gerant', 'co_gerant', 'associe', 'usufruitier'))
      not valid;
  end if;
end $$;

-- Validation séparée : à décommenter après avoir vérifié qu'aucune ligne
-- n'est hors référentiel.
--   select distinct role from associes
--    where role not in ('gerant','co_gerant','associe','usufruitier');
-- alter table associes validate constraint associes_role_check;

commit;

-- ============================================================
-- VÉRIFICATION POST-MIGRATION (à exécuter manuellement)
-- ============================================================
-- 1) Plus aucune policy d'écriture utilisateur sur subscriptions :
--    select policyname, cmd from pg_policies
--     where schemaname='public' and tablename='subscriptions';
--    -> attendu : uniquement subscriptions_owner_select / SELECT
--
-- 2) Les policies associes exigent le rôle gérant :
--    select policyname, cmd, qual, with_check from pg_policies
--     where schemaname='public' and tablename='associes';
--
-- 3) Rejeu de l'exploit C1 avec un compte de test (doit renvoyer 401/403) :
--    curl -X POST "$API/rest/v1/subscriptions" \
--      -H "apikey: $ANON" -H "Authorization: Bearer $USER_JWT" \
--      -d '{"user_id":"<self>","status":"active","plan_key":"pilotage"}'
--    -> attendu : 401 ou 403 (avant correctif : 201)
