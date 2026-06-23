# Stripe — Diagnostic webhook + Passage en production (LIVE)

> Runbook créé suite à l'alerte Stripe « échecs de livraison de webhooks (mode test) » pour
> `https://api.gerersci.fr`. Consigne le diagnostic réel + les étapes exactes de passage en
> production. Remplace `STRIPE_SETUP_COMPLETE.md` (obsolète).

## TL;DR — il y a 3 comptes Stripe, et la prod doit pointer vers le bon

| Compte | ID | Rôle | État |
|--------|----|----|------|
| **A** | `acct_1SFrVgBCxd3SKdGJ` | Ancien compte (source de l'alerte webhook `we_1TKFE…`) | À nettoyer |
| **B** | `acct_1Sei1OHfxmPH8rox` | **Configuré dans l'env actuel** (clés `sk_test_`) — bac à sable | Non activé (test) |
| **C** | `acct_1SFrY0ApRgYAyPDH` ("SCI Manager") | **LE vrai compte de production** | ✅ **Activé** (`charges_enabled=true`) |

➡️ **Le passage en prod = faire pointer l'env vers le compte C (clés live), pas vers B.**
Le compte C a déjà : compte activé (IBAN + identité vérifiés), **produits live** et **prix
live** créés. Il ne manque que : (1) un **webhook live**, (2) le **basculement de l'env**,
(3) le **redéploiement**.

## Contexte technique
- Handler : `POST /api/v1/stripe/webhook` (`backend/app/api/v1/stripe.py:538`) — vérifie la
  signature avec `STRIPE_WEBHOOK_SECRET` → **400** si mismatch. Events traités :
  `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`,
  `invoice.payment_failed`.
- Le mode (test/live) dépend uniquement des clés (`sk_test_` vs `sk_live_`). Passer en prod =
  **configuration**, pas de code. `config.py` refuse de démarrer en `APP_ENV=production` avec un
  secret placeholder.

## Diagnostic constaté
- **L'alerte vient du compte A** (`we_1TKFEOBCxd3SKdGJxejXfh7A`). L'env utilise le compte B, donc
  les events du compte A ne passent plus la vérif de signature → 400.
- Le compte B (env) est en **test**, non activé.
- Le **compte C** est **activé pour le live** et possède déjà les **produits + prix live**
  (vérifié via l'API Stripe / MCP, `livemode:true`).
- **Cloudflare ne bloque PAS Stripe** (vérifié) — voir Étape 5.

## Prix LIVE existants (compte C `acct_1SFrY0ApRgYAyPDH`)
| Plan | `price_id` live | Montant |
|------|-----------------|---------|
| Gestion mensuel | `price_1TDtVBApRgYAyPDHfVRFGuUj` | 19€ |
| Gestion annuel  | `price_1TDtVBApRgYAyPDHVjOG7o3N` | 190€ |
| Pilotage mensuel| `price_1TDtVKApRgYAyPDH5J9tUNFt` | 39€ |
| Pilotage annuel | `price_1TDtVLApRgYAyPDHbkYyvnmN` | 390€ |
| Fondateur (one-time) | `price_1TlazQApRgYAyPDH449eJzEk` | **990€** |

> ✅ **Prix alignés** (suite à l'étude de marché, voir `docs/PRICING_STUDY.md`) : Fondateur porté
> à **990€** (app + Stripe + CGV/CGU). Plan **Cabinet abandonné** (produit + prix archivés dans
> Stripe). Gestion 19€ / Pilotage 39€ inchangés.

---

## Étape 1 — Stopper les alertes (compte A)
Dashboard du **compte A** `acct_1SFrVgBCxd3SKdGJ` → Developers → Webhooks →
`we_1TKFEOBCxd3SKdGJxejXfh7A` → **Disable** (ou Delete).

## Étape 2 — Créer le webhook LIVE (compte C, dashboard)
La gestion des webhooks n'est pas exposée par le MCP → à faire au Dashboard, **compte C, mode
Live** : Developers → Webhooks → Add endpoint
- URL : `https://api.gerersci.fr/api/v1/stripe/webhook`
- Events : `checkout.session.completed`, `customer.subscription.updated`,
  `customer.subscription.deleted`, `invoice.payment_failed`
- Copier le **Signing secret** (`whsec_…`).

## Étape 3 — Basculer l'env cloud vers le compte C (LIVE)
Récupérer les clés live du compte C : Dashboard C → Developers → API keys (`sk_live_…`,
`pk_live_…`). Puis remplacer dans l'env cloud :

```
# Clés LIVE (compte C) — à récupérer au dashboard
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...          # secret du webhook créé à l'Étape 2

# Price IDs LIVE (compte C) — valeurs exactes ci-dessous
STRIPE_GESTION_MONTHLY_PRICE_ID=price_1TDtVBApRgYAyPDHfVRFGuUj
STRIPE_GESTION_ANNUAL_PRICE_ID=price_1TDtVBApRgYAyPDHVjOG7o3N
STRIPE_PILOTAGE_MONTHLY_PRICE_ID=price_1TDtVKApRgYAyPDH5J9tUNFt
STRIPE_PILOTAGE_ANNUAL_PRICE_ID=price_1TDtVLApRgYAyPDHbkYyvnmN
STRIPE_FONDATEUR_PRICE_ID=price_1TlazQApRgYAyPDH449eJzEk
# (Cabinet abandonné — ne plus configurer STRIPE_CABINET_*)

# Alias hérités (fallback) = mêmes IDs live
STRIPE_STARTER_PRICE_ID=price_1TDtVBApRgYAyPDHfVRFGuUj
STRIPE_STARTER_ANNUAL_PRICE_ID=price_1TDtVBApRgYAyPDHVjOG7o3N
STRIPE_PRO_PRICE_ID=price_1TDtVKApRgYAyPDH5J9tUNFt
STRIPE_PRO_ANNUAL_PRICE_ID=price_1TDtVLApRgYAyPDHbkYyvnmN
STRIPE_LIFETIME_PRICE_ID=price_1TlazQApRgYAyPDH449eJzEk
```

## Étape 4 — Redéployer + vérifier
- Redéployer (`./deploy.sh` / CI). `config.py` bloque si un secret reste placeholder.
- Dashboard C (live) → webhook → **Send test event** → attendu **200**.
- Faire un vrai paiement (petit montant) → vérifier une ligne `subscriptions` `is_active=true`.
- Confirmer `STRIPE_SECRET_KEY` commence par `sk_live_`.

## Étape 5 — Cloudflare (vérifié : aucune action)
`api.gerersci.fr` est derrière **Cloudflare** (zone `gerersci.fr`, plan Free). Vérifié via API :
BIC=on, Bot Fight Mode=off, aucune règle WAF custom. Un POST avec `User-Agent: Stripe/1.0`
atteint le backend (400 « Missing Stripe signature » = OK) ; seul un UA générique reçoit le
`403/1010`. **Cloudflare ne bloque pas Stripe.** Filet de sécurité (si Bot Fight Mode activé un
jour) : règle WAF *Skip* sur `http.request.uri.path eq "/api/v1/stripe/webhook"`.

## Étape 6 — Tester les webhooks en local (test)
```
stripe login
stripe listen --forward-to localhost:8001/api/v1/stripe/webhook
stripe trigger checkout.session.completed
```
Backend : `cd backend && PYTHONPATH=. pytest tests -k stripe`.

## Annexe — résolution price_id → plan
`backend/app/core/entitlements.py:194` : Gestion/Pilotage/Fondateur prioritaires, Starter/Pro en
fallback. Toutes les vars sont transmises au conteneur par `docker-compose.yml:30-43`.
