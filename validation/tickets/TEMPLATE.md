<!-- Template de ticket de validation PO — copier ce fichier pour chaque feature, bug ou chore à valider. -->

| Champ | Valeur |
|---|---|
| Type | `Feature` / `Bug` / `Chore` / `Spike` / `Security` / `Tech debt` / `Product decision` |
| Priorité | `P0` / `P1` / `P2` / `P3` |
| Area | `Frontend` / `Backend` / `Infra` / `Billing` / `Fiscalité` / `Docs` |
| Risk | `Low` / `Medium` / `High` |
| IDs cahier liés | _ex : `FISC-001, FISC-002`_ |

---

## Objectif

_Décris en une ou deux phrases ce que ce ticket cherche à atteindre du point de vue du produit. Quel problème est résolu ? Quelle valeur est livrée ?_

## Contexte

_Donne le contexte nécessaire à la compréhension : contrainte métier, décision de design, ticket parent, etc. Cite les fichiers ou endpoints concernés si pertinent._

## Critères d'acceptation

_Liste chaque critère comme une assertion vérifiable. Un critère = un comportement observable par le PO._

- [ ] <critère 1>
- [ ] <critère 2>
- [ ] <critère 3>

## Scénarios de validation

_Référence les IDs du cahier `docs/cahier-de-recette-interactif.json` pour chaque type de parcours. Un scénario sans référence est une zone d'ombre._

- [ ] Parcours nominal - ID cahier : `<DOMAINE-NNN>` ou `HORS-CAHIER`
- [ ] Cas d'erreur - ID cahier : `<DOMAINE-NNN>` ou `HORS-CAHIER`
- [ ] Cas limite - ID cahier : `<DOMAINE-NNN>` ou `HORS-CAHIER`
- [ ] Régression - ID cahier : `<DOMAINE-NNN>` ou `HORS-CAHIER`

## Risques

_Quels risques subsistent si ce ticket est accepté en l'état ? Cite les dépendances non testées, les données de test manquantes, les environnements non couverts._

## Notes techniques

_Références internes : fichiers modifiés, endpoints touchés, migrations, flags de feature. À remplir par le développeur._

## Validation

- Statut : `PASS` / `FAIL` / `BLOCKED` / `NOT_TESTED`
- Date : `<AAAA-MM-JJ>`
- Version : `<sha-court>` ou `<numéro de build>`
- Preuves : _lien ou chemin relatif vers rapport Playwright, PNG annoté, extrait de log_

---

## Règle de traçabilité

Tout scénario listé dans la section « Scénarios de validation » DOIT référencer un ID du cahier `docs/cahier-de-recette-interactif.json` (format `DOMAINE-NNN`), ou porter explicitement la mention `HORS-CAHIER` si aucun ID ne correspond. Un scénario sans référence est considéré non traçable et bloque la décision `ACCEPT`.
