---
name: validate-sprint
description: Conduire une recette de sprint GererSCI de bout en bout — déterminer le périmètre, sélectionner les scénarios du cahier de recette, exécuter les tests pertinents, capturer les preuves, classer les résultats et produire un rapport lisible par un Product Owner. Ne corrige jamais le code et ne modifie jamais GitHub sans accord.
---

## Portée

Cette skill conduit la recette d'un sprint GererSCI. Elle ne corrige jamais le code source,
ne modifie jamais les tickets ou le projet GitHub sans accord explicite au moment de l'action,
et ne remplit jamais le champ `resultat` du cahier pour un test qui n'a pas été exécuté.

## Étape 1 — Déterminer le périmètre

La chaîne de repli s'arrête au premier rang non vide. Le rapport annonce toujours le rang
retenu.

**Rang 1 : argument explicite (prioritaire).** IDs de scénarios ou numéros d'issue passés
directement à la commande (ex. `FISC-001,FISC-002`).

**Rang 2 : itération active du projet.**
```bash
gh project field-list 7 --owner radnou --format json | jq '.fields[] | select(.name=="Iteration")'
```
Aucune itération n'est configurée sur le projet #7 à ce jour.

**Rang 3 : items dont le Status vaut `Ready`, `In progress` ou `Validation`.**
```bash
gh project item-list 7 --owner radnou --limit 100 --format json
```
Le projet #7 contient 1 seul item (PR #4) et 0 issue ouverte.

**Rang 4 : issues ouvertes.**
```bash
gh issue list --repo radnou/sci-manager-renew --state open --json number,title,labels,body
```

**Rang 5 : `TODO.md`**, sections « Aujourd'hui » et « Cette semaine ».

**Rang 6 : `BACKLOG.md`**, section « Ordre d'exécution recommandé ».

**Rang 7 : commits récents.** Marquer le rapport `TRAÇABILITÉ FAIBLE — périmètre déduit du code`.
```bash
git log $(git describe --tags --abbrev=0 2>/dev/null || echo HEAD~20)..HEAD --oneline --name-only
```

**Rang 8 : aucun périmètre trouvé.** S'arrêter et demander. Ne jamais inventer un sprint,
créer une itération, un label ou une issue pour combler le vide.

## Étape 2 — Lire les critères d'acceptation

Pour chaque ticket retenu aux rangs 1 à 4, vérifier la présence d'une section « Critères
d'acceptation » et d'une section « Scénarios de validation » dans le corps du ticket. Tout
ticket qui en est dépourvu est listé comme `NOT_TESTED -- critères manquants`. Ne pas inventer
de critères.

## Étape 3 — Sélectionner les scénarios

Registre de référence : `docs/cahier-de-recette-interactif.json` (41 tests). Vocabulaire du
cahier : `OK` / `KO` / `PARTIEL` / `SKIP`. Sélection par domaine :
```bash
jq '.tests[] | select(.domaine=="<Domaine>")' docs/cahier-de-recette-interactif.json
```

**Matrice de traçabilité (trois classes, non bijective dans aucun sens) :**

| Classe | Identifiants cahier | Spec `frontend/e2e/validation/` |
|--------|---------------------|----------------------------------|
| Automatisé | PUB, AUTH, DASH, NAV, SCI, BIEN, AG, FISC, DOC, FIN, SET, NOTIF | landing, auth, dashboard, navigation, sci-management, bien-management, assemblees-generales, fiscalite, documents, finances, settings-account, notifications |
| Manuel uniquement (ID sans spec) | ASSOC-001, EXPL-001, OFFLINE-001, DARK-001, PERF-001 | -- |
| Automatisé hors cahier (spec sans ID) | -- | paywall, onboarding, quittances, billing-audit, full-visual-audit |

**Dérives à signaler sans corriger :** `meta.credentials` pointe sur `demo@gerersci.fr` qui
exige un seed Python. `docs/GUIDE-RECETTE.md` annonce 40 tests alors qu'il y en a 41.

## Étape 4 — Vérifier les préconditions

Déléguer à la skill `skills/local-environment/SKILL.md`. Ne pas rejouer son diagnostic.

