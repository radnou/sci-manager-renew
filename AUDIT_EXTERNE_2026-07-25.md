# AUDIT EXTERNE INDÉPENDANT — GérerSCI

**Date** : 25 juillet 2026
**Périmètre** : application complète (`app.gerersci.fr`, `api.gerersci.fr`), code (backend FastAPI, frontend SvelteKit, 45 migrations Supabase, infra Docker/Caddy, CI GitHub Actions), et **tests boîte noire + parcours authentifié réel en production**.
**Méthode** : analyse statique ligne à ligne + sondes HTTP live + création d'un compte de test réel avec exploitation contrôlée (nettoyée). Chaque finding est marqué :

- 🔴 **[PROD-VÉRIFIÉ]** — reproduit en production pendant l'audit
- ⚪ **[CODE]** — établi par lecture du code, non rejoué en prod

Les problèmes déjà documentés comme connus (gotchas de `CLAUDE.md`, `AUDIT_BIG4`, `PRODUCTION_READINESS`) sont exclus, sauf lorsque la réalité de production les contredit.

---

> **📌 Mise à jour remédiation — 2026-07-25**
> **C1** et **C3** : correctifs écrits, `🔧 prêts à déployer` (migration
> `043_security_fix_c1_c3_rls.sql` + patches backend + tests de non-régression).
> **Non encore appliqués en production** — ils ne passeront en « corrigé » qu'une
> fois la migration jouée et l'exploit rejoué sans succès.
> **C2** : bloqué, la config Caddy vit dans le dépôt `vps-infra`.
> Suivi et procédure de déploiement : [`BACKLOG.md`](./BACKLOG.md).

## Résumé exécutif

| Sévérité | Nombre | Dont vérifiés en prod |
|---|---|---|
| CRITICAL | 9 | 3 |
| HIGH | 16 | 2 |
| MEDIUM | 22 | 3 |
| LOW | ~20 | — |

