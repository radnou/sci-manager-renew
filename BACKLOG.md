# BACKLOG — GérerSCI

Backlog de remédiation issu de l'**audit externe du 2026-07-25**
(rapport complet : [`AUDIT_EXTERNE_2026-07-25.md`](./AUDIT_EXTERNE_2026-07-25.md)).

**Légende**
`✅ Fait` · `🔧 Prêt, à déployer` · `⏳ À faire` · `🚫 Bloqué (hors repo)`
🔴 = vérifié en production · ⚪ = établi par lecture de code

> Règle : aucun élément CRITICAL ne passe en `✅` tant qu'il n'est pas **déployé
> et rejoué en production**. Écrire le correctif ne suffit pas.

---

## État de la remédiation

| Finding | Sévérité | État | Bloquant go-live |
|---|---|---|---|
| C1 — Contournement du paiement | CRITICAL 🔴 | 🔧 Prêt, à déployer | Oui |
| C2 — Supabase exposé publiquement | CRITICAL 🔴 | 🚫 Bloqué (repo `vps-infra`) | Oui |
| C3 — Élévation de privilège associés | CRITICAL ⚪ | 🔧 Prêt, à déployer | Oui |
| C4 — Fondateur 990 € inachetable | CRITICAL ⚪ | ⏳ À faire | Oui |
| C5 — Déficit foncier corrompu au GET | CRITICAL ⚪ | ⏳ À faire | Oui |
| C6 — Charges non récupérables réclamées | CRITICAL ⚪ | ⏳ À faire | Oui |
| C7 — 2065 sans amortissement | CRITICAL ⚪ | ⏳ À faire | Oui |
| C8 — Aucune sauvegarde DB | CRITICAL 🔴 | ⏳ À faire | Oui |
| C9 — Cron dupliqué (emails en double) | CRITICAL ⚪ | ⏳ À faire | Oui |

---

## 🔧 Prêt à déployer — C1 / C3

### C1 — Contournement total du paiement

**Exploit reproduit en production le 2026-07-25** (compte de test, nettoyé) :
`POST /rest/v1/subscriptions {status:"active", plan_key:"pilotage"}` → `201`,
puis `POST /api/v1/scis` passe de **402 à 422** — le paywall est franchi.

Modifications :

- [x] `supabase/migrations/043_security_fix_c1_c3_rls.sql` — suppression des
      policies d'écriture utilisateur sur `subscriptions` + `REVOKE` explicite.
      L'écriture devient service_role uniquement.
- [x] `backend/app/services/subscription_service.py` — inversion de l'ordre de
      fusion (`{**row, **snapshot}`) : le catalogue serveur prime toujours sur
      la ligne DB. Défense en profondeur côté applicatif.
- [x] Bascule en service_role des écritures légitimes, sans quoi la migration
      casse l'onboarding : `services/demo_service.py` (seed + cleanup),
      `api/v1/onboarding.py` (`/complete`), `api/v1/gdpr.py` (anonymisation
      facturation + purge notifications).
- [x] Test de non-régression : `tests/test_api/test_associes_security.py`.

> ⚠️ **Piège évité** : le fallback `row.get("plan_key")` a été **conservé**
> volontairement. `stripe_price_id` n'étant pas renseigné au checkout
> (finding HIGH-10), le supprimer aurait rétrogradé **tous les clients payants
> existants** en `free` (max_scis=0, compte bloqué). Ce fallback ne redeviendra
> superflu qu'une fois HIGH-10 corrigé.

### C3 — Élévation de privilège sur les associés

