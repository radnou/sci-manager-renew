---
name: local-environment
description: Diagnostiquer et démarrer la stack locale GererSCI (OrbStack, Supabase, backend 8001, frontend 5173) dans l'ordre des dépendances, et poser les variables E2E canoniques. À utiliser avant toute recette locale, et quand un test E2E échoue pour une raison qui ressemble à un problème d'environnement.
---

# Environnement local GererSCI

## Portée

Cette skill **diagnostique** l'environnement puis **propose** de le démarrer. Elle ne remplace pas les lanceurs existants : `start-dev.sh` (racine) et `scripts/start-real-stack.sh` font le démarrage. Leur défaut est de présupposer que Docker tourne, que `frontend/node_modules` existe et qu'un venv Python est présent. Quand ce n'est pas le cas, ils échouent tard et de façon opaque. Le rôle de cette skill est de vérifier les prérequis **avant**, dans l'ordre des dépendances, et de nommer la remédiation exacte.

Ne jamais réécrire un lanceur de stack. Ne jamais modifier `docker-compose*.yml`, `supabase/config.toml`, `.gitignore` ni de code métier.

## Contrainte shell obligatoire

`node` et `pnpm` ne résolvent qu'en **shell de login** sur cette machine (nvm en chargement paresseux). En shell non-login, `node --version` échoue avec `command not found: _lazy_nvm_load`.

Toute commande Node passe donc par :

```bash
zsh -lc 'cd frontend && <commande>'
```

Playwright se lance toujours depuis `frontend/` : les `--config=e2e/...` des scripts npm sont relatifs à ce répertoire.

## Étape 1 — Diagnostic (bloquant, dans cet ordre)

Chaque étape conditionne la suivante. S'arrêter à la première qui échoue, proposer la remédiation, attendre l'accord, puis reprendre au même point.

| # | Vérification | Commande | Si KO |
|---|---|---|---|
| 1 | Socket Docker | `test -S ~/.orbstack/run/docker.sock && echo OK \|\| echo KO` | `orb start` — **~30 à 60 s à froid** |
| 2 | Daemon répond | `docker info --format '{{.ServerVersion}}'` | Attendre la fin de l'étape 1 |
| 3 | Supabase local | `supabase status` | `supabase start` — **plusieurs minutes au 1er run** (téléchargement des images) |
| 4 | Base seedée | `psql "postgresql://postgres:postgres@127.0.0.1:54322/postgres" -tAc "select count(*) from auth.users where email='test@gerersci.fr'"` | `supabase db reset` — **DESTRUCTIF**, voir garde-fous |
| 5 | Dépendances frontend | `test -d frontend/node_modules && echo OK \|\| echo KO` | `zsh -lc 'cd frontend && pnpm install'` — **~1 à 3 min** |
| 6 | Fichier d'environnement | `test -f .env && echo OK \|\| echo KO` (noter : `frontend/vite.config.ts` a `envDir: '..'`, le `.env` est lu **à la racine**) | Proposer la copie depuis `.env.example` — **création de fichier, demander l'accord** |
| 7 | Venv backend | `test -d backend/venv -o -d backend/.venv && echo OK \|\| echo ABSENT` | **Non bloquant** pour la recette frontend. Voir « Ce qui est bloqué sans Python ». |
| 8 | Ports libres | `lsof -nP -iTCP:5173 -iTCP:8001 -sTCP:LISTEN` | `start-dev.sh` libère lui-même 8001, 5173 et 5174-5179 |

### Format de sortie du diagnostic

Toujours produire ce tableau, jamais un texte libre :

```
| Étape | Statut | Remédiation |
|-------|--------|-------------|
| Socket Docker | KO | `orb start` (~30-60 s) |
| ... | OK | — |
```

Statuts autorisés : `OK`, `KO — remédiable maintenant`, `KO — remédiable, ~N min`, `ABSENT — non bloquant`.

Terminer par une ligne de verdict :

```
PRÊT POUR : recette frontend [OUI/NON] · scénarios Python (paywall, quotas, Stripe) [OUI/NON]
```

La distinction de durée existe pour une raison : au premier passage, `orb start` puis `supabase start` prennent plusieurs minutes. Sans cette annotation, l'utilisateur croit que la commande est figée.

## Étape 2 — Variables canoniques

Poser exactement ces variables pour toute exécution E2E locale :

```bash
export VITE_SUPABASE_URL=http://localhost:54321
export E2E_BASE_URL=http://localhost:5173
export E2E_EMAIL=test@gerersci.fr
export E2E_PASSWORD=testpassword123
```

