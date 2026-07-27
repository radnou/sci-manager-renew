# TODO — actions immédiates

Checklist opérationnelle courte. Le registre complet des 67 findings est dans
[`BACKLOG.md`](./BACKLOG.md) ; les preuves dans [`AUDIT_EXTERNE_2026-07-25.md`](./AUDIT_EXTERNE_2026-07-25.md).

---

## 📍 Emplacements canoniques de production

Source : dépôt d'infrastructure [`radnou/vps-infra`](https://github.com/radnou/vps-infra).
Rien de tout cela n'est géré depuis ce dépôt.

| Quoi | Où |
|---|---|
| Compose de production + `.env` | `/opt/vps-infra/services/gerersci/`, **symlink vers `/opt/gerersci`** — c'est bien depuis ce répertoire que tournent les conteneurs (vérifié par `docker inspect` le 2026-07-26) |
| Base de production | conteneur `supabase_db_sci-manager-renew` (stack CLI Supabase, sans label compose) |
| Reverse proxy | Caddy, `/etc/caddy/sites/gerersci.caddy` |
| Frontend | `gerersci.fr`, `www`, `app.gerersci.fr` → `127.0.0.1:14173` |
| Backend | `api.gerersci.fr` → `127.0.0.1:18000` |
| Supabase (Kong) | `api.gerersci.fr/{auth,rest,realtime,storage,functions}/*` → `127.0.0.1:54321` |
| Logs / santé | https://status.radnoumane.com (Dozzle) |
| Sauvegarde / restauration | `/opt/vps-infra/scripts/backup.sh` (03h00 UTC) et `/opt/vps-infra/scripts/restore.sh gerersci` |

Aucun conteneur ne doit écouter sur `0.0.0.0` — contrôle : `ss -tlnp | grep -v 127.0.0.1`.

---

## 🔥 Aujourd'hui

### 1. CRITICAL-8 — ROUVERT le 2026-07-27 : la sauvegarde ne conserve rien

Vérifié dans `radnou/vps-infra@9fa4791`, pas supposé. `scripts/backup.sh` dumpe
correctement `supabase_db_sci-manager-renew`, copie dans `backups/latest/`,
commite… puis **supprime les dumps** (étape 7). L'étape git ne peut pas les avoir
sauvés : `.gitignore` ignore `*.sql`, `*.sql.gz` et `backups/`. Contrôle sur
trois commits `chore(backup)` (`9db2a75`, `7c3e9be`, `09eccb9`) : **aucun dump,
uniquement des fichiers de configuration**. `INFRA_GUIDELINES.md` §4 affirme
« Dumps are pushed to GitHub » — le script ne peut pas le faire.

Trois défauts aggravants :

- `restore.sh gerersci` cherche `gerersci_supabase_*.sql.gz` alors que
  `backup.sh` écrit `supabase_db_sci-manager-renew_*.sql.gz` : **la restauration
  ne trouvera jamais de fichier**. Même décalage pour `bookrcs`.
- `2>/dev/null … || true` sans contrôle de taille : un `pg_dumpall` en échec
  produit un gzip valide de 20 octets, indiscernable d'un succès (mesuré).
- `rm -f backups/latest/*` précède la copie du nouveau dump : un échec
  silencieux détruit la copie précédente.

**Ne pas jouer la migration 043 avant d'avoir un dump vérifié hors VPS.**

**Tranché le 2026-07-27 par inspection du VPS.** Le cron `ubuntu` contient :

```
0 3 * * * /home/ubuntu/infra/scripts/backup.sh >> /var/log/vps-backup.log 2>&1
```

C'est le script qui ne garde rien. `backup-vps-infra.sh` — celui qui fonctionne —
**n'est planifié nulle part**. Constats :

| Fait | Preuve |
|---|---|
| Le bon script a cessé de tourner le 2026-07-26 | dernier dump `/opt/backups/vps-infra/db/gerersci_supabase-20260726.sql.gz` (143 K, gzip valide, 79 `CREATE TABLE`) |
| Le script planifié ne laisse rien | `/home/ubuntu/infra/backups/latest/` : `total 0` |
| Il ne s'exécute probablement même pas | `/var/log/vps-backup.log` n'existe pas et `ubuntu` ne peut pas écrire dans `/var/log` (`drwxrwxr-x root:syslog`, `touch` → Permission denied). La redirection échoue avant la commande. |
| Aucune copie hors VPS n'a jamais existé | `rclone` installé mais sans configuration (`rclone.conf` absent) : le `rclone sync` vers R2 du bon script n'a jamais rien envoyé |

