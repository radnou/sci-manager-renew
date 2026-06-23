# Stripe — Diagnostic webhook + Passage en production (LIVE)

> Runbook créé suite à l'alerte Stripe « échecs de livraison de webhooks (mode test) »
> pour `https://api.gerersci.fr`. Il consigne le diagnostic réel et les étapes exactes de
> passage en production. Remplace les infos obsolètes de `STRIPE_SETUP_COMPLETE.md`.

## TL;DR

| Sujet | État | Action |
|------|------|--------|
| Alerte webhook (mode test) | Vient de l'**ancien compte** `acct_1SFrVgBCxd3SKdGJ`, endpoint `we_1TKFEOBCxd3SKdGJxejXfh7A` | **Désactiver/supprimer** cet endpoint (Étape 1) |
| Compte actuel `acct_1Sei1OHfxmPH8rox` (env) | Mode **test** OK : catalogue + webhook `we_1TLLSOHfxmPH8roxJdb2BYRv` actifs | Vérifier secret + redéploiement (Étape 2) |
| Passage en **LIVE** | **BLOQUÉ** : compte non activé (`charges_enabled=false`, `details_submitted=false`) | Activer le compte d'abord (Étape 3) |
| Cloudflare devant `api.gerersci.fr` | Renvoie 403 (err 1010) aux requêtes auto | Vérifier que les IP/User-Agent Stripe ne sont pas bloqués (Étape 5) |

## Contexte technique

- Handler webhook : `POST /api/v1/stripe/webhook` (`backend/app/api/v1/stripe.py:538`).
  Vérifie la signature avec **un seul** `STRIPE_WEBHOOK_SECRET` → **HTTP 400** si elle ne
  correspond pas. Events traités : `checkout.session.completed`,
  `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`.
- Le code **ne distingue pas test/live** : le mode dépend uniquement des clés (`sk_test_`
  vs `sk_live_`). Passer en prod = changer la **config**, pas le code.
- `backend/app/core/config.py` refuse de démarrer en `APP_ENV=production` si un secret est un
  *placeholder* (mais accepte des clés `sk_test_` — donc « APP_ENV=production + clés test » démarre).

## Diagnostic constaté (lecture seule API Stripe, compte de l'env)

Compte configuré dans l'env cloud : **`acct_1Sei1OHfxmPH8rox`** (mode **TEST**).

```
details_submitted: False   charges_enabled: False   payouts_enabled: False   ← compte NON activé
```

Webhook (mode test) déjà en place et **activé** :

```
we_1TLLSOHfxmPH8roxJdb2BYRv  enabled  →  https://api.gerersci.fr/api/v1/stripe/webhook
```

Catalogue (mode test) cohérent avec l'env :

| Produit | Product ID | Prix mensuel | Prix annuel |
|--------|-----------|--------------|-------------|
| Gestion | `prod_UJzQYozlxVoA3H` | `price_1TLLRXHfxmPH8roxJrsHYPE6` (19€) | `price_1TLLRYHfxmPH8roxyDTAptJw` (190€) |
| Pilotage | `prod_UJzQT6hpsNvvFr` | `price_1TLLRlHfxmPH8roxLXjbMvWt` (39€) | `price_1TLLRmHfxmPH8roxqesclZCF` (390€) |
| Fondateur | `prod_UJzQ8hZRNQl6QK` | — | `price_1TLLRnHfxmPH8roxBIw3MZ3w` (349€, paiement unique) |
| Cabinet | `prod_UJzQA2WfscQVwu` | `price_1TLLRx...2bL8diH5` (79€) | `price_1TLLRx...uOE7GDtr` (790€) |

➡️ **Cause de l'alerte** : l'endpoint en échec appartient à l'**ancien compte**
(`...BCxd3SKdGJ`). Le backend en prod utilise désormais le secret du **nouveau compte**
(`...HfxmPH8rox`) ; il ne peut donc pas valider les events de l'ancien → 400 systématique.

---

## Étape 1 — Stopper les alertes (ancien compte)

Dans le Dashboard du **compte `acct_1SFrVgBCxd3SKdGJ`** (mode test) :
`Developers → Webhooks → we_1TKFEOBCxd3SKdGJxejXfh7A` → **Disable** (ou **Delete**).

C'est l'unique source des e-mails d'échec. Si ce compte n'est plus utilisé, le supprimer
entièrement de l'organisation est encore plus propre.

## Étape 2 — Valider le mode TEST du compte actuel

1. Vérifier que le `STRIPE_WEBHOOK_SECRET` de l'env cloud correspond bien au signing secret
   de `we_1TLLSOHfxmPH8roxJdb2BYRv` (Dashboard `acct_1Sei1OHfxmPH8rox` → Webhooks → cet
   endpoint → *Signing secret*). Stripe ne renvoie ce secret qu'à la création/rotation.
