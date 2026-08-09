-- 046_grant_supabase_roles.sql
-- Rend le dépôt capable d'amorcer une base locale fonctionnelle.
--
-- PROBLÈME
--   Les privilèges par défaut du schéma `public` sont enregistrés pour le rôle
--   créateur `supabase_admin` (cf. pg_default_acl). Or le CLI Supabase exécute
--   les migrations en tant que `postgres` : les tables créées héritent donc
--   d'aucune ACL pour `anon`, `authenticated` et `service_role`.
--   Aucune migration du dépôt ne contenait de GRANT, si bien qu'un
--   `supabase db reset` propre produisait une base inutilisable :
--     permission denied for table sci (SQLSTATE 42501)
--   Symptômes : /health/ready en `degraded`, seed démo en échec, aucune
--   lecture `authenticated`, aucune écriture `service_role`.
--
--   La production n'est pas concernée : ses trois rôles ont déjà le DML
--   complet sur toutes les tables (vérifié le 2026-08-09). Cette migration y
--   est donc un no-op.
--
-- MODÈLE DE SÉCURITÉ
--   Accorder le DML à `anon` et `authenticated` est le modèle Supabase
--   standard et correspond exactement à l'état de la production. La frontière
--   de sécurité réelle est RLS, activé sur toutes les tables, et non les
--   privilèges de table. Voir CLAUDE.md, invariant 6 : Supabase est exposé
--   publiquement, tout contrôle purement applicatif est contournable.
--
-- ⚠️ ORDRE CRITIQUE
--   La migration 043 retire les droits d'écriture sur `subscriptions` à
--   `anon` et `authenticated` : c'est le correctif de la faille C1
--   (auto-attribution d'un plan payant via PostgREST, exploit reproduit en
--   production le 2026-07-25). Un GRANT ALL postérieur les rendrait, et
--   rouvrirait la faille. Le revoke est donc rejoué en fin de fichier.
--   Toute modification de ce fichier doit conserver ce bloc final.
--
-- Idempotent : rejouable sans effet de bord.

begin;

-- ── Accès au schéma ─────────────────────────────────────────────────────────
grant usage on schema public to anon, authenticated, service_role;

-- ── Objets déjà créés par les migrations 001 à 045 ─────────────────────────
grant all privileges on all tables    in schema public to anon, authenticated, service_role;
grant all privileges on all sequences in schema public to anon, authenticated, service_role;
grant all privileges on all functions in schema public to anon, authenticated, service_role;

-- ── Objets futurs créés par `postgres` (le rôle qui exécute les migrations) ─
-- Sans ceci, toute nouvelle table repartirait sans droits et le problème
-- réapparaîtrait à la prochaine migration.
alter default privileges for role postgres in schema public
  grant all on tables    to anon, authenticated, service_role;
alter default privileges for role postgres in schema public
  grant all on sequences to anon, authenticated, service_role;
alter default privileges for role postgres in schema public
  grant all on functions to anon, authenticated, service_role;

-- ── Restauration de l'invariant C1 (migration 043) ──────────────────────────
-- NE PAS SUPPRIMER. Le GRANT ALL ci-dessus vient de rendre à `anon` et
-- `authenticated` les droits d'écriture sur `subscriptions` que 043 avait
-- retirés. On les retire de nouveau. `service_role` conserve l'accès complet
-- et bypasse RLS : les écritures légitimes (webhook Stripe, seed démo,
-- onboarding, admin) continuent de fonctionner.
revoke insert, update, delete on subscriptions from anon, authenticated;

commit;

-- ═══════════════════════════════════════════════════════════════════════════
-- VÉRIFICATION POST-MIGRATION
--
-- 1) service_role lit et écrit partout :
--    select count(*) from information_schema.tables t
--     where t.table_schema='public' and t.table_type='BASE TABLE'
--       and not exists (select 1 from information_schema.role_table_grants g
--                       where g.grantee='service_role' and g.table_schema='public'
--                         and g.table_name=t.table_name and g.privilege_type='SELECT');
--    -> attendu : 0
--
-- 2) C1 toujours fermé — aucune écriture utilisateur sur subscriptions :
--    select grantee, privilege_type from information_schema.role_table_grants
--     where table_schema='public' and table_name='subscriptions'
--       and grantee in ('anon','authenticated')
--       and privilege_type in ('INSERT','UPDATE','DELETE');
--    -> attendu : aucune ligne
--
-- 3) /health/ready ne rapporte plus la base en `degraded`.
-- ═══════════════════════════════════════════════════════════════════════════