Deux vecteurs : INSERT sans contrainte sur `id_sci` (s'ajouter gérant chez un
tiers) et UPDATE sans `WITH CHECK` (s'auto-promouvoir gérant).

- [x] Migration 043 — policies `associes` réservées aux rôles de gouvernance.
- [x] `backend/app/api/v1/associes.py` — helper `_require_gerant()` appliqué sur
      POST / PATCH / DELETE (le GET reste ouvert aux membres) ; `user_id` fourni
      par le client désormais ignoré ; garde-fou « dernier gérant » élargi aux
      co-gérants.
- [x] `backend/app/models/associes.py` — `role` contraint au référentiel réel,
      `user_id` retiré de `AssocieUpdate`.

> ⚠️ **Piège évité** : le référentiel comporte **4 rôles**
> (`gerant`, `co_gerant`, `associe`, `usufruitier` — cf.
> `frontend/src/lib/high-value/associes.ts`). Une première version restreignait
> à `gerant`/`associe` : la contrainte `CHECK` aurait **échoué à s'appliquer**
> sur les données de production (donc migration 043 entièrement annulée) et les
> **co-gérants auraient perdu tout droit de gestion**. La fonction
> `is_user_gerant_of_sci` couvre désormais `gerant` + `co_gerant`, et la
> contrainte est posée en `NOT VALID`.

**Tests impactés** (comportement permissif encodé dans les fixtures) :
`tests/conftest.py` (`associe-2` : `associe` → `gerant`) et
`test_associes.py::test_delete_self_row` (`extra-sci2` → `gerant`). Ces deux
ajustements préservent l'intention des tests métier ; l'absence d'habilitation
est désormais couverte par `test_associes_security.py`.

### Procédure de déploiement C1/C3

```bash
# 1. Appliquer la migration (aucun chemin de déploiement ne joue les migrations — cf. HIGH-12)
psql "$DATABASE_URL" -f supabase/migrations/043_security_fix_c1_c3_rls.sql

# 2. Vérifier l'état des policies
psql "$DATABASE_URL" -c "select policyname, cmd from pg_policies where tablename='subscriptions';"
#    attendu : uniquement subscriptions_owner_select / SELECT

# 3. Déployer le backend (les correctifs applicatifs et la migration vont ensemble)

# 4. Rejouer l'exploit avec un compte de test — doit renvoyer 401/403
curl -X POST "https://api.gerersci.fr/rest/v1/subscriptions" \
  -H "apikey: $ANON" -H "Authorization: Bearer $USER_JWT" \
  -d '{"user_id":"<self>","status":"active","plan_key":"pilotage"}'

# 5. Vérifier la non-régression du parcours : inscription → /welcome (seed démo)
#    → onboarding → /complete, puis suppression de compte RGPD.
```

- [ ] Migration appliquée en production
- [ ] Backend déployé
- [ ] Exploit rejoué → refusé
- [ ] Parcours onboarding + RGPD vérifiés
- [ ] Purger le compte de test de l'audit : `be2e22f5-a401-4d25-b2e4-67003bc85df8`

> ⚠️ **Tests non exécutés** : l'environnement d'audit est en Python 3.10, le
> projet requiert 3.12 (`datetime.UTC`). Les fichiers modifiés compilent et
> passent `pyflakes`, mais **la suite doit être lancée en local** avant
> déploiement : `cd backend && PYTHONPATH=. pytest tests/test_api/test_associes.py tests/test_api/test_associes_security.py`

---

## 🚫 Bloqué hors repo — C2

### C2 — PostgREST / GoTrue / Storage exposés publiquement

Vérifié en production : `GET /rest/v1/sci` → `200`, `/rest/v1/` renvoie le
swagger complet du schéma, `/auth/v1/settings` révèle `disable_signup:false` +
`mailer_autoconfirm:true`.

Conséquence : **RLS est la seule frontière de sécurité**. Tout le contrôle
applicatif (middleware paywall, `require_gerant_role`, quotas, validation
Pydantic, rate limiting, audit log) est contournable par appel direct. C1 en
est la démonstration.

**Ne peut pas être corrigé depuis ce dépôt** : la configuration Caddy de
production vit dans `vps-infra`. `docker/nginx.conf` est du **code mort**
(le proxy réel est Caddy, pas nginx).

> **Point de situation 2026-07-26.** La rationalisation de l'infrastructure sous
> `vps-infra` **ne ferme pas ce finding** : elle déplace les routes
> `/auth/*`, `/rest/*`, `/realtime/*`, `/storage/*`, `/functions/*` du vhost
> `api.gerersci.fr` vers `/etc/caddy/sites/gerersci.caddy` (Kong `127.0.0.1:54321`).
> L'exposition publique de PostgREST reste donc active, et avec elle la
> dépendance totale à RLS. Le correctif est une PR dans `vps-infra`.

- [ ] Dans `vps-infra`, fichier `/etc/caddy/sites/gerersci.caddy` : retirer le
      routage de `/rest/`, `/storage/`, `/realtime/` sur le vhost
      `api.gerersci.fr`, ne conserver que `/auth/`.
      Le frontend n'utilise `supabase-js` que pour l'auth (aucun `.from()`
      dans `frontend/src` — vérifié).
- [ ] Désactiver le signup public GoTrue (finding HIGH-1) — c'est le détonateur
      de C1 : n'importe qui obtient un compte confirmé instantanément.
- [ ] Vérifier après coup : `curl https://api.gerersci.fr/rest/v1/sci` → 404
- [ ] Supprimer `docker/nginx.conf` (code mort qui a induit l'audit en erreur).

> **Angle mort structurel** : tout le bord public (TLS, headers, timeouts,
> body max, rate-limit edge) échappe à la revue et à la CI de ce projet.
> À terme, rapatrier la config Caddy ici ou la soumettre à une CI dédiée.

---

## ⏳ CRITICAL restants

- [x] **C8 — Sauvegarde DB.** *Transféré à `vps-infra` le 2026-07-26.*
      Le constat d'audit reste exact pour ce dépôt : `backup-remote.sh` ciblait un
      service `db` inexistant (no-op silencieux) et `backup-db.sh` n'était appelé
      par personne. Les deux scripts ont été supprimés — la sauvegarde est
      désormais assurée par [`radnou/vps-infra`](https://github.com/radnou/vps-infra)
      (dump quotidien 03h00 UTC, push sur `main`, purge des SQL temporaires).
      - [ ] **Vérifier côté serveur** que la tâche tourne :
            `systemctl list-timers --all | grep -i backup` puis `crontab -l`
      - [ ] **Tester une restauration** sur un dump récent — jamais fait, et
            aggravé par HIGH-11 (ordre des migrations cassé → reconstruction
            incertaine). Le backup n'est un backup qu'une fois restauré.
      - [ ] Confirmer que le dump couvre bien la base Supabase de `gerersci` et
            pas seulement les configurations.
- [ ] **C9 — Cron dans chaque worker.** `--workers 2` + tâche lancée dans le
      `lifespan` sans verrou → emails et notifications en double, rejoués à
      chaque redéploiement. Sortir le cron du process web (`ENABLE_CRON` +
      conteneur dédié `--workers 1`), contrainte `UNIQUE(user_id,type,dedup_key)`
      + `pg_try_advisory_lock`.
- [ ] **C4 — Fondateur 990 € inachetable.** `mode=subscription` sur un prix
      `one_time` → 503. 25 × 990 € = 24 750 € inaccessibles, aucun test.
- [ ] **C5 — Déficit foncier corrompu.** Un `GET` fiscalité exécute un `UPDATE` :
      rafraîchir la page impute le déficit une seconde fois. Rendre
      `calculate()` pur ; imputation dans un POST « clôturer l'exercice ».
- [ ] **C6 — Charges non récupérables.** Aucun filtre `type_charge` → taxe
      foncière et travaux réclamés au locataire (décret 87-713). Risque de
      litige direct.
- [ ] **C7 — 2065 sans amortissement.** IS surévalué. *Recommandation : désactiver
      la génération 2065 tant que l'amortissement n'est pas implémenté.*

---

## ⏳ HIGH (16)

**Paiement & conformité** — H3 rattrapage webhook (client débité sans accès) ·
H4 `client_reference_id` perdu (compte dupliqué) · H5 `/welcome` réinjecte la
démo dans un compte payant · H6 rétrogradation silencieuse en `free` ·
H7 garantie 30 j calculée depuis l'inscription · H8 résiliation en 5 clics et
absente en `past_due` (art. L215-1-1, amende ≤ 75 000 €) · H9 coupure au premier
échec de paiement · H10 `stripe_price_id` jamais renseigné → MRR admin à 0.

**Sécurité & exposition** — H1 signup GoTrue ouvert + auto-confirmé 🔴 ·
H2 `/docs` + `/openapi.json` publics (147 endpoints) 🔴.

**Infra & CI** — H11 ordre des migrations cassé (`0045` avant `004`, `035`
dupliqué) + readiness gate inopérant (`curl -sf` avale le 503) + rollback
fictif · H12 migrations jamais jouées au déploiement, deux chemins divergents.

**Produit** — H13 erreurs brutes affichées (JSON/anglais/HTML nginx) ·
H14 SDK Supabase 44,5 Ko sur toutes les pages publiques · H15 biens en
soft-delete toujours comptés (loyers générés, quotas, fiscalité) ·
H16 CI : 13 specs jamais exécutées, 27 tests E2E sans `expect()`, lint non
bloquant, aucun ruff/mypy.

---

## ⏳ MEDIUM (22) — extraits prioritaires

**Chantier « exactitude fiscale »** (le plus structurant pour la crédibilité) :
bail nu 3 ans au lieu de 6 pour une SCI (MED-1) · IRL codé en dur à +2,5 %
(MED-2) · `zone_tendue` ignoré → préavis 3 mois au lieu d'1 (MED-3) · bail
mobilité proposé mais rejeté en 422 (MED-4) · plafond déficit appliqué au
niveau SCI au lieu du foyer fiscal (MED-5) · ligne CERFA 229 au lieu de 228
(MED-6) · congé bailleur mal rattaché au terme (MED-7) · surtaxe plus-value
sans décote (MED-8) · micro-foncier recommandé à tort (MED-9).

**Autres** : import CSV cassé (`NameError` → 500 systématique, MED-14) ·
quittance sans date de paiement et numérotation non idempotente (MED-12) ·
rentabilité fausse avec crédit (MED-13) · quorum AG codé à 50 % (MED-18) ·
calendrier fiscal partiellement faux, TVA absente (MED-19) ·
✅ *RGPD incomplet (MED-20) — corrigé au passage avec C1* ·
emails en clair dans les logs (MED-21) · admin sans rate-limit ni MFA (MED-22).

Liste complète et correctifs détaillés : `AUDIT_EXTERNE_2026-07-25.md`.

---

## ⏳ LOW (~20)

Contraste WCAG (261 occurrences) · modales sans restitution du focus ·
lignes de tableau non atteignables au clavier · aucune PWA · `LockedAction`
qui laisse passer l'action · monitoring mort en prod · pas de limite mémoire
sur 3 services · mots de passe Matomo par défaut · `.bak` et `.coverage`
versionnés · dépendances Python non figées · `float` au lieu de `Decimal` sur
les chemins fiscaux. Détail dans le rapport d'audit.

---

## Rotation des secrets (à trancher)

`.env` a été tracké avant le commit `8ad430d7` et **contient des secrets réels
dans l'historique git** (`sk_test_…`, `whsec_…`, `re_…`,
`SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`).

- [ ] Déterminer si le dépôt a été public ou partagé à un moment.
- [ ] Si oui : rotation de `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`,
      `STRIPE_SECRET_KEY`, `RESEND_API_KEY`.

---

## Code mort d'infrastructure — à supprimer ou réorienter (LOW)

Depuis la centralisation de la production dans `vps-infra` (Docker Compose +
Caddy), ces fichiers décrivent une architecture qui n'existe plus. Ils
s'exécutent sans erreur fatale et n'ont aucun effet, ce qui est pire qu'une
erreur : l'audit s'est appuyé sur `docker/nginx.conf` pour conclure à tort que
le proxy était nginx.

- [ ] `scripts/maintenance-on.sh` / `maintenance-off.sh` — opèrent sur un
      conteneur `gerersci_nginx` inexistant, échecs avalés par `|| true`. Le
      mécanisme réel est dans `deploy.sh` (flag `/srv/maintenance/`).
- [ ] `scripts/init-ssl.sh` — certbot standalone + `systemctl stop nginx`,
      incompatible avec l'ACME automatique de Caddy.
- [ ] `docker/nginx.conf`, `docker/nginx-init.conf`, `docker/ssl-params.conf`.
- [ ] `docs/VPS_PREPARATION_RUNBOOK.md` — décrit une architecture
      systemd + nginx + certbot entièrement remplacée. À archiver ou réécrire.
- [ ] `scripts/rollback.sh` — s'appuie sur un `.deploy-history` que rien
      n'alimente et sur des clés `image:` absentes du compose (cf. HIGH-11).

---

## Ordre d'exécution recommandé

1. **Aujourd'hui** — C8 (vérifier la sauvegarde `vps-infra` + tester une
   restauration), C2 + C1 (fermer l'exposition et déployer la migration 043),
   H1 + H2 (signup GoTrue, `/docs`).
2. **Cette semaine** — C3 (déjà prêt, déployé avec C1), C5, C6, C9, H11, H12.
3. **Ce mois** — C4, C7, chaîne de paiement (H3→H10), H15, H16.
4. **Ensuite** — chantier exactitude fiscale (MEDIUM), accessibilité, PWA.

---

*Backlog généré le 2026-07-25 à partir de l'audit externe. 9 CRITICAL,
16 HIGH, 22 MEDIUM, ~20 LOW. 8 findings vérifiés en production.*