- [ ] **Copier hors VPS le dernier dump valide, maintenant** :
      `scp ovh:/opt/backups/vps-infra/db/gerersci_supabase-20260726.sql.gz .`
      (un `/tmp/vps_db_dumps_2026-07-26_235239/supabase_db_sci-manager-renew_*.sql.gz`
      de 726 K, plus complet, traîne aussi sur le VPS — reliquat d'un run manuel)
- [ ] Remettre `backup-vps-infra.sh` dans le cron à la place de `backup.sh`, et
      **écrire le log ailleurs que dans `/var/log`** (ex. `/home/ubuntu/logs/`)
- [ ] Configurer `rclone` pour obtenir enfin une copie hors machine
- [ ] Corriger `restore.sh gerersci` : il cherche `gerersci_supabase_*.sql.gz`
      dans `/home/ubuntu/infra/backups/latest` alors que les dumps s'appellent
      `gerersci_supabase-2026….sql.gz` et vivent dans `/opt/backups/vps-infra/db/`
      — mauvais répertoire **et** mauvais motif
- [ ] Dump manuel immédiat, copié hors du VPS, et vérifié non vide :
      ```bash
      docker exec -e PGPASSWORD=postgres supabase_db_sci-manager-renew \
        pg_dumpall -U supabase_admin | gzip > gerersci_$(date +%F).sql.gz
      zcat gerersci_$(date +%F).sql.gz | grep -c "CREATE TABLE"   # doit être ≥ 27
      ```
- [ ] **Jouer une restauration** vers une base jetable et compter les lignes.
      Jamais fait. Aggravé par HIGH-11 : `0045_`/`0046_` trient avant `004_` et
      `035` est dupliqué, donc une reconstruction de schéma part dans le désordre.

### 2. Déployer le correctif C1/C3
Le contournement de paiement est **actif en production**.

- [ ] `psql "$DATABASE_URL" -f supabase/migrations/043_security_fix_c1_c3_rls.sql`
- [ ] Déployer le backend (migration + patches applicatifs vont ensemble)
- [ ] Rejouer l'exploit → doit renvoyer 401/403 :
      ```bash
      curl -X POST "https://api.gerersci.fr/rest/v1/subscriptions" \
        -H "apikey: $ANON" -H "Authorization: Bearer $USER_JWT" \
        -d '{"user_id":"<self>","status":"active","plan_key":"pilotage"}'
      ```
- [ ] Vérifier la non-régression : inscription → `/welcome` → onboarding → `/complete`
- [ ] Vérifier la suppression de compte RGPD

### 3. Fermer l'exposition Supabase (CRITICAL-2 + HIGH-1/HIGH-2)
**Dans le dépôt `vps-infra`**, pas ici. La centralisation de l'infrastructure
n'a pas fermé cette exposition : elle a déplacé les routes dans
`/etc/caddy/sites/gerersci.caddy`.

- [ ] Dans `/etc/caddy/sites/gerersci.caddy`, bloc `api.gerersci.fr` : retirer
      `/rest/*`, `/storage/*`, `/realtime/*` (et `/functions/*` s'il n'est pas
      utilisé), ne conserver que `/auth/*` vers Kong `127.0.0.1:54321`
- [ ] Désactiver le signup public GoTrue (`disable_signup: true`)
- [ ] Désactiver `/docs`, `/redoc`, `/openapi.json` en production
- [ ] Vérifier : `curl -o /dev/null -w "%{http_code}" https://api.gerersci.fr/rest/v1/sci` → 404
      et que le magic link fonctionne toujours (`/auth/*` doit rester ouvert)

### 4. Nettoyer les conteneurs orphelins de monitoring

Tranché le 2026-07-26 : `docker inspect` sur le VPS montre que les conteneurs en
service viennent de `/opt/gerersci/docker-compose.yml`, désormais symlinké depuis
`/opt/vps-infra/services/gerersci`. La CI vise donc le bon répertoire (commit
`3b1c9c5` ajoute le chemin canonique avec repli).

Effet de bord constaté : `gerersci_grafana` et `gerersci_loki` **tournent encore**
alors que le commit `7274a0e` les a retirés du compose principal — ce sont des
orphelins d'une révision antérieure, que `docker compose up -d` ne supprime pas
sans `--remove-orphans`. Ils consomment de la mémoire sans rien collecter (aucun
agent d'ingestion dans le dépôt).

- [ ] `docker compose -f /opt/gerersci/docker-compose.yml up -d --remove-orphans`
      puis vérifier : `docker ps --filter name=gerersci`
- [ ] Confirmer que `matomo`, `matomo-db` et `uptime-kuma` (passés en
      `profiles: ["disabled"]`) ne tournent pas non plus

### 5. Nettoyage
- [ ] Purger le compte de test de l'audit : `be2e22f5-a401-4d25-b2e4-67003bc85df8`
- [ ] `stripe login` sur le compte **C** (`acct_1SFrY0ApRgYAyPDH`) puis
      `stripe prices list --live` → résout le « produits Stripe disparus »
      (la prod est saine : `/health/ready` renvoie `stripe.mode: live`, 4 prix validés)

---

## ✅ Suite de tests — exécutée le 2026-07-26

`PYTHONPATH=. pytest` est **verte** (venv `backend/.venv`, Python 3.11 — 3.12
n'était pas requis, `datetime.UTC` existe depuis 3.11).

Le commit d'audit introduisait 12 régressions, toutes corrigées :

| Test | Cause | Correctif |
|---|---|---|
| `test_scis::test_*_requires_gerant` (2) | le fixture `associe-2` avait été passé à `gerant`, supprimant la seule base négative du projet | fixture remis à `associe` ; les tests concernés promeuvent localement |
| `test_associes::test_*_generic_exception` (3) | patchaient `_get_user_sci_ids`, que create/update/delete n'appellent plus | patch sur `_require_gerant` |
| `test_associes::test_delete_single_gerant_blocked` | scénario devenu inatteignable (l'appelant se rétrogradait avant l'appel) | le gérant unique supprime sa propre ligne |
| `test_plan_enforcement` (6) | fixtures injectant `max_scis`/`max_biens` dans la ligne DB — précisément ce que C1 neutralise | quotas alignés sur `PLAN_CATALOG` ; le cas `upgrade_required` patche le catalogue |

**Trois régressions de production trouvées dans le correctif lui-même :**

- `demo.py` seed/cleanup écrivait avec le JWT utilisateur → la policy
  `associes_member_insert` de la 043 rejette l'insertion du gérant sur une SCI
  neuve : **tout le parcours demo-first aurait cassé** dès l'application de la
  migration. Bascule en service_role + test `test_demo_rls_identity.py`.
- `gdpr.py` supprimait la ligne associé des SCI partagées avec le JWT
  utilisateur → suppression silencieusement ignorée pour un non-gérant
  (non-conformité RGPD). Bascule sur `erase_client`.
- `subscription_service` : `resolve_plan_key_from_price_id` renvoie `FREE` (et
  non `None`) pour un `price_id` inconnu. Placé avant le fallback `plan_key`,
  tout client payant portant un prix historique était rétrogradé à chaque
  lecture. Ce `FREE` est désormais traité comme non concluant.

Reste non vérifié en conditions réelles : la 043 elle-même (aucune base de test
avec RLS). Les invariants ci-dessus reposent sur la lecture des policies.

---

## 📅 Cette semaine

- [ ] **C9** — sortir le cron des workers uvicorn (emails en double chez les clients)
- [ ] **C5** — fiscalité : le `GET` ne doit plus écrire (déficit foncier corrompu à chaque affichage)
- [ ] **C6** — filtrer les charges récupérables (réclamations illégales aux locataires)
- [ ] **HIGH-11** — corriger le gate de readiness (`curl -sf` avale le 503) + ordre des migrations (`0045`/`0046`/`035`)
- [ ] **HIGH-12** — jouer les migrations dans le déploiement
- [ ] **MED-14** — import CSV cassé (`NameError` → 500 systématique, correctif = 1 ligne)

## 📅 Ce mois

- [ ] **C4** — Fondateur 990 € inachetable (24 750 € bloqués)
- [ ] **C7** — désactiver ou corriger la 2065 (IS surévalué, pas d'amortissement)
- [ ] **H3→H10** — chaîne de paiement : rattrapage webhook, garantie 30 j, résiliation 3 clics, `past_due`
- [ ] **HIGH-15** — filtre `deleted_at` sur ~20 requêtes
- [ ] **HIGH-16** — CI : activer `test:unit`, ruff, mypy

## 🔐 À trancher

- [ ] `.env` a été tracké avant le commit `8ad430d7` et contient des secrets réels
      dans l'historique. Le dépôt a-t-il été public/partagé ?
      Si oui → rotation de `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`,
      `STRIPE_SECRET_KEY`, `RESEND_API_KEY`.