## Étape 5 — Afficher le plan et attendre l'accord

Avant toute exécution, afficher le plan structuré suivant et attendre la validation explicite :
- périmètre retenu et rang de repli utilisé ;
- scénarios sélectionnés (IDs et titres) ;
- commandes exactes qui seront lancées ;
- durée estimée ;
- ce qui ne sera pas testé et pourquoi.

## Étape 6 — Exécuter

Toute commande Node passe par un shell de login (nvm en chargement paresseux) :

```bash
# E2E P0 (31 tests)
zsh -lc 'cd frontend && pnpm test:e2e:validate:p0'

# E2E complet (118 tests)
zsh -lc 'cd frontend && pnpm test:e2e:validate'

# Spec ciblée
zsh -lc 'cd frontend && pnpm exec playwright test --config=e2e/playwright.validation.config.ts e2e/validation/<spec>.spec.ts'

# Unitaires
zsh -lc 'cd frontend && pnpm test:unit -- --run'

# Modules critiques
zsh -lc 'cd frontend && pnpm test:high-value'

# Typage
zsh -lc 'cd frontend && pnpm check'

# Backend (nécessite un venv)
cd backend && PYTHONPATH=. pytest tests/<fichier>.py -q
```

Variables E2E locales : `VITE_SUPABASE_URL=http://localhost:54321`,
`E2E_BASE_URL=http://localhost:5173`, `E2E_EMAIL=test@gerersci.fr`,
`E2E_PASSWORD=testpassword123`.

**Partition mocké / réel : établir AVANT l'exécution par le grep suivant.**
```bash
grep -l "fixtures/api-mocks" frontend/e2e/validation/*.spec.ts
```
13 des 17 specs importent `../fixtures/api-mocks` et interceptent le réseau via `page.route`.
Un vert y prouve le rendu du frontend contre des fixtures, pas le comportement du backend.
Exceptions sans mock : `auth.spec.ts`, `landing.spec.ts`, `billing-audit.spec.ts`,
`full-visual-audit.spec.ts`.

Côté backend, `backend/tests/conftest.py` monkeypatche tous les clients Supabase. Un pytest
vert ne prouve pas le comportement de la base de données réelle.

Rapport Playwright : `frontend/playwright-report/validation/index.html`.

**Le rapport comporte trois blocs séparés. Ne jamais agréger mocké et réel dans un même taux.**

1. `Preuves — contrat UI (mocké, page.route) — ne prouve PAS le backend`
2. `Preuves — stack réelle`
3. `Non couvert`

## Étape 7 — Contrôles complémentaires

À appliquer à chaque scénario :
- Erreurs de console navigateur et requêtes HTTP en erreur inattendue (4xx/5xx).
- Données réellement persistées en base :
  ```bash
  psql "postgresql://postgres:postgres@127.0.0.1:54322/postgres" -c "<requête>"
  ```
- Logs Docker du service concerné :
  ```bash
  docker compose logs --tail=100 backend
  docker logs --tail=100 supabase_db_sci-manager-renew
  ```
- Événements Stripe en mode test uniquement : déléguer à la skill `stripe-test-validation`.

## Étape 8 — Reproduire les échecs

Tout échec est rejoué au moins une seconde fois avant d'être déclaré bug. Les deux tentatives
sont consignées dans le rapport (contexte, résultat de chaque tentative). Un échec non
reproductible est signalé avec le type « problème d'environnement ».

## Étape 9 — Classer

**Statuts de résultat :**
- `PASS` : comportement observé conforme au résultat attendu du cahier.
- `FAIL` : comportement diffère du résultat attendu après au moins deux tentatives.
- `BLOCKED` : test non exécutable faute de précondition remplie (données, env, accès).
- `NOT_TESTED` : hors périmètre de cette session ou sans critère d'acceptation défini.

**Types d'anomalie (pour chaque `FAIL`) :**
- Bug fonctionnel : résultat incorrect selon la spécification.
- Anomalie UX : interface confuse ou inutilisable sans être techniquement fausse.
- Régression : comportement correct précédemment, cassé par une modification récente.
- Problème d'environnement : défaut lié à la configuration locale ou au seed de données.
- Problème de données de test : fixtures ou seed inadaptés au scénario.
- Manque de test : comportement attendu non couvert par un scénario existant.
- Problème de documentation : écart entre la spécification et la réalité du code.

