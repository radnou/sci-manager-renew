# Guide de Recette Interactif — GérerSCI

## Comment utiliser le cahier de recette

### 1. Ouvrir l'application locale
```
http://localhost:5173
📧 demo@gerersci.fr / 🔑 password123
```

### 2. Suivre les tests
Ouvrez le fichier `docs/cahier-de-recette-interactif.json` et suivez les étapes de chaque test.

### 3. Remplir les résultats
Pour chaque test, remplissez 2 champs :

| Champ | Valeurs possibles |
|-------|-------------------|
| `resultat` | `OK` / `KO` / `PARTIEL` / `SKIP` |
| `commentaire` | Texte libre (bug, suggestion, capture d'écran) |

### 4. Me renvoyer le fichier
Copiez-collez le contenu du JSON modifié dans le chat, ou envoyez juste les tests qui ont un résultat `KO` ou `PARTIEL`.

**Format rapide** (si vous préférez ne pas éditer le JSON) :
```
PUB-001: OK
PUB-002: KO — le prix TTC n'est pas affiché
AUTH-001: OK
BIEN-002: PARTIEL — onglet Rentabilité affiche NaN
```

## Résumé des 40 tests

| Domaine | Tests | Priorité |
|---------|-------|----------|
| Public (landing, pricing, simulateurs, légal) | 6 | P0-P1 |
| Authentification (login, magic link, protection) | 3 | P0-P1 |
| Dashboard (KPIs, cartes SCI, activité) | 3 | P0-P1 |
| Navigation (sidebar, breadcrumbs, thème) | 3 | P0-P1 |
| SCI (overview, infos légales, export CSV) | 3 | P0-P1 |
| Biens (grille, fiche 6 onglets, loyer, charge, quittance) | 6 | P0-P1 |
| Associés | 1 | P1 |
| Assemblées Générales | 2 | P1 |
| Fiscalité (paywall, exercice, analyse, PDF, report 2042) | 5 | P0-P1 |
| Documents | 1 | P0 |
| Finances | 1 | P0 |
| Exploitation | 1 | P1 |
| Settings (accents, dropdown, notifications) | 2 | P1 |
| Notifications | 1 | P1 |
| Résilience (offline) | 1 | P1 |
| UI/UX (dark mode, performance) | 2 | P2 |

## Données seedées

| Donnée | Détail |
|--------|--------|
| 2 SCI | Belleville Patrimoine (IR) + Horizon Lyon (IS) |
| 4 biens | 3 Paris + 1 Lyon |
| 4 locataires | Avec baux actifs |
| 44 loyers | Mix payé / impayé / en attente |
| 64 charges | 4 types × 4 biens × 4 trimestres |
| 4 PNO | MAIF + AXA |
| 2 AG | AGO 2024 + AGE 2025 |
| 2 mouvements de parts | Cession + souscription |
| Fiscalité | 2024 + 2025 |
| Plan | Pro (toutes features débloquées) |
