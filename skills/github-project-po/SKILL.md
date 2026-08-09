---
name: github-project-po
description: Inspecter le GitHub Project #7 gerer-sci, le comparer à un modèle cible de gestion produit solo, et produire le script gh exact pour l'aligner — sans jamais l'exécuter. À utiliser pour préparer le suivi de recette et auditer la qualité des tickets.
---

## Portée

Cette skill inspecte et propose. Elle n'exécute aucune mutation GitHub : ni création, ni
modification, ni fermeture d'issue, ni changement de statut, de priorité, d'itération, ni
archivage, ni suppression. Toute action irréversible exige un accord explicite.

## État réel du projet

Projet numéro `7`, titre `gerer-sci`, propriétaire `radnou`,
identifiant `PVT_kwHOAE8e5M4Bfz3Y`, URL `https://github.com/users/radnou/projects/7`,
lié au dépôt `radnou/sci-manager-renew`.

**Champs existants :** `Title`, `Assignees`, `Status`, `Labels`, `Linked pull requests`,
`Milestone`, `Repository`, `Reviewers`, `Parent issue`, `Sub-issues progress`, `Created`,
`Updated`, `Closed`, `Priority`, `Size`, `Estimate`, `Iteration`.

**Options actuelles :**

| Champ | Options |
|-------|---------|
| Status | `Backlog`, `Ready`, `In progress`, `In review`, `Done` |
| Priority | `P0`, `P1`, `P2` |
| Size | `XS`, `S`, `M`, `L`, `XL` |
| Iteration | Aucune itération configurée |

**Contenu :** 1 item (PR #4 « feat: design system light-first + accessibility overhaul »,
Status `Backlog`). 0 issue ouverte. 9 labels par défaut GitHub uniquement (`bug`,
`documentation`, `duplicate`, `enhancement`, `help wanted`, `good first issue`, `invalid`,
`question`, `wontfix`). 0 milestone.

## Modèle cible

| Élément | Valeurs cibles |
|---------|----------------|
| Status | `Backlog`, `Ready`, `In progress`, `Validation`, `Blocked`, `Done` |
| Priority | `P0`, `P1`, `P2`, `P3` |
| Type (nouveau) | `Feature`, `Bug`, `Chore`, `Spike`, `Security`, `Tech debt`, `Product decision` |
| Area (nouveau) | `Frontend`, `Backend`, `Infra`, `Billing`, `Fiscalité`, `Docs` |
| Risk (nouveau) | `Low`, `Medium`, `High` |
| Validation status (nouveau) | `NOT_TESTED`, `PASS`, `FAIL`, `BLOCKED` |
| Release (nouveau) | Texte libre |

Les valeurs de `Validation status` doivent correspondre exactement aux statuts utilisés par
la skill `validate-sprint` et par `validation/reports/TEMPLATE-SPRINT-REPORT.md`. Tout écart
casse la traçabilité.

## Écart

| Élément | Réel | Cible | Action | Faisable en gh ? |
|---------|------|-------|--------|------------------|
| Status : Validation | Absent | Requis | Ajouter l'option | Interface GitHub (pas de CLI) |
| Status : Blocked | Absent | Requis | Ajouter l'option | Interface GitHub (pas de CLI) |
| Status : In review | Présent | Non listé | Conserver ou fusionner avec Validation | Décision utilisateur |
| Priority : P3 | Absent | Requis | Ajouter l'option | Interface GitHub (pas de CLI) |
| Champ Type | Absent | Requis | Créer le champ | Oui : `gh project field-create` |
| Champ Area | Absent | Requis | Créer le champ | Oui : `gh project field-create` |
| Champ Risk | Absent | Requis | Créer le champ | Oui : `gh project field-create` |
| Champ Validation status | Absent | Requis | Créer le champ | Oui : `gh project field-create` |
| Champ Release | Absent | Requis | Créer le champ | Oui : `gh project field-create` |
| Itération | Aucune configurée | A créer | Créer une itération | Mutation GraphQL (accord requis) |