**`localhost` et non `127.0.0.1`.** Hypothèse : `frontend/src/lib/supabase.ts:6` appelle `createClient(url, key)` sans `auth.storageKey`, donc supabase-js dérive la clé de session du **premier segment** du hostname, alors que `frontend/e2e/fixtures/auth.fixture.ts:65-66` et `frontend/e2e/production/auth.setup.ts:40-41` la calculent avec le **hostname complet**. Un hôte sans point aligne les deux.

Cette hypothèse **n'est pas vérifiée** (`frontend/node_modules` était absent au moment de l'audit). Le scénario `AUTH-000` est un test falsifiant : le lancer d'abord avec `127.0.0.1`. **S'il passe, l'hypothèse est fausse** — retirer cette note et re-diagnostiquer.

Ce qui tient dans tous les cas : `auth.setup.ts:63-66,73` n'assert que sur sa propre clé et sur `fs.existsSync(AUTH_FILE)`, jamais sur un état authentifié rendu. C'est un générateur de faux verts indépendant de la formule.

Ports de référence (source : `start-dev.sh:26-30` et `supabase/config.toml`) : frontend 5173, backend 8001, Supabase API 54321, Postgres 54322, Studio 54323, Mailpit 54324.

## Étape 3 — Démarrage

Une fois le diagnostic vert, proposer **une** de ces commandes, selon le besoin, et attendre l'accord :

| Besoin | Commande |
|---|---|
| Stack de développement complète | `./start-dev.sh` |
| Stack conteneurisée façon production | `zsh -lc 'CHECK_ONLY=1 ./scripts/start-real-stack.sh'` puis sans `CHECK_ONLY` |
| Frontend seul (backend déjà up) | `zsh -lc 'cd frontend && pnpm dev'` |

Vérification post-démarrage :

```bash
curl -sf -o /dev/null -w '%{http_code}\n' http://localhost:8001/docs
curl -sf -o /dev/null -w '%{http_code}\n' http://localhost:5173
curl -sf http://localhost:8001/health/ready | jq .
```

Noter que les chemins de santé réels sont `/health`, `/health/live` et `/health/ready` — **sans** préfixe `/api/v1` (le router est monté sans préfixe, `backend/app/main.py:830`).

## Étape 4 — Tests

| Portée | Commande |
|---|---|
| E2E validation P0 (31 tests) | `zsh -lc 'cd frontend && pnpm test:e2e:validate:p0'` |
| E2E validation complète (118 tests) | `zsh -lc 'cd frontend && pnpm test:e2e:validate'` |
| Unitaires frontend | `zsh -lc 'cd frontend && pnpm test:unit -- --run'` |
| Modules critiques (seuils lignes/fonctions/instructions 90, branches 85) | `zsh -lc 'cd frontend && pnpm test:high-value'` |
| Typage | `zsh -lc 'cd frontend && pnpm check'` |
| Backend | `cd backend && PYTHONPATH=. pytest` — **nécessite le venv** |
| Gate qualité complet | `./scripts/quality-gate.sh` — **nécessite le venv** |

Rapport Playwright : `frontend/playwright-report/validation/index.html`.

## Ce qui est bloqué sans venv Python

À dire explicitement, jamais à contourner ni à promettre :

- tous les scénarios **paywall**, **quotas de plan** et **Stripe** ;
- `backend/scripts/seed_dev_data.py`, `seed_billing_audit.py`, `seed_marketing_data.py` ;
- `backend/scripts/stripe_test_workflow.py` ;
- `scripts/quality-gate.sh` et pytest.

Le `pytest` système est cassé (`bad interpreter`) : il faut un venv dédié, pas le binaire global.

## Garde-fous

**Avant toute commande destructive, afficher : la commande exacte, la cible, l'impact, le risque, les données concernées. Puis attendre l'accord explicite.**

| Commande | Impact | Règle |
|---|---|---|
| `supabase db reset` | **Efface toute la base locale.** Rejoue les 48 migrations et `supabase/seed.sql`. Recrée `test@gerersci.fr`. Perd toute donnée saisie à la main. | Confirmation obligatoire |
| `docker compose down -v` | **Détruit les volumes**, y compris les données Supabase | Confirmation obligatoire |
| `docker system prune` | Supprime images, conteneurs, caches partagés avec d'autres projets | Confirmation obligatoire |
| Écriture de `.env` ou `frontend/.env` | Crée ou écrase un fichier de configuration | Confirmation obligatoire, montrer le contenu prévu |
| `docker compose down` (sans `-v`) | Arrête des services potentiellement utilisés par un autre processus | Confirmation obligatoire |

Jamais de secret affiché. Pour vérifier la présence d'une variable, tester son existence, pas sa valeur :

```bash
printenv STRIPE_SECRET_KEY >/dev/null && echo "présent" || echo "absent"
```

Ne jamais copier la moindre valeur de `.env` dans une sortie, un rapport ou un message.
