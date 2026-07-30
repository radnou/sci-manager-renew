-- 045_cron_leases.sql
-- Correctif CRITICAL-9 (audit externe du 2026-07-25).
--
-- Le cron de notifications est lancé dans le `lifespan` de FastAPI, donc une
-- fois par worker uvicorn (`--workers 2`), sans aucun verrou : chaque cycle
-- s'exécutait deux fois. Preuve relevée dans les logs de production du
-- 2026-07-30 : le même `signup_nurture_user_lookup_failed` apparaît deux fois
-- pour le même user_id, à 3 ms d'écart. Les clients recevaient donc les
-- relances de loyer en double. De plus `asyncio.sleep(86_400)` part du
-- démarrage du processus : tout déploiement rejouait le cycle immédiatement.
--
-- Un bail (lease) posé en base sérialise les workers, quel que soit leur
-- nombre, y compris s'ils sont répartis sur plusieurs conteneurs.
--
-- L'acquisition tient en un seul UPDATE conditionnel — `where name = ? and
-- locked_until < now()` — donc atomique côté PostgreSQL : deux workers
-- simultanés ne peuvent pas l'obtenir tous les deux. Pas besoin de
-- `pg_advisory_lock`, hors de portée via PostgREST qui ne garde pas de session.
--
-- Idempotent : rejouable sans effet de bord.

begin;

create table if not exists cron_leases (
    name         text primary key,
    locked_until timestamptz not null,
    holder       text,
    updated_at   timestamptz not null default now()
);

comment on table cron_leases is
  'Verrou d''exclusion mutuelle des tâches de fond entre workers (audit C9). Une ligne par tâche.';
comment on column cron_leases.locked_until is
  'Le bail est libre dès que cette date est dépassée. Fait aussi office d''expiration : un worker mort ne bloque pas la tâche indéfiniment.';
comment on column cron_leases.holder is
  'Hôte et PID du détenteur, à titre de diagnostic uniquement.';

-- Aucune policy pour `anon`/`authenticated` : cette table n'est jamais touchée
-- par un utilisateur. Le backend y accède via le client service_role, qui
-- contourne RLS. RLS activé quand même — toute table exposée par PostgREST doit
-- l'être (invariant de sécurité n° 6, cf. CLAUDE.md), sinon elle serait en
-- lecture-écriture publique.
alter table cron_leases enable row level security;

revoke all on cron_leases from anon, authenticated;

commit;

-- ============================================================
-- VÉRIFICATION POST-MIGRATION
-- ============================================================
-- 1) La table n'est accessible ni en lecture ni en écriture aux rôles publics :
--    select grantee, privilege_type from information_schema.role_table_grants
--     where table_name = 'cron_leases' and grantee in ('anon','authenticated');
--    -> attendu : aucune ligne
--
-- 2) Après un cycle, le bail doit exister et être daté dans le futur :
--    select name, locked_until, holder from cron_leases;
--
-- 3) Un seul worker travaille : dans les logs, `notification_cron_cycle_complete`
--    doit apparaître une seule fois par cycle, et les autres workers émettre
--    `notification_cron_lease_held`.