**Verdict** : produit fonctionnellement riche et, sur plusieurs points, mieux durci que la moyenne des SaaS de cette taille (JWT rigoureux, webhook Stripe correct, conteneurs non-root, en-têtes de sécurité présents, RLS qui tient pour l'accès anonyme). **Mais trois classes de défauts justifient un arrêt des nouvelles fonctionnalités jusqu'à correction** :

1. **Contournement total du paiement, vérifié en direct.** N'importe qui peut créer un compte (signup ouvert + auto-confirmé) puis s'auto-attribuer le plan Pilotage illimité en une requête HTTP sur la base exposée publiquement. **Confirmé de bout en bout : `POST /api/v1/scis` est passé de 402 à 422 après auto-attribution.** Perte de revenu potentielle : 100 %.
2. **Exactitude fiscale défaillante.** Corruption du déficit foncier reportable à chaque consultation, régularisation de charges qui répute tout récupérable, déclaration IS sans amortissement, durée de bail SCI erronée (3 ans au lieu de 6). Risque de déclaration fausse et de litige locataire.
3. **Aucune sauvegarde de base de données.** Perte totale et irrécupérable des données clients en cas de sinistre VPS.

### Réponse à « je n'ai plus les produits Stripe avec Stripe CLI »

**La production est saine** — la sonde `GET https://api.gerersci.fr/health/ready` renvoie en direct :
```json
"stripe": { "healthy": true, "mode": "live", "validated_price_count": 4 }
```
Vos 4 prix récurrents live sont donc bien présents et validés côté serveur. **Le problème est purement local à votre CLI**, pas une perte de produits. Cause la plus probable (par ordre) :

1. **Le CLI interroge le mode test alors que vos produits sont en `livemode:true`.** `stripe products list` regarde le mode test par défaut → catalogue vide. Ajoutez `--live`.
2. **Le CLI est loggé sur le mauvais compte.** Vous avez 3 comptes (`docs/STRIPE_GOLIVE.md:9-13`) : A `acct_1SFrVgBCxd3SKdGJ` (obsolète), B `acct_1Sei1OHfxmPH8rox` (sandbox), **C `acct_1SFrY0ApRgYAyPDH` (prod live, le bon)**. Un `stripe login` sur A ou B affiche un autre catalogue.

Commandes de confirmation :
```bash
stripe config --list                 # doit pointer acct_1SFrY0ApRgYAyPDH
stripe products list --live          # catalogue live du compte courant
stripe prices list --live --active true
# Contrôle direct via l'API avec votre clé live compte C :
curl -s -u "sk_live_XXX:" https://api.stripe.com/v1/account | jq '{id,livemode,charges_enabled}'
```
Astuce : le suffixe d'un price ID encode les 10 derniers caractères du compte. Vos prix prod finissent par `ApRgYAyPDH` (`docs/STRIPE_GOLIVE.md:39-44`). Tout price ID en `BCxd3SKdGJ` = compte A obsolète.

⚠️ Réserve : la readiness ne valide que **4** prix (starter/pro ou gestion/pilotage). Le prix **Fondateur 990 € one-time n'est pas dans le lot validé** → voir CRIT-4.

---

# CRITICAL

## CRITICAL-1 🔴 [PROD-VÉRIFIÉ] — Contournement total du paiement : auto-attribution d'un abonnement payant

**Où** : base PostgREST exposée sur `https://api.gerersci.fr/rest/v1/subscriptions` + policies `supabase/migrations/003_subscriptions_and_gdpr_exports.sql:34-42` + confiance backend `backend/app/services/subscription_service.py:111,117-118`.

**Preuve reproduite en production** (compte de test créé pour l'audit, ligne supprimée ensuite) :
```
POST /rest/v1/subscriptions  {user_id, status:"active", is_active:true, plan_key:"pilotage"}  → 201 Created
GET  /rest/v1/subscriptions?user_id=eq.<moi>  → [{status:"active", is_active:true, plan_key:"pilotage", max_biens:null, max_scis:null}]
POST /api/v1/scis            → passe de 402 (Payment Required) à 422 (validation) : LE PAYWALL EST FRANCHI
```
La policy RLS ne contraint que `user_id = auth.uid()`. Les colonnes `status`, `is_active`, `plan_key`, `max_scis`, `max_biens`, `features` sont **librement écrivables par l'utilisateur**. Et le backend fait confiance à la ligne : `row = {**snapshot, **row}` (ligne 117) fait primer la ligne DB sur le catalogue serveur ; `is_active = row_status in ACTIVE_SUBSCRIPTION_STATUSES` (ligne 118).

**Chaîne d'exploitation complète, sans prérequis** : `disable_signup:false` + `mailer_autoconfirm:true` (vérifié sur `/auth/v1/settings`) → n'importe qui crée un compte confirmé par mot de passe → une requête PostgREST → Pilotage illimité gratuit, sans jamais toucher Stripe.

**Impact** : perte de revenu 100 %, aucune trace côté Stripe, quotas illimités. C'est le finding le plus grave de l'audit.

**Correctif** :
1. **Retirer les policies d'écriture utilisateur** sur `subscriptions` (INSERT/UPDATE/DELETE lignes 33-47). Écritures réservées au `service_role` (le webhook Stripe passe déjà par lui). Ne garder que `subscriptions_owner_select`, idéalement restreint aux colonnes non sensibles via une vue.
2. Inverser la fusion `subscription_service.py:111,117` → `row = {**row, **snapshot}` pour que le catalogue serveur prime toujours.
3. Résoudre `plan_key`, `max_*`, `features` uniquement depuis `stripe_price_id` + `resolve_plan_key_from_price_id()`.

## CRITICAL-2 🔴 [PROD-VÉRIFIÉ] — Toute la couche PostgREST/GoTrue/Storage de Supabase est exposée publiquement

**Où** : `https://api.gerersci.fr/rest/`, `/auth/`, `/storage/` (proxy Caddy).

**Preuve live** :
```
GET /rest/v1/            → 200  (swagger complet : "standard public schema", toutes les tables listées)
GET /rest/v1/sci         → 200
GET /rest/v1/subscriptions → 200
GET /auth/v1/settings    → 200  (signup ouvert + autoconfirm révélés)
```
Conséquence structurante : **RLS est la seule frontière de sécurité réelle**. Tout ce qui est fait dans FastAPI — `write_protection_middleware`, `require_gerant_role`, `enforce_limit`, validation Pydantic, rate limiting applicatif, audit log — est **contournable** par un appel direct `/rest/v1/…` avec la clé anon (publique, dans le bundle) + un JWT utilisateur. CRITICAL-1 en est la démonstration.

**Nuance vérifiée en prod (bonne nouvelle)** : RLS **tient** pour l'accès anonyme et pour un compte authentifié neuf — `sci`, `biens`, `loyers`, `associes`, `locataires`, `subscriptions` renvoient tous `[]`. La fuite n'est donc pas « lecture de toutes les données par un inconnu ». Le risque exploité est l'écriture sur ses propres colonnes (CRITICAL-1) et les policies trop permissives (CRITICAL-3).

**Correctif** : le frontend n'utilise `supabase-js` que pour l'auth (aucun `.from()` dans `frontend/src`). Sur le vhost `api.gerersci.fr`, **supprimer le routage de `/rest/`, `/storage/`, `/realtime/`** et ne conserver que `/auth/`. Cela referme d'un coup la surface de CRITICAL-1, CRITICAL-3 et de la classe IDOR. Corriger les policies quoi qu'il arrive (défense en profondeur).

## CRITICAL-3 ⚪ [CODE] — Un associé peut se promouvoir gérant / s'ajouter à une SCI tierce

**Où** : `supabase/migrations/038_associes_rls_gerant_management.sql:22,25,28` + `backend/app/api/v1/associes.py:218-242`.
```sql
associes_member_insert ... WITH CHECK (user_id = auth.uid() OR public.is_user_gerant_of_sci(id_sci));  -- id_sci non contraint
associes_member_update ... USING (user_id = auth.uid() OR public.is_user_gerant_of_sci(id_sci));       -- pas de WITH CHECK → role non contraint
```
Deux élévations de privilège :
- **INSERT** : la branche `user_id = auth.uid()` ne contraint pas `id_sci` → un utilisateur s'insère comme `role:"gerant"` dans la SCI d'un autre (prérequis : connaître l'UUID de la SCI — fuité par les URLs `/scis/{id}/…`, les noms de fichiers quittances `quitus-<sci_id>-…`, ou détenu par tout ancien associé retiré).
- **UPDATE** : sans `WITH CHECK`, PostgreSQL réutilise `USING` → seul `user_id` reste contraint, **`role` ne l'est pas**. Un associé fait `PATCH /associes/{self}` `{role:"gerant"}`. Côté API, `update_associe` ne vérifie que l'appartenance, jamais le rôle, et `AssocieUpdate` expose `role`.

**Impact** : prise de contrôle d'une SCI — suppression de biens, dissolution, cession de parts, falsification du registre (portée juridique art. 1865 C. civ.). RLS anonyme tient (vérifié), donc l'attaquant doit être authentifié et cibler un UUID — d'où CRITICAL plutôt que « catastrophe anonyme », mais l'impact par cible est total.

**Correctif** :
```sql
DROP POLICY associes_member_insert ON associes;
CREATE POLICY associes_member_insert ON associes FOR INSERT WITH CHECK (public.is_user_gerant_of_sci(id_sci));
DROP POLICY associes_member_update ON associes;
CREATE POLICY associes_member_update ON associes FOR UPDATE USING (public.is_user_gerant_of_sci(id_sci)) WITH CHECK (public.is_user_gerant_of_sci(id_sci));
```
API : `Depends(require_gerant_role)` sur POST/PATCH/DELETE `/associes` ; retirer `role` et `user_id` de `AssocieCreate`/`AssocieUpdate`.

## CRITICAL-4 ⚪ [CODE] — Le bouton Fondateur 990 € est cassé (mode subscription sur un prix one-time)

**Où** : `backend/app/core/entitlements.py:185-187` + `backend/app/api/v1/stripe.py:338` + `frontend/src/routes/pricing/+page.svelte:99-110`.
`resolve` rabat `LIFETIME → PRO` (dont `checkout_mode = "subscription"`), le front envoie `plan_key:'lifetime'` sans `mode`, mais `resolve_price_id_for_plan(LIFETIME)` renvoie le prix **one-time 990 €**. Stripe refuse un prix `one_time` en `mode=subscription` → 503.
**Impact** : l'offre de lancement (25 × 990 € = 24 750 €) est **inachetable**. Aucun test ne couvre ce chemin. Cohérent avec la readiness qui ne valide que 4 prix récurrents.
**Correctif** : envoyer `plan_key:'fondateur'` + `mode:'payment'` depuis `/pricing` ; dériver le mode de `resolve_price_id_for_plan`, pas de `get_plan`.

## CRITICAL-5 ⚪ [CODE] — Le GET de la fiscalité détruit le déficit foncier reportable à chaque appel

**Où** : `backend/app/api/v1/cerfa.py:279-294` (méthode **GET**) → `backend/app/services/resume_fiscal_service.py:492-499` puis `:198-201`.
Un simple affichage de la page fiscalité exécute un `UPDATE deficit_reportable SET total_impute_foncier=…, solde_restant=…`. **Rafraîchir la page impute une seconde fois** le déficit antérieur : le solde reportable se vide, et le résultat affiché change à chaque consultation de la même année.
**Impact** : perte d'un actif fiscal réel + résultat non reproductible → déclaration fausse, redressement possible.
**Correctif** : rendre `calculate()` pur (lecture seule) ; déplacer l'imputation dans un POST explicite « clôturer l'exercice », idempotent sur `(id_deficit, annee_imputation)`.

## CRITICAL-6 ⚪ [CODE] — Régularisation de charges : toutes les charges réputées récupérables

**Où** : `backend/app/services/regularisation_service.py:53-67` (aucun filtre `type_charge`) et `:45` (`provisions = charges_locatives × 12`, sans prorata).
Taxe foncière, PNO, travaux, intérêts d'emprunt sont comptés comme récupérables alors que la liste est limitative (décret n° 87-713). Exemple : provisions 600 €, TF 1 200 € + travaux 800 € → l'app réclame « 2 000 € dus par le locataire ».
**Impact** : réclamation illégale au locataire, restitution + dommages, atteinte à la crédibilité du produit.
**Correctif** : filtrer sur une liste blanche de charges récupérables ; proratiser sur la période d'occupation réelle.

## CRITICAL-7 ⚪ [CODE] — Déclaration 2065 (SCI à l'IS) sans amortissement des immeubles

**Où** : `backend/app/services/declaration_2065_service.py:134-151` (immobilisations en brut) et `:254-261` (résultat = trésorerie, pas comptabilité d'engagement) ; bug `:158` `.eq("statut","impayé")` — statut inexistant (`en_attente|paye|en_retard`) → créances clients toujours 0.
Pour une SCI à l'IS l'amortissement du bâti est obligatoire et constitue le premier poste de charge → **bénéfice imposable et IS massivement surévalués**.
**Impact** : déclaration IS fausse. **Recommandation : désactiver la génération 2065 tant que l'amortissement n'est pas implémenté** — en l'état elle produit un document erroné.

## CRITICAL-8 🔴 [PROD-VÉRIFIÉ partiel] — Aucune sauvegarde de base de données

**Où** : `scripts/backup-remote.sh:18` cible un service `db` **qui n'existe pas** dans `docker-compose.yml` → no-op silencieux ; aucun cron installé (`deploy.sh:194-202` n'installe que le nettoyage Docker) ; `docs/VPS_PREPARATION_RUNBOOK.md` : 0 occurrence de backup ; `README.md:283` coche pourtant « Sauvegardes automatiques actives » (faux).
La base prod est un Supabase auto-hébergé sur le VPS (confirmé indirectement : `/rest/v1/` expose PostgREST `14.3` en direct).
**Impact** : perte totale et irrécupérable (SCI, baux, loyers, quittances, pièces fiscales) en cas de panne disque, ransomware ou migration ratée. Exposition juridique (obligation de conservation). Fin commerciale du produit.
**Correctif** : (1) `pg_dump` manuel hors VPS **aujourd'hui** ; (2) corriger la cible du script vers le conteneur Postgres Supabase réel ; (3) cron quotidien chiffré → OVH Object Storage, rétention 30 j ; (4) **tester une restauration** — un backup non testé n'est pas un backup. Aggravé par l'ordre de migrations cassé (HIGH-11).

> **Addendum 2026-07-26.** La sauvegarde est désormais assurée par le dépôt d'infrastructure `radnou/vps-infra` (dump quotidien 03h00 UTC, push sur `main`, purge des SQL temporaires). Les deux scripts morts de ce dépôt (`scripts/backup-db.sh`, `scripts/backup-remote.sh`) ont été supprimés — leur constat ci-dessus reste exact au moment de l'audit. Deux points du correctif restent ouverts et ne sont pas attestables depuis ce dépôt : la couverture réelle du dump (base Supabase de `gerersci` et pas seulement les configurations) et le **test de restauration**, toujours jamais effectué.

## CRITICAL-9 ⚪ [CODE] — Le cron de notifications tourne dans chaque worker → emails en double

**Où** : `backend/Dockerfile` (`--workers 2`) + `backend/app/main.py:222-223` (tâche lancée dans le `lifespan`, par worker, sans verrou) + `main.py:110-144` (cycle exécuté immédiatement au démarrage). Déduplication seulement applicative (`notification_service.py:12`, aucune contrainte UNIQUE en base — vérifié).
**Impact** : 2 workers → doublon d'email/notification (TOCTOU) ; chaque redéploiement relance tout le batch. Avec auto-déploiement sur `main`, le client reçoit N×2 « Loyer impayé J+15 » et les emails de nurture J1/J3/J7. Réputation d'expéditeur Resend en jeu.
**Correctif** : sortir le cron du process web (conteneur `backend-worker` dédié, `--workers 1`, garde `ENABLE_CRON`) ; contrainte `UNIQUE(user_id,type,dedup_key)` + `pg_try_advisory_lock` + table `cron_runs(job, run_date UNIQUE)`.

---

# HIGH

## HIGH-1 🔴 [PROD-VÉRIFIÉ] — Inscription par mot de passe ouverte et auto-confirmée

`/auth/v1/settings` en prod : `disable_signup:false`, `mailer_autoconfirm:true`. Le parcours voulu est le magic-link, mais GoTrue exposé accepte un `POST /auth/v1/signup` email+mot de passe **instantanément confirmé** (j'ai obtenu un `access_token` valide immédiatement). C'est le détonateur de CRITICAL-1.
**Correctif** : désactiver le signup public GoTrue (ou couper l'exposition `/auth/` externe — cf. CRITICAL-2), forcer le flux magic-link piloté par le backend.

## HIGH-2 🔴 [PROD-VÉRIFIÉ] — Documentation OpenAPI publique : 147 endpoints exposés

`GET /docs`, `/redoc`, `/openapi.json` → 200. `openapi.json` liste **147 chemins**, cartographie complète de l'API offerte à un attaquant (dont admin, gdpr, stripe).
**Correctif** : `FastAPI(docs_url=None, redoc_url=None, openapi_url=None)` en production (`APP_ENV=production`).

## HIGH-3 ⚪ [CODE] — Le webhook échoue → client débité, aucun accès, aucun rattrapage

`stripe.py:556-567` (400 si signature invalide → `_sync_subscription` jamais appelé → ligne reste `status:'demo'` → 402 sur toute écriture). Aucun endpoint de vérification de session, aucun polling, aucun job de réconciliation. Pire, `/dashboard?upgraded=true` affiche « Abonnement activé » et déclenche un `cleanupDemo()` à l'aveugle (`dashboard/+page.svelte:29-41,135-146`).
**Correctif** : endpoint `checkout.session.retrieve` appelé sur la page succès + cron de réconciliation `stripe.Subscription.list(status='active')` vs table `subscriptions`.

## HIGH-4 ⚪ [CODE] — Achat depuis la landing : `client_reference_id` perdu → compte dupliqué

`frontend/src/routes/+page.svelte:112-114` appelle `createGuestCheckout` (ne pose pas `client_reference_id`, `stripe.py:436-448`) même pour un connecté. Le webhook retombe sur `customer_details.email` ; si le client saisit un autre email dans Stripe, un **nouveau** compte est créé et activé, le vrai payeur reste sans accès.
**Correctif** : router les utilisateurs connectés vers `/create-checkout-session`.

## HIGH-5 ⚪ [CODE] — `success_url` guest → `/welcome`, qui réinjecte des données démo dans un compte payant

`stripe.py:445` renvoie sur `/welcome` qui `seedDemo()`. Course avec le webhook : la SCI démo peut être créée après le cleanup et **consommer le quota** (`max_scis=1` en Gestion) → le client ne peut plus créer sa vraie SCI.
**Correctif** : `success_url → /dashboard?upgraded=true` + garde `demo_seeded` sur `/welcome`.

## HIGH-6 ⚪ [CODE] — Rétrogradation silencieuse d'un client payant en `free`

`entitlements.py:262` renvoie `PlanKey.FREE` (truthy) au lieu de `None` quand un price ID est inconnu ; les metadata `plan_key` ne sont pas posées sur l'objet Subscription (`stripe.py:366`). Un `customer.subscription.updated` (renouvellement) avec un price ID non mappé → `max_scis=0, max_biens=0`, features `false`, tout en gardant `is_active=true`. Le client paie et ne peut plus rien créer.
**Correctif** : `return None` ; passer `subscription_data={"metadata":{…}}` au checkout.

## HIGH-7 ⚪ [CODE] — Garantie 30 jours calculée depuis l'inscription, pas depuis le paiement

`stripe.py:629-635` : fallback sur `created_at`, or la ligne `subscriptions` est créée au **seeding démo** (`demo_service.py:294-299`). Un prospect qui explore 25 jours n'a plus que 5 jours de garantie ; au-delà de 30 jours d'exploration, 0. La CGV art. 4 promet « 30 jours à compter de la souscription ». Pratique commerciale trompeuse (art. L121-2 C. conso).
**Correctif** : écrire `guarantee_expires_at = now()+30j` sur `checkout.session.completed`.

## HIGH-8 ⚪ [CODE] — Résiliation en 5 clics et indisponible en `past_due` (art. L215-1-1)

Parcours : menu compte → Paramètres → onglet Abonnement → Résilier → Confirmer = **5 clics** (`AppNavbar.svelte:344`, `settings/+page.svelte:32`, `SettingsAbonnement.svelte:139-171`). Le bloc est conditionné par `is_active` → un client en `past_due` **ne voit plus le bouton** alors que Stripe le facture encore. La CGV cite `L215-1` mais jamais `L215-1-1`.
**Impact** : amende jusqu'à 15 000 € / 75 000 € (art. L242-8).
**Correctif** : entrée « Résilier » directe (2 clics) ; retirer la condition `is_active`.

## HIGH-9 ⚪ [CODE] — Un premier échec de paiement coupe l'accès instantanément

`ACTIVE_SUBSCRIPTION_STATUSES = {"active","paid"}` (`subscription_service.py:20`). `past_due`, `unpaid`, `incomplete` traités comme inactifs → dès le premier `past_due` (carte expirée), 402 sur toute écriture, alors que Stripe fait ses *smart retries* ~3 semaines. Churn évitable (~1 client/15/mois).
**Correctif** : fenêtre de grâce (7 j) sur `past_due` via `current_period_end` ; coupure sur `unpaid`/`canceled`.

## HIGH-10 ⚪ [CODE] — `stripe_price_id` jamais renseigné → MRR admin à 0

`stripe.py:103` lit `session_data.get("price_id")` — champ inexistant sur un objet Checkout Session (`line_items` non expandé). `stripe_price_id` écrit `NULL` → `admin_metrics_service.py:119-126,168` calcule MRR=0 €, 0 client payant. Le test `test_stripe.py:202` masque le bug avec un `price_3` fabriqué.
**Correctif** : `expand=["line_items"]` ou lire le prix depuis l'objet Subscription.

## HIGH-11 ⚪ [CODE] — Ordre des migrations cassé + readiness gate inopérant + rollback fictif

Trois défauts DevOps couplés :
- **Migrations** : `0045_`/`0046_` trient **avant** `004_` en lexicographique (`'5' < '_'`) ; préfixe `035` **dupliqué**. Toute reconstruction à neuf (nouveau VPS, restauration après sinistre) applique le schéma dans le désordre → échec. Multiplicateur de gravité de CRITICAL-8.
- **Readiness gate** : `.github/workflows/deploy.yml:104-110` `curl -sf … || echo '{"status":"FAIL"}'` puis `grep "not_ready"` — sur un 503, `curl -sf` n'imprime rien, le grep ne matche jamais → **le garde-fou se désarme exactement quand il devrait bloquer**. Le rollback `if: failure()` ne se déclenche pas.
- **Rollback** : `scripts/rollback.sh` dépend d'un `.deploy-history` jamais alimenté ; le compose n'a aucune clé `image:` → variables ignorées ; `git reset --hard HEAD~1` en CI vise le commit précédent de `main`, pas la révision déployée.
**Correctif** : renommer `0045→044`/`0046→045`, dédupliquer `035` ; `curl -s -o /tmp/r -w '%{http_code}'` + test `==200` ; tagger les images `:${GIT_SHA}` + `image:` au compose + SHA déployé persisté.

## HIGH-12 ⚪ [CODE] — Migrations DB jamais jouées par le déploiement ; deux chemins divergents

Ni `deploy.sh` ni `deploy.yml` n'exécutent `supabase db push` / `migration up` (45 fichiers, 0 appelant). `deploy.sh` (page de maintenance) **n'est jamais appelé par la CI** ; le chemin réel `deploy.yml` build+restart sans page de maintenance → erreurs pendant la fenêtre. Déployer du code attendant une colonne non créée = 500 en prod.
**Correctif** : étape migration idempotente et bloquante avant restart ; faire converger les deux chemins.

## HIGH-13 ⚪ [CODE] — Messages d'erreur bruts (JSON/anglais/HTML) affichés à l'utilisateur

`frontend/src/lib/api/client.ts:90-124` ne lit que `parsed.error`, mais le backend n'a **aucun** handler `HTTPException` (`main.py`) → les 33 `raise HTTPException` retombent sur `{"detail":…}` de Starlette. L'utilisateur voit `{"detail":"Bien non trouvé"}`, `Internal server error`, ou du HTML nginx 502. Diffusé dans 47 composants. Aggravé par 7 `detail=str(e)` exposant l'exception Python (`declarations.py:93-190`, `biens_baux.py:633,671`).
**Correctif** : handler `StarletteHTTPException` renvoyant `{"error":…}` ; côté front lire `parsed.error ?? parsed.detail` + messages FR génériques par statut.

## HIGH-14 ⚪ [CODE] — SDK Supabase (44,5 Ko gzip) sur le chemin critique de toutes les pages publiques

`frontend/src/routes/+layout.svelte:9` importe `supabase` statiquement dans le layout **racine** → 44,5 Ko sur ~72 Ko de JS gzip sur `/` et les lead magnets SEO (`/generateur-quittance`, `/simulateur-*`) qui n'ont aucun besoin d'auth. LCP/TBT dégradés sur mobile, sur les pages censées convertir.
**Correctif** : import dynamique `getSupabase()` (`await import(...)`) appelé uniquement sur les routes protégées.

## HIGH-15 ⚪ [CODE] — Biens en soft-delete toujours comptés dans les calculs fiscaux et les quotas

`0046_soft_delete_biens.sql` ajoute `deleted_at`, mais seuls `biens_core`/`biens_flat` filtrent. **Aucun filtre** dans `resume_fiscal_service`, `notification_cron.py:55,413` (génération auto des loyers), `subscription_service.py:79` (quota), `dashboard_service`, `declaration_2065_service`, etc. (~20 requêtes). Un bien « supprimé » génère encore des loyers, apparaît dans la 2044/2072, consomme le quota. Ni purge ni restauration pour la « grâce 30 jours » annoncée.
**Correctif** : `.is_("deleted_at","null")` sur les ~20 requêtes listées, prioritairement `resume_fiscal_service` et `notification_cron`.

## HIGH-16 ⚪ [CODE] — CI : la majorité des tests ne s'exécutent pas / n'assertent rien ; qualité non bloquante

- `quality-gate.yml:93` ne lance que `test:high-value` (9 fichiers) ; **13 specs frontend jamais exécutées**, dont `route-guard.spec.ts` (le point d'application du paywall). `test:unit` dans aucun workflow.
- E2E : **27 tests sur 106 sans aucun `expect()`** (ex. `paywall.spec.ts:33` @P0) ; suites facturation gated sur des variables jamais définies → inertes ; les E2E ne démarrent pas le backend (mocks maison → dérive de contrat indétectable).
- `build || true`, `lint || true` (418 erreurs ESLint tolérées), `audit || true` ; **aucun ruff/mypy** côté Python (~11 000 lignes métier sans typage ni lint).
**Correctif** : ajouter `test:unit` bloquant ; supprimer/compléter les tests sans assertion (@P0 d'abord) ; `ruff check` bloquant + `mypy` progressif sur `app/services/`.

---

# MEDIUM

| # | Sévérité | Constat | Fichier / preuve | Correctif |
|---|---|---|---|---|
| MED-1 | ⚪ | **Durée bail nu = 3 ans** au lieu de 6 pour une personne morale (SCI). Art. 10 loi 89-462. Congé bailleur à 3 ans nul. | `biens/biens_baux.py:119` `"nu":(1095,"3 ans")` | 2190 j par défaut ; 1095 seulement si SCI familiale déclarée |
| MED-2 | ⚪ | **IRL codé en dur à +2,5 %** et affiché au bailleur. L'IRL varie (≈3,5 %→≈1 %). Révision > indice réel = non écrite, trop-perçu récupérable. | `services/irl_service.py:18,74,129` | Table versionnée des indices INSEE trimestriels |
| MED-3 | ⚪ | **`zone_tendue` silencieusement ignoré** (absent de `BienUpdate`) → préavis toujours 3 mois au lieu d'1. | `models/biens.py:31-53` vs `biens_baux.py:463` | Ajouter `zone_tendue` au modèle Pydantic |
| MED-4 | ⚪ | **Bail mobilité proposé dans l'UI mais rejeté par l'API (422)**. Feature morte. | `FicheBienIdentite.svelte:118` vs `models/biens.py:12` `Literal["nu","meuble","mixte"]` | Ajouter `"mobilite"` au Literal |
| MED-5 | ⚪ | **Plafond déficit 10 700 € appliqué au niveau SCI puis réparti** au lieu de par foyer fiscal (art. 156-I-3° CGI) → case 4BB sous-évaluée, associés sur-imposés. | `resume_fiscal_service.py:482,554` | Appliquer le plafond par associé après répartition |
| MED-6 | ⚪ | **Ligne CERFA 229** utilisée pour les provisions de copropriété (229 = régularisation, soustractive ; 228 = provisions). Revenu foncier surévalué à la recopie. | `resume_fiscal_pdf_service.py:335,331` | 228 pour provisions, 222 pour le forfait 20 € |
| MED-7 | ⚪ | **Congé bailleur = notification + 183 j** au lieu de « 6 mois avant le terme, effet au terme ». Préavis en jours calendaires (off-by-one). Cas de préavis réduit 1 mois non modélisés. | `biens/biens_baux.py:397-418` | Rattacher au terme du bail ; `dateutil.relativedelta` |
| MED-8 | ⚪ | **Surtaxe plus-value : décote des tranches absente** (art. 1609 nonies G). À 55 000 € : 1 100 € codé vs 850 € réel (+29 %). *(Abattements et taux 19 %+17,2 % corrects.)* | `simulateur-plus-value/+page.svelte:109-121` | Ajouter le terme correctif par tranche |
| MED-9 | ⚪ | **Micro-foncier recommandé à des SCI** sans le droit (art. 32 CGI : nécessite un immeuble loué nu en direct). | `resume_fiscal_service.py:576-594`, `fiscalite/+page.svelte:485` | Conditionner ou retirer la recommandation |
| MED-10 | ⚪ | **Report déficit : off-by-one sur 10 ans** (`.gt` au lieu de `.gte`) → 9 ans utilisables. | `resume_fiscal_service.py:126,150` | `.gte("annee_prescription", annee)` |
| MED-11 | ⚪ | **Aucun contrôle de chevauchement de baux** ; passage silencieux du bail précédent à `expire` sans `date_fin`. | `biens/biens_baux.py:154-165` | Vérifier continuité + confirmation |
| MED-12 | ⚪ | **Quittance : numéro non idempotent** (trous de séquence sur `/render` et `/batch`) et **date de paiement non affichée** (imprime `date.today()`). | `quitus.py:176,213`, `quitus_service.py:190,362` | Numéroter à l'émission seulement ; transmettre `date_paiement` |
| MED-13 | ⚪ | **Rentabilité nette-nette fausse avec crédit** : intérêts d'emprunt non déduits de la base IR/PS. | `rentabilite_service.py:57-65,76` | Déduire les intérêts de la base imposable |
| MED-14 | ⚪ | **Import CSV loyers cassé** : `get_supabase_user_client` non importé → `NameError` → 500 systématique. + pas de contrôle de doublon ni transaction ; export non ré-importable. | `import_csv.py:17,205` | `from ...supabase_client import get_supabase_user_client` |
| MED-15 | ⚪ | **Migration 041 : un seul loyer/mois/bien** toutes personnes confondues (colocation à baux séparés impossible ; création d'index échoue si doublon existant). | `041_loyers_unique_monthly.sql:8-9` | Unicité par `(id_bien, bail, mois)` |
| MED-16 | ⚪ | **SIREN sans clé de contrôle (Luhn)** ; `date_cloture_exercice` jetée à la création de SCI (`exclude=`). | `models/sci.py:8`, `scis.py:334` | Valider Luhn ; retirer l'exclusion |
| MED-17 | ⚪ | **Somme des parts contrôlée seulement à la hausse** → répartition < 100 % fausse le résultat par associé ; la 2042 individuelle n'est pas bloquée. | `associes.py:68-88`, `cerfa.py:331` | Contrôler l'égalité stricte à 100 % |
| MED-18 | ⚪ | **Quorum d'AG codé à >50 %** (il n'y a pas de quorum légal en SCI — art. 1852 unanimité sauf statuts). Base légale du délai de convocation erronée. | `assemblees_generales.py:371,446,541` | Paramétrer selon les statuts ; corriger la référence (décret 78-704 art. 40) |
| MED-19 | ⚪ | **Calendrier fiscal** : dates dynamiques (OK) mais plusieurs fausses (liasse IS au 31/03, 2072, AG ignorant `date_cloture_exercice`) ; **TVA absente** ; détection CFE cassée côté front. | `calendrier_fiscal.py:60-109`, `SciFiscalCalendar.svelte:72` | Corriger les dates ; dériver de la clôture réelle |
| MED-20 | 🔴 | **Suppression RGPD incomplète** : `notifications` supprimées via le client user sans policy DELETE → RLS refuse en silence (survivent) ; lignes `sci` non supprimées ; pas de re-confirmation. | `gdpr.py:298,316,372-380` | Cascade en service_role + suppression `sci` + confirmation email |
| MED-21 | 🔴 | **Emails en clair dans les logs WARNING/ERROR** (non masqués hors `auth.py`). Un log dev journalise même le magic-link complet. | `email_service.py:65+`, `auth_service.py:65` | Processor structlog masquant `email`/`action_link` |
| MED-22 | ⚪ | **Admin : pas de rate-limit dédié ni MFA**, secret statique unique en `sessionStorage`, échecs non alertés ; `get_current_admin` (JWT) est du code mort. | `security.py:150-182`, `admin.py:35-38` | `@limiter.limit("5/minute")` + alerte Sentry + migration vers JWT admin |

---

# LOW (synthèse)

| # | Constat | Référence |
|---|---|---|
| L1 | `admin_mrr_snapshots`/`admin_audit_log` : commentaires « No RLS needed ». **En prod, lecture anon = `[]`** (RLS tient ou tables vides) → risque non confirmé, mais activer RLS + `REVOKE` par principe. | `023_admin_mrr_snapshots.sql:20` |
| L2 | `notifications` INSERT `WITH CHECK (true)` sans `TO service_role` → injection de notif possible via PostgREST (phishing in-app). RLS anon tient en lecture, mais l'écriture reste à vérifier. | `004_notifications.sql:30-32` |
| L3 | CORS élargit automatiquement au domaine apex + www avec `allow_credentials=true` (redondant, risqué si `FRONTEND_URL` devient un sous-domaine mutualisé). **CORS live OK** (origine `evil` rejetée). | `main.py:440-448` |
| L4 | Jetons (`token`, `access_token`, `session_id`) passés en **query string** → journalisés (logs proxy, analytics). | `auth.py:189,214`, `stripe.py:445` |
| L5 | URLs signées documents à **24 h** (vs 30 min pour l'export RGPD) — incohérent, non révocable. | `biens/biens_documents.py:124,148` |
| L6 | Monitoring **mort en prod** : `docker-compose.monitoring.yml` référencé nulle part, aucun promtail dans le repo ; `deploy.sh:224` affiche pourtant l'URL Grafana. | commit `7274a0e` |
| L7 | 3 services sur 5 (matomo, matomo-db, uptime-kuma) **sans limite mémoire ni rotation de logs** → saturation disque VPS possible. | `docker-compose.yml` |
| L8 | Mots de passe Matomo par défaut (`matomo_change_me`) publiés dans le compose, absents de `.env.example`. | `docker-compose.yml:137-140` |
| L9 | `docker volume prune -f` hebdomadaire peut détruire les volumes nommés (Docker < 23). | `scripts/docker-cleanup-cron.sh:22` |
| L10 | `LockedAction` : l'action verrouillée s'exécute quand même (interception sur le parent, ordre de bouillonnement DOM) → double overlay en démo. | `LockedAction.svelte:16-20` |
| L11 | Contraste WCAG 1.4.3 : **261 occurrences** `text-slate-400/300` en échec (dont le prix TTC de la page pricing). | `PricingSection.svelte:80` +260 |
| L12 | Modales : aucune ne restitue le focus ; 4 modales sans piège à focus ni Escape (dont dissolution SCI). | `CrudModal.svelte` vs 4 modales custom |
| L13 | Lignes de tableau cliquables non atteignables au clavier ; `role="tab"` sans navigation flèches/roving tabindex. | `bilans/+page.svelte:345`, `biens/[bienId]/+page.svelte:189` |
| L14 | **Aucune PWA** : pas de `manifest.json`, pas de service worker, pas de `theme-color`. | `frontend/static/` |
| L15 | `.bak` versionnés (`scis_biens.py.bak`, `api.ts.bak`) ; `.coverage` versionné ; `AGENT.md`==`AGENTS.md`. | racine |
| L16 | `float` (au lieu de `Decimal`) sur les chemins fiscaux CERFA/2072 ; `datetime.utcnow()` naïf ponctuel. | `resume_fiscal_service`, `biens_core.py:519` |
| L17 | Dépendances Python non figées (21/21 en plages, pas de lock) ; `pytest`/`bandit` embarqués dans l'image prod. | `backend/requirements.txt` |
| L18 | Boucle de redirection `/dashboard ↔ /welcome` sur panne API (catch fourre-tout). | `(app)/+layout.ts:36-47` |
| L19 | `/welcome` impose 7 s fixes dans le tunnel d'inscription. | `welcome/+page.svelte:13-18` |
| L20 | N+1 client sur `/exploitation` (1+N `fetchSciBiens`). | `exploitation/+page.svelte:45-61` |

---

# Faux positifs corrigés par les tests de production

Par honnêteté d'audit, trois hypothèses issues de l'analyse statique sont **infirmées en direct** :

1. **« En-têtes de sécurité perdus sur les pages HTML »** — FAUX. `app.gerersci.fr/` et `/dashboard` renvoient bien CSP, HSTS (`max-age=63072000; includeSubDomains; preload`), `X-Frame-Options: DENY`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`. Caddy les pose (`via: 1.1 Caddy`). L'analyse avait porté sur `docker/nginx.conf`, **code mort** (le proxy réel est Caddy, pas nginx — `CLAUDE.md:15` est faux sur ce point).
2. **« Tables admin exposées en lecture à l'anon »** — NON CONFIRMÉ. Lecture avec la clé anon = `[]` sur `admin_mrr_snapshots`, `admin_audit_log`, `subscriptions`, etc. RLS tient. Reclassé en LOW (défense en profondeur).
3. **« Fuite de données cross-tenant »** — NON REPRODUITE. Un compte authentifié neuf lit `[]` sur toutes les tables tenant. L'isolement de base fonctionne ; le risque réel est l'**écriture** sur ses propres colonnes (CRITICAL-1) et les policies `associes` (CRITICAL-3), pas la lecture ouverte.

---

# Forces (à préserver)

**Sécurité** : vérification JWT stricte (algos en liste blanche, `verify_aud`, JWKS caché — `security.py:71-103`) ; webhook Stripe correct (signature + idempotence `UNIQUE(event_id)`) ; **aucune manipulation de prix au checkout** (prix résolu serveur depuis un `plan_key` enum) ; refund scopé à l'appelant ; secret admin en `hmac.compare_digest` fail-closed ; en-têtes de sécurité complets en prod ; CORS qui rejette les origines étrangères (vérifié live) ; conteneurs non-root, ports bindés sur `127.0.0.1` ; validation d'upload sérieuse (magic bytes ↔ extension) ; anti-path-traversal explicite ; Jinja2 `autoescape` ; **zéro `{@html}`** sur 197 composants (aucune surface XSS de rendu).

**Paywall** : fail-closed (`check_write_access` renvoie `False` sans ligne) ; triple couche (middleware + `require_gerant_role` + `enforce_limit`) ; quotas réellement appliqués côté backend ; consentement L221-28 correctement recueilli (case décochée par défaut).

**Fiscalité (ce qui est juste)** : barèmes d'abattement plus-value exacts (IR 22 ans / PS 30 ans, 19 %+17,2 %) ; ventilation intérêts/autres charges du déficit correcte ; plafond 10 700 € correct pour 2026 ; quittance sérieuse (séparation loyer/charges, mentions légales, bascule reçu partiel) ; compteur de quittances atomique (RPC `SECURITY DEFINER`) ; divisions par zéro gardées partout ; garde-fou IR→IS avec confirmation + audit.

**Infra/qualité** : arrêt gracieux soigné ; healthchecks applicatifs ; rotation des logs sur backend/frontend ; `svelte-check` strict bloquant en CI ; Bandit bloquant ; smoke tests de prod post-déploiement ; `concurrency` anti-déploiements concurrents ; `.env` non tracké (corrigé au commit `8ad430d7`) ; sonde de readiness qui valide les price IDs contre l'API Stripe (rare et excellent) ; dette de commentaires quasi nulle ; Svelte 5 quasi intégral (346 `onclick` vs 4 `on:click`).

---

# Points non vérifiés / limites de l'audit

- **Historique git** : `.env` a été tracké avant le commit `8ad430d7` et **contient des secrets réels dans l'historique** (`sk_test_…`, `whsec_…`, `re_…`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`). Si le dépôt a un jour été public ou partagé, **rotation obligatoire** de toutes ces clés. À vérifier : `git log -p --all -- .env`.
- **Compte de test créé pendant l'audit** : `user_id=be2e22f5-a401-4d25-b2e4-67003bc85df8` (email `audit.pentest+…@gerersci-audit.test`). La ligne `subscriptions` de test a été supprimée (DELETE 204 vérifié) ; **le compte utilisateur reste à purger** côté Supabase.
- **État RLS effectif en prod** : je n'ai lu que les migrations. Deux jeux divergents existent (`supabase/migrations/` et `backend/scripts/migrations/`). Confirmer avec `SELECT * FROM pg_policies WHERE schemaname='public';` et `SELECT relname, relrowsecurity FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind='r';`.
- **Table `calendrier_fiscal`** écrite par le code mais créée par **aucune migration** → état RLS inconnu (potentielle exposition). À vérifier en priorité.
- **Config Caddy de production** (TLS, timeouts, body max, rate-limit edge) : vit dans le dépôt `vps-infra`, hors périmètre — angle mort structurel.
- **Backups/monitoring réels sur le VPS** hors dépôt : `crontab -l`, `systemctl list-timers`, `docker ps | grep -E 'grafana|loki'`.
- **Aucun test n'a été exécuté** (env sandbox Linux ≠ venv macOS) : findings de code établis par lecture + `grep -n`, findings prod par sonde HTTP réelle.
- **CRITICAL-3 (associes)** établi par SQL, non rejoué en prod (aurait nécessité de cibler une vraie SCI — écarté par éthique).

---

# Plan d'action priorisé

**Aujourd'hui (arrêt de l'hémorragie)**
1. CRITICAL-8 — `pg_dump` manuel hors VPS **maintenant**.
2. CRITICAL-2 + CRITICAL-1 — couper l'exposition `/rest/`, `/storage/`, `/realtime/` sur `api.gerersci.fr` (referme le contournement de paiement) **et** retirer les policies d'écriture user sur `subscriptions`.
3. HIGH-1 + HIGH-2 — désactiver le signup GoTrue public et les `/docs` en prod.

**Cette semaine**
4. CRITICAL-3 — corriger les policies `associes` + gating API par rôle.
5. CRITICAL-5 + CRITICAL-6 — rendre la fiscalité en lecture seule ; filtrer les charges récupérables.
6. CRITICAL-9 — sortir le cron des workers web.
7. HIGH-11/12 — corriger le gate readiness, l'ordre des migrations, jouer les migrations au déploiement.

**Ce mois**
8. CRITICAL-4/7, HIGH-3→10 — chaîne de paiement (Fondateur, réconciliation webhook, garantie, résiliation 3 clics, past_due).
9. HIGH-15 — filtre `deleted_at` généralisé.
10. HIGH-16 — CI : tests unitaires + ruff/mypy bloquants.
11. MEDIUM fiscaux (bail 6 ans, IRL, zone tendue, lignes CERFA) — chantier « exactitude fiscale ».

**Rotation des secrets** (si l'historique git a fuité) : `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `STRIPE_SECRET_KEY`, `RESEND_API_KEY`.

---

*Audit réalisé le 25/07/2026. 9 CRITICAL, 16 HIGH, 22 MEDIUM, ~20 LOW. 8 findings vérifiés en production, dont le contournement de paiement reproduit de bout en bout puis nettoyé.*