2. S'assurer que l'endpoint est abonné aux 4 events gérés (ci-dessus).
3. **Redéployer** le backend pour qu'il prenne l'env à jour.
4. Tester : Dashboard → cet endpoint → **Send test event** (`checkout.session.completed`)
   → réponse attendue **200**. Ou en local : voir Étape 6.

## Étape 3 — Passage en LIVE (⚠️ nécessite l'activation du compte)

### 3a. Activer le compte Stripe (préalable obligatoire)
Dashboard (compte `acct_1Sei1OHfxmPH8rox`) → **Activer le compte** : infos société (SIREN),
représentant légal/identité, IBAN. Attendre `charges_enabled = true`. Sans cela, **aucune
ressource live ni paiement** n'est possible.

### 3b. Créer les produits/prix en mode LIVE
Basculer le Dashboard en **mode Live**, puis recréer le catalogue à l'identique du test
(mêmes montants/intervalles que le tableau ci-dessus). Noter les **nouveaux** `price_...` live.
> Peut être automatisé via le MCP Stripe (`stripe_api_write`) **si** la connexion MCP est en
> mode live ET autorisée en écriture ; sinon le faire dans le Dashboard.

### 3c. Créer l'endpoint webhook LIVE
Mode Live → `Developers → Webhooks → Add endpoint` :
- URL : `https://api.gerersci.fr/api/v1/stripe/webhook`
- Events : `checkout.session.completed`, `customer.subscription.updated`,
  `customer.subscription.deleted`, `invoice.payment_failed`
- Récupérer le **Signing secret** (`whsec_...`) live.

### 3d. Mettre à jour l'env cloud (mêmes variables que d'habitude) avec les valeurs LIVE
```
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...            # secret de l'endpoint LIVE (3c)
STRIPE_GESTION_MONTHLY_PRICE_ID=price_...  # live
STRIPE_GESTION_ANNUAL_PRICE_ID=price_...   # live
STRIPE_PILOTAGE_MONTHLY_PRICE_ID=price_... # live
STRIPE_PILOTAGE_ANNUAL_PRICE_ID=price_...  # live
STRIPE_FONDATEUR_PRICE_ID=price_...        # live
# alias hérités (mettre = aux IDs live correspondants) :
STRIPE_STARTER_PRICE_ID / STRIPE_STARTER_ANNUAL_PRICE_ID
STRIPE_PRO_PRICE_ID / STRIPE_PRO_ANNUAL_PRICE_ID
STRIPE_LIFETIME_PRICE_ID  STRIPE_CABINET_PRICE_ID  STRIPE_CABINET_ANNUAL_PRICE_ID
```
(Template complet dans `.env.production.example`.) `APP_ENV=production` peut rester.

### 3e. Redéployer
`./deploy.sh` (ou le pipeline CI). `config.py` bloquera le démarrage si un secret reste un
placeholder — garde-fou voulu.

## Étape 4 — Vérification finale (LIVE)
- Dashboard live → endpoint webhook → **Send test event** → **200**.
- Réaliser un vrai paiement de test (petit montant / carte réelle) → vérifier qu'une ligne
  `subscriptions` est créée/mise à jour avec `is_active=true` (Supabase).
- Vérifier le mode des clés : `STRIPE_SECRET_KEY` commence par `sk_live_`.

## Étape 5 — Cloudflare / WAF (à contrôler)
`api.gerersci.fr` est derrière **Cloudflare** (les requêtes automatisées reçoivent `403`,
erreur **1010**). Si les webhooks Stripe échouent malgré une config correcte, vérifier dans
Cloudflare que **Bot Fight Mode / WAF** ne challenge pas les POST de Stripe :
- Autoriser le chemin `/api/v1/stripe/webhook` (WAF skip rule), ou
- Autoriser l'User-Agent `Stripe/1.0` et/ou les plages d'IP de Stripe
  (https://docs.stripe.com/ips → webhook IPs).

## Étape 6 — Tester les webhooks en local (mode test)
```
stripe login
stripe listen --forward-to localhost:8001/api/v1/stripe/webhook
# (utiliser le whsec_ affiché par `stripe listen` comme STRIPE_WEBHOOK_SECRET local)
stripe trigger checkout.session.completed
```
Backend : `cd backend && PYTHONPATH=. pytest tests -k stripe`.

## Annexe — Mapping plan → variable d'env (référence)
Résolution dans `backend/app/core/entitlements.py:194` (`resolve_price_id_for_plan`) :
les noms **Gestion/Pilotage/Fondateur** sont prioritaires, **Starter/Pro** servent de
fallback. Tous ces vars sont bien transmis au conteneur par `docker-compose.yml:30-43`.
