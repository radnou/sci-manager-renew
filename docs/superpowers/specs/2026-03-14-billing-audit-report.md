# Audit Billing & Paywall — GererSCI

**Date** : 14 mars 2026
**Auditeurs** : QA Engineer Senior + Expert Technique SaaS (Billing & Stripe)
**Environnement** : Local (Supabase + Stripe Test `SCI Manager`)

---

## 1. PLAN DE SEEDING

### 3 comptes test créés

| Compte | Email | Plan | SCIs | Biens | Stripe Price ID |
|--------|-------|------|------|-------|-----------------|
| **A** (Free) | free@audit.test | Essentiel | 1 (max=1) | 2 (max=2) | _(aucun)_ |
| **B** (Starter) | starter@audit.test | Gestion | 2→3 (max=3) | 5 (max=10) | `price_1TAyt3BCxd3SKdGJ0WbBDbsW` |
| **C** (Pro) | pro@audit.test | Fiscal | 3→5 (illimité) | 8 (illimité) | `price_1TAyt3BCxd3SKdGJeNgk9G3E` |

**Données par SCI** : biens immobiliers, baux actifs, 3 mois de loyers (mix payé/en attente).

---

## 2. MATRICE DE DROITS

### Quotas (enforce_limit)

| Opération | Free (max 1/2) | Starter (max 3/10) | Pro (illimité) |
|-----------|:-:|:-:|:-:|
| Créer SCI (dans limite) | — | **201** ✅ | **201** ✅ |
| Créer SCI (hors limite) | **402** ✅ | **402** ✅ | **201** ✅ |
| Lister SCIs | **200** ✅ | **200** ✅ | **200** ✅ |
| Dashboard | **200** ✅ | **200** ✅ | **200** ✅ |
| Finances | **200** ✅ | **200** ✅ | **200** ✅ |

### Features (ensure_feature_enabled)

| Feature | Free | Starter | Pro |
|---------|:-:|:-:|:-:|
| Quittances PDF | ✅ | ✅ | ✅ |
| Charges | ❌ 402 | ✅ | ✅ |
| Documents | ❌ 402 | ✅ | ✅ |
| Notifications | ❌ 402 | ✅ | ✅ |
| Fiscalité | ❌ 402 | ❌ 402 | ✅ |
| CERFA 2044 | ❌ 402 | ❌ 402 | ✅ |
| Associés management | ❌ 402 | ❌ 402 | ✅ |
| PNO / Frais agence | ❌ 402 | ❌ 402 | ✅ |
| Rentabilité | ❌ 402 | ❌ 402 | ✅ |

### Stripe Checkout

| Endpoint | Résultat |
|----------|----------|
| Guest checkout Starter (monthly) | **200** → URL `checkout.stripe.com` ✅ |
| Guest checkout Pro (annual) | **200** → URL `checkout.stripe.com` ✅ |
| Auth checkout Starter | **200** ✅ |
| Auth checkout Pro | **200** ✅ |

---

## 3. RAPPORT D'ANOMALIES

### 🔴 CRITIQUE — Corrigé

| # | Anomalie | Sévérité | Status |
|---|----------|----------|--------|
| **B1** | **INSERT bloqué par RLS** — Toutes les opérations CREATE (SCI, bien, bail, loyer, etc.) retournaient 500 au lieu de 201/402 | 🔴 Critique | ✅ Corrigé |

**Cause** : Migration C01 (JWT per-request) a basculé tous les endpoints vers `get_supabase_user_client()`. Les policies RLS `INSERT` exigent que l'utilisateur soit déjà membre de la SCI — paradoxe pour le premier INSERT.

**Fix** : Pattern "elevated insert" — `_get_write_client()` (service role) pour les INSERTs, `_get_client(request)` (user JWT) pour les lectures.

### 🟡 À VÉRIFIER — UX Frontend

| # | Point | Status |
|---|-------|--------|
| **U1** | Modale d'upsell quand limite atteinte (402) | À vérifier en E2E |
| **U2** | Boutons grisés/masqués quand feature non dispo | À vérifier en E2E |
| **U3** | Flow checkout Stripe → redirection → webhook → activation plan | À tester |
| **U4** | Pas de données premium dans le DOM pour comptes non-autorisés | À vérifier |

### ✅ PASSÉ

| # | Test | Résultat |
|---|------|----------|
| **S1** | Paywall FREE bloque 2ème SCI | 402 ✅ |
| **S2** | Paywall STARTER bloque 4ème SCI | 402 ✅ |
| **S3** | PRO crée sans limite | 201 ✅ |
| **S4** | Stripe checkout génère URL valide | 200 ✅ |
| **S5** | Auth obligatoire sur tous endpoints protégés | 401 ✅ |
| **S6** | Subscription endpoint retourne entitlements | 200 ✅ |

---

## 4. CONFIGURATION STRIPE TEST

### Produits créés

| Produit | ID | Description |
|---------|-----|-------------|
| GererSCI Gestion | `prod_U9HR3OLTCP36Wx` | Plan Gestion — 3 SCI, 10 biens |
| GererSCI Fiscal | `prod_U9HRpAd2Fs27q8` | Plan Fiscal — illimité |

### Prix créés

| Plan | Période | Prix | Price ID |
|------|---------|------|----------|
| Gestion | Mensuel | 19€ | `price_1TAyt3BCxd3SKdGJ0WbBDbsW` |
| Gestion | Annuel | 180€ | `price_1TAyt3BCxd3SKdGJrSPKKLom` |
| Fiscal | Mensuel | 39€ | `price_1TAyt3BCxd3SKdGJeNgk9G3E` |
| Fiscal | Annuel | 348€ | `price_1TAyt4BCxd3SKdGJJiyH7t4O` |

### Clés test

| Clé | Valeur |
|-----|--------|
| Publishable | `pk_test_51SFrVg...` |
| Secret | `sk_test_51SFrVg...` |

---

*Phase 3 (E2E navigateur) en cours...*
