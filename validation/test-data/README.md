# Données et comptes de test

Ce document est la référence de tous les comptes, jeux de données et variables d'environnement utilisés lors de la recette GererSCI.

---

## Comptes disponibles

| Compte | Mot de passe | Créé par | Prérequis | Usage recommandé |
|---|---|---|---|---|
| `test@gerersci.fr` | `<mot de passe du seed, cf. supabase/seed.sql>` | `supabase/seed.sql` (lignes 12-13) | `supabase db reset` uniquement - aucun prérequis Python | Compte de référence E2E ; email déjà confirmé ; **RECOMMANDÉ** pour les specs automatisées |
| `free@audit.test` | `<mot de passe du seed, cf. backend/scripts/seed_billing_audit.py>` | `backend/scripts/seed_billing_audit.py` | Venv Python actif + script `seed_billing_audit.py` exécuté | Scénarios d'audit de plan free (write protection) |
| `starter@audit.test` | `<mot de passe du seed, cf. backend/scripts/seed_billing_audit.py>` | `backend/scripts/seed_billing_audit.py` | Venv Python actif + script `seed_billing_audit.py` exécuté | Scénarios paywall plan Gestion (19 euros/mois) |
| `pro@audit.test` | `<mot de passe du seed, cf. backend/scripts/seed_billing_audit.py>` | `backend/scripts/seed_billing_audit.py` | Venv Python actif + script `seed_billing_audit.py` exécuté | Scénarios paywall plan Pilotage (39 euros/mois) et quotas illimités |
| `demo@gerersci.fr` | `<mot de passe du seed, cf. backend/scripts/seed_billing_audit.py>` | `backend/scripts/seed_dev_data.py` | Venv Python actif + script `seed_dev_data.py` exécuté | Données demo complètes (1 SCI, 2 biens, baux, loyers). **Déconseillé comme compte E2E principal.** Dérive documentée : ce compte est cité dans `docs/GUIDE-RECETTE.md` et dans `meta.credentials` du cahier ; à corriger vers `test@gerersci.fr`. |
| `sophie@gerersci.fr` | `<mot de passe du seed, cf. backend/scripts/seed_billing_audit.py>` | `backend/scripts/seed_marketing_data.py` | Venv Python actif + script `seed_marketing_data.py` exécuté | Utilisé exclusivement par `frontend/e2e/validation/full-visual-audit.spec.ts` |

---

## Stratégies d'authentification E2E, par ordre de fiabilité

| Rang | Stratégie | Compte | Prérequis | Commentaire |
|---|---|---|---|---|
| 1 | Variables `E2E_EMAIL` / `E2E_PASSWORD` avec `test@gerersci.fr` | `test@gerersci.fr` | `supabase db reset` + `pnpm` | Zéro Python, email pré-confirmé, réplicable en CI. **RECOMMANDÉ.** |
| 2 | Login UI réel via le formulaire `/login` en mode mot de passe (`signInWithPassword`, `frontend/src/routes/login/+page.svelte:51`) | Tout compte existant | Stack locale complète | Immunisé au défaut de clé de session ; plus lent. Utilisé par `billing-audit.spec.ts` et `full-visual-audit.spec.ts`. |
| 3 | Comptes `*@audit.test` via `seed_billing_audit.py` | `free@audit.test`, `starter@audit.test`, `pro@audit.test` | Venv Python + script de seed | Indispensable pour les scénarios de paywall, de quota et de plan Stripe. |
| 4 | `E2E_AUTH_TOKEN` (mode 3 de `frontend/e2e/fixtures/auth.fixture.ts`) | N/A | JWT forgé manuellement | JWT non signé par GoTrue. **À PROSCRIRE.** Un token forgé ne traverse pas le middleware d'abonnement et peut faussement valider un parcours protégé. |

---

## Règle d'assertion d'authentification

> **Une étape d'authentification DOIT vérifier qu'un élément du DOM réservé aux utilisateurs authentifiés est rendu.**
>
> Elle ne doit JAMAIS se contenter de `localStorage.getItem(...)` ni de `fs.existsSync(...)` comme preuve d'une session active.
>
> **Motif :** `frontend/e2e/production/auth.setup.ts` (lignes 63-66 et 73) effectue exactement ces vérifications fichier/storage et peut passer au vert en produisant une session non authentifiée. Tout scénario héritant de ce pattern peut valider un faux-positif d'authentification.

---

## Variables d'environnement E2E

| Nom | Valeur locale | Rôle |
|---|---|---|
| `E2E_BASE_URL` | `http://localhost:5173` | URL de base du frontend SvelteKit en dev |
| `E2E_EMAIL` | `test@gerersci.fr` | Email du compte de test principal |
| `E2E_PASSWORD` | `<mot de passe du seed, cf. supabase/seed.sql>` | Mot de passe du compte de test principal |
| `VITE_SUPABASE_URL` | `http://localhost:54321` | URL de l'API Supabase locale (Kong) |
| `E2E_AUTH_TOKEN` | _(déconseillé - voir rang 4)_ | JWT forgé - à proscrire |
| `E2E_MAGIC_LINK_URL` | `<URL complète du magic link, non définie par défaut>` | URL complète du magic link à visiter directement (pas une URL de base Mailpit) |

> **Note sur `VITE_SUPABASE_URL`.** Utiliser `localhost` et non `127.0.0.1`. La dérivation de la clé de session par le client Supabase peut différer selon l'hôte. Cette hypothèse doit être validée par le scénario `AUTH-000` lors de la première exécution en stack réelle.

---

## Réinitialisation des données

```bash
supabase db reset
```

> **AVERTISSEMENT.** Cette commande est **DESTRUCTIVE** : elle supprime l'intégralité de la base locale et rejoue toutes les migrations depuis `001_init`. Elle recrée automatiquement le compte `test@gerersci.fr` (email pré-confirmé, confirmation désactivée via `supabase/config.toml:212`). Ne jamais l'exécuter sur un environnement partagé ni sans confirmation explicite du responsable du run.

---

## Ce qui n'est pas exécutable sans venv Python

Les éléments suivants requièrent un environnement Python configuré (`cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`) :

- Tous les scénarios de **paywall** (plan starter, pro, quotas de biens et de SCI)
- Tous les scénarios de **quota de plan** (`SubscriptionService.enforce_limit`)
- Tous les scénarios **Stripe** (webhooks, checkout, portail client)
- `scripts/quality-gate.sh` (à la racine du dépôt)
- `PYTHONPATH=. pytest` (suite pytest complète, 88 fichiers de test)
- `backend/scripts/seed_billing_audit.py` (comptes `*@audit.test`)
- `backend/scripts/seed_dev_data.py` (compte `demo@gerersci.fr`)
- `backend/scripts/seed_marketing_data.py` (compte `sophie@gerersci.fr`)
