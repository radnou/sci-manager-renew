<!-- Template de rapport de bug — un fichier par anomalie, nommé BUG-<NNN>-<slug>.md -->

| Champ | Valeur |
|---|---|
| ID | `BUG-<NNN>` |
| ID cahier lié | `<DOMAINE-NNN>` ou `HORS-CAHIER` |
| Date | `<AAAA-MM-JJ>` |
| Auteur | `<prénom nom>` |
| Statut | `Ouvert` / `En cours` / `Résolu` / `Fermé` / `Non reproductible` |

---

## Titre

_Formule le bug en une phrase : quoi + où + dans quelle condition. Ex : « Le montant TTC affiché sur le bilan mensuel est nul quand aucune charge n'est saisie. »_

`<titre>`

## Type

_Sélectionne le type le plus précis._

`bug fonctionnel` / `anomalie UX` / `régression` / `problème d'environnement` / `problème de données de test` / `manque de test` / `problème de documentation`

## Priorité

_P0 = bloquant pour la mise en production. P1 = bloquant pour la recette. P2 = gênant, non bloquant. P3 = cosmétique._

`P0` / `P1` / `P2` / `P3`

## Environnement

_Environnement dans lequel le bug a été constaté : local, staging, production. Inclure la version de navigateur si pertinente._

`<local / staging / production>` - navigateur : `<Chrome 130 / Firefox 131 / Safari 18 / autre>`

## Version ou commit

_SHA court du commit ou numéro de build au moment de l'observation._

`<sha-court>`

## Préconditions

_Décris l'état exact de l'application avant de reproduire : compte connecté, données présentes, étapes préalables obligatoires._

- Compte : `<test@gerersci.fr / autre>`
- Données : `<supabase db reset / seed exécuté / état spécifique>`
- État de départ : `<description>`

## Étapes de reproduction

_Une action par ligne, numérotées, à l'impératif. Aussi précises que possible._

1. <action 1>
2. <action 2>
3. <action 3>

## Résultat attendu

_Ce qui devrait se passer selon le critère d'acceptation ou le comportement documenté._

`<résultat attendu>`

## Résultat observé

_Ce qui se passe réellement. Être factuel, pas interprétatif._

`<résultat observé>`

## Fréquence

_À quelle fréquence le bug se produit-il lors des reproductions ?_

`systématique` / `intermittente - taux observé : <N sur M tentatives>`

## Impact métier

_Quel est l'impact pour l'utilisateur ou le produit ? Qui est affecté ? Quel flux est bloqué ?_

`<description de l'impact>`

## Logs utiles

_Colle ici les extraits de log pertinents (console navigateur, logs Docker, réponse HTTP). Masque toute valeur sensible par `***MASQUÉ***`._

```
<extrait de log>
```

## Capture

_Chemin relatif vers le PNG annoté déposé dans `validation/reports/artifacts/`. Un seul PNG par bug si possible._

`validation/reports/artifacts/BUG-<NNN>-<AAAA-MM-JJ>.png`

## Trace E2E

_Si le bug a été détecté par une spec Playwright, indique le chemin du rapport HTML. Ne jamais copier le fichier `.zip` de trace dans `validation/reports/artifacts/`._

Rapport Playwright : `frontend/playwright-report/validation/index.html`
Trace (reste dans `frontend/test-results/`, non versionné) : `<chemin local - ne pas copier dans artifacts/>`

## Requêtes réseau

_Copie ici les requêtes HTTP en erreur (méthode, URL, statut, corps de réponse tronqué). Masque les tokens et clés._

```
<méthode> <URL> -> HTTP <statut>
Réponse : <corps tronqué, valeurs sensibles masquées>
```

## Hypothèse technique

_Quelle est la cause probable ? Quel fichier, quelle fonction, quel edge case est suspecté ?_

`<hypothèse>`

## Workaround éventuel

_Existe-t-il un contournement temporaire permettant à l'utilisateur de continuer à travailler ?_

`<workaround>` / `Aucun`

## Recommandation

_Quelle action corrective est proposée ? Quel est le niveau d'urgence ?_

`<recommandation>`

---

## Reproduction confirmée

_Tout échec doit être reproduit au moins une seconde fois avant d'être déclaré bug._

| Tentative | Date | Résultat | Note |
|---|---|---|---|
| Tentative 1 | `<AAAA-MM-JJ>` | `Reproduit` / `Non reproduit` | `<note>` |
| Tentative 2 | `<AAAA-MM-JJ>` | `Reproduit` / `Non reproduit` | `<note>` |

---

## Sécurité du rapport

> **Ne jamais inclure dans ce rapport :** clé API, token d'accès, JWT, mot de passe de production, URL signée Supabase Storage.
>
> **Masquer systématiquement** toute valeur sensible par `***MASQUÉ***`, y compris dans les extraits de log et les corps de requête.
>
> **Ne pas joindre** dans `validation/reports/artifacts/` : trace Playwright (`.zip`), fichier `storageState`, fichier `.har`. Ce répertoire n'est PAS dans `.gitignore` : tout fichier qui y est poussé est versionné et potentiellement public.
