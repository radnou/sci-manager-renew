<!-- Template de rapport de recette de sprint — à compléter après chaque cycle de validation PO. -->

| Champ | Valeur |
|---|---|
| Date | `<AAAA-MM-JJ>` |
| Commit validé | `<sha-court>` |
| Branche | `<nom-de-branche>` |
| Environnement | `local` / `staging` / `production` |
| Périmètre déterminé par | `<source principale, ex : GitHub Project #7 sprint <N>>` - rang de repli : `<ex : tickets P0 fermés depuis le dernier rapport>` |
| Testeur | `<prénom nom>` |

---

## Décision globale

**`ACCEPT`** / **`ACCEPT_WITH_RESERVES`** / **`REJECT`**

_Justification en 2 à 3 lignes : pourquoi cette décision ? Quels critères sont remplis ou manquants ? Quelles réserves bloquent une acceptation pleine ?_

---

## Synthèse

> **AVERTISSEMENT.** Ne jamais afficher de taux de réussite agrégé (ex : « 17/20 tests passent ») mêlant preuves mockées et preuves de stack réelle. Ces deux catégories ne prouvent pas la même chose. Les présenter séparément dans les sections « Preuves » ci-dessous.

| Ticket / ID | Intitulé | Statut | Preuve |
|---|---|---|---|
| `<DOMAINE-NNN>` ou `#<numéro>` | `<intitulé>` | `PASS` / `FAIL` / `BLOCKED` / `NOT_TESTED` | `<chemin PNG ou "cf. rapport Playwright">` |

---

## Preuves - contrat UI (mocké, page.route) - ne prouve PAS le backend

_Liste des specs Playwright dont les requêtes réseau sont interceptées via `page.route` (import `../fixtures/api-mocks`). Le résultat `PASS` prouve le contrat UI uniquement et ne constitue pas une preuve de comportement backend._

| Spec | Rapport | Statut global |
|---|---|---|
| `frontend/e2e/validation/<spec>.spec.ts` | `frontend/playwright-report/validation/index.html` | `PASS` / `FAIL` / `BLOCKED` |

---

## Preuves - stack réelle

_Liste des specs ou scénarios manuels exécutés contre une stack complète (frontend + backend + Supabase local ou staging). Ces preuves valident le comportement de bout en bout._

| Spec ou scénario | Environnement | Rapport ou preuve | Statut global |
|---|---|---|---|
| `frontend/e2e/validation/<spec>.spec.ts` ou `<ID cahier> - manuel` | `local` / `staging` | `<chemin ou description>` | `PASS` / `FAIL` / `BLOCKED` |

---

## Non couvert

_Critères d'acceptation non testés dans ce rapport, avec la raison explicite._

| Critère | Raison de non-couverture |
|---|---|
| `<critère>` | `<environnement non disponible / données de test manquantes / scénario non écrit / hors périmètre sprint>` |

---

## Anomalies

| ID bug | Titre | Type | Priorité | Rapport détaillé |
|---|---|---|---|---|
| `BUG-<NNN>` | `<titre>` | `bug fonctionnel` / `anomalie UX` / `régression` / `problème d'environnement` / `problème de données de test` / `manque de test` / `problème de documentation` | `P0` / `P1` / `P2` / `P3` | `validation/reports/BUG-<NNN>.md` |

---

## Risques résiduels

_Risques identifiés mais non bloquants pour la décision, à surveiller lors du prochain cycle._

- `<risque 1>`
- `<risque 2>`

---

## Actions proposées

_Chaque action est marquée **À VALIDER** : aucune n'est exécutée sans accord explicite du PO ou du responsable technique._

- **À VALIDER** : `<action - ex : créer une issue GitHub pour le scénario FISC-003 manquant>`
- **À VALIDER** : `<action - ex : passer le ticket #42 en statut "Done" dans le GitHub Project #7>`
- **À VALIDER** : `<action - ex : déclencher le déploiement en staging>`

---

## Traçabilité

| ID cahier | Scénario | Spec Playwright | Statut |
|---|---|---|---|
| `<DOMAINE-NNN>` | `<intitulé du test dans le cahier>` | `frontend/e2e/validation/<spec>.spec.ts` / `manuel` / `non couvert` | `PASS` / `FAIL` / `BLOCKED` / `NOT_TESTED` |

**Trois classes de couverture :**

- **Automatisé :** scénario du cahier couvert par une spec Playwright. Préciser si mockée (niveau de preuve `MOCKÉ`) ou stack réelle (niveau de preuve `STACK RÉELLE`).
- **Manuel uniquement :** scénario du cahier non automatisé, exécuté manuellement par le testeur lors de ce cycle.
- **Automatisé hors cahier :** spec Playwright existante qui ne correspond à aucun ID de `docs/cahier-de-recette-interactif.json`. À enregistrer dans le cahier ou à marquer `HORS-CAHIER` dans le ticket associé.

---

> **Règle.** Aucun test non exécuté dans ce rapport ne doit apparaître avec le statut `PASS`. Tout élément non testé doit porter le statut `NOT_TESTED`, quel qu'en soit le motif.