**Réserve sur les options de champs existants.** L'ajout d'une option à un champ `Status` ou
`Priority` existant n'est pas couvert par `gh project field-create`. Il se fait soit par
l'interface web de GitHub, soit par une mutation GraphQL `updateProjectV2Field`. Dans les deux
cas, l'utilisateur réalise l'opération lui-même.

## Commandes d'inspection

Ces commandes sont en lecture seule et peuvent être exécutées librement :

```bash
gh api graphql -f query='{repository(owner:"radnou",name:"sci-manager-renew"){projectsV2(first:10){nodes{number title url}}}}'

gh project field-list 7 --owner radnou --limit 30 --format json

gh project item-list 7 --owner radnou --limit 100 --format json

gh issue list --repo radnou/sci-manager-renew --state open --json number,title,labels,body

gh label list --repo radnou/sci-manager-renew --limit 40

gh api repos/radnou/sci-manager-renew/milestones
```

## Script de migration proposé

```bash
# À EXÉCUTER PAR L'UTILISATEUR — non exécuté par Claude

gh project field-create 7 --owner radnou --name "Type" \
  --data-type SINGLE_SELECT \
  --single-select-options "Feature,Bug,Chore,Spike,Security,Tech debt,Product decision"

gh project field-create 7 --owner radnou --name "Area" \
  --data-type SINGLE_SELECT \
  --single-select-options "Frontend,Backend,Infra,Billing,Fiscalité,Docs"

gh project field-create 7 --owner radnou --name "Risk" \
  --data-type SINGLE_SELECT \
  --single-select-options "Low,Medium,High"

gh project field-create 7 --owner radnou --name "Validation status" \
  --data-type SINGLE_SELECT \
  --single-select-options "NOT_TESTED,PASS,FAIL,BLOCKED"

gh project field-create 7 --owner radnou --name "Release" --data-type TEXT
```

Pour `Status` (ajouter `Validation`, `Blocked`) et `Priority` (ajouter `P3`) : utiliser
l'interface web GitHub ou une mutation GraphQL `updateProjectV2Field`. Ne pas supposer
qu'une syntaxe `gh project field-update` ou équivalente existe : si la commande exacte
n'est pas connue avec certitude, indiquer « à faire via l'interface GitHub ».

Pour créer une itération : mutation GraphQL (accord requis avant exécution).

## Audit de la qualité des tickets

Pour chaque ticket retenu, vérifier par lecture du corps (commande `gh issue list` ci-dessus) :
- Présence de la section « Critères d'acceptation ».
- Présence de la section « Scénarios de validation ».
- Champ Priority renseigné.
- Champ Type renseigné (une fois le champ créé).

Produire une liste de validation priorisée : P0 en premier, puis P1, puis le reste.
Les tickets sans critères d'acceptation sont listés comme `NOT_TESTED -- critères manquants`
dans le rapport de sprint (cohérence avec la skill `validate-sprint`).

## Format d'issue

Référence : `validation/tickets/TEMPLATE.md`. Format attendu pour tout nouveau ticket :

```markdown
## Objectif
## Contexte
## Critères d'acceptation
- [ ] ...
## Scénarios de validation
- [ ] Parcours nominal
- [ ] Cas d'erreur
- [ ] Cas limite
- [ ] Régression
## Risques
## Notes techniques
## Validation
- Statut :
- Date :
- Version :
- Preuves :
```

## Garde-fous

Le jeton CLI `gh` est authentifié avec la portée `project` (vérifiable via `gh auth status`).
Les mutations sont donc techniquement possibles, ce qui rend la retenue d'autant plus
nécessaire : la retenue est une règle, pas une limite technique.

Avant toute proposition d'action irréversible, afficher :
- la commande exacte ;
- la cible (champ, item, issue) ;
- l'impact attendu ;
- le risque en cas d'erreur ;
- les données concernées.

Puis attendre l'accord explicite.

Interdictions absolues :
- Ne jamais afficher de jeton ni de valeur de secret.
- Ne jamais créer une itération, un label ou une issue pour combler un backlog vide.
- Ne jamais exécuter le script de migration sans accord préalable.