## Étape 10 — Rapport

Remplir `validation/reports/TEMPLATE-SPRINT-REPORT.md`. Nommage du fichier produit :
`validation/reports/SPRINT-<AAAA-MM-JJ>.md`.
Pour chaque `FAIL`, ouvrir un fichier depuis `validation/reports/TEMPLATE-BUG.md`,
nommé `validation/reports/BUG-<ID>.md`.
Clé de jointure de bout en bout entre rapport, bug et cahier : l'ID du scénario (ex. `FISC-001`).

## Étape 11 — Propositions GitHub

Produire le corps complet des issues proposées (titre, objectif, critères d'acceptation,
scénarios de validation). Ne rien créer, ne rien modifier. Toute création, modification,
fermeture d'issue ou mutation du projet GitHub exige un accord explicite au moment de l'action.

## Preuves et artefacts

Traces et rapports HTML : restent dans `frontend/playwright-report/` et `frontend/e2e-artifacts/`
(répertoires gitignorés), référencés par chemin relatif dans le rapport de sprint.

`validation/reports/artifacts/` n'est pas gitignoré et ne reçoit que des PNG curatés illustrant
des cas `KO`. Jamais de `.zip` de trace, jamais de fichier `storageState`, jamais de `.har` :
une trace d'un run authentifié contient le JWT.

## Défauts connus à constater

Les défauts ci-dessous sont à consigner dans le rapport de sprint. CONSTATER, NE PAS CORRIGER.

| # | Localisation | Description |
|---|--------------|-------------|
| 1 | `backend/app/main.py:580` | Exemption healthcheck pour `/api/v1/health` et `/api/v1/health/ready` inexistants. Vrais chemins : `/health`, `/health/live`, `/health/ready`. En maintenance, `/health/live` renvoie 503 et le backend passe unhealthy. |
| 2 | `main.py:489` vs `:524` | `CORSMiddleware` enregistré avant `write_protection_middleware`. Ordre Starlette inverse : le 402 `subscription_required` (`:557-564`) part sans en-tête CORS. Contrôle : `curl -i -X POST -H 'Origin: http://localhost:5173' -H 'Authorization: Bearer <jeton>' http://localhost:8001/api/v1/scis` |
| 3 | `frontend/tests/e2e/` | 11 specs non atteintes par aucune des 5 configurations Playwright (toutes dans `frontend/e2e/`). Couverture fantôme. |
| 4 | `(app)/+layout.ts:41-44` | Erreurs de `fetchSubscriptionEntitlements` avalées silencieusement : backend éteint provoque une redirection vers `/welcome`. |
| 5 | `register/+page.svelte:109-115` | N'appelle jamais `goto` et affiche « vérifiez votre boîte mail » alors que `supabase/config.toml:212` a `enable_confirmations = false`. Impasse d'interface. |
| 6 | `stripe.py:363` | Course entre webhook et redirection : `success_url = /dashboard?upgraded=true` mais `(app)/+layout.ts` relit `is_active` immédiatement. |
| 7 | `auth.fixture.ts:65-66`, `auth.setup.ts:40-41,63-66,73` | Clé de session dérivée du hostname complet alors que `frontend/src/lib/supabase.ts:6` laisse supabase-js utiliser son défaut. `auth.setup.ts` peut passer au vert en produisant une session non authentifiée. Jouer le scénario précondition `AUTH-000` en premier. |

## Interdits

- Ne jamais corriger le code source, même si l'anomalie est évidente.
- Ne jamais agréger mocké et réel dans un même taux de réussite.
- Ne jamais conclure « le paiement fonctionne » depuis un résultat pytest.
- Ne jamais compter les 11 specs de `frontend/tests/e2e/` comme de la couverture effective.
- Ne jamais remplir le champ `resultat` du cahier pour un test qui n'a pas été exécuté.
- Ne jamais prétendre avoir exécuté un test qui ne l'a pas été.
- Ne jamais créer une itération, un label ou une issue pour combler un périmètre vide.
