<!-- Template de scénario de recette — un fichier par scénario, nommé <DOMAINE-NNN>-<slug>.md -->

| Champ | Valeur |
|---|---|
| ID | `<DOMAINE-NNN>` |
| Domaine | `PUB` / `AUTH` / `DASH` / `NAV` / `SCI` / `BIEN` / `ASSOC` / `AG` / `FISC` / `DOC` / `FIN` / `EXPL` / `SET` / `NOTIF` / `OFFLINE` / `DARK` / `PERF` |
| Priorité | `P0` / `P1` / `P2` / `P3` |
| Type | `nominal` / `erreur` / `limite` / `régression` |
| Automatisé | `oui - spec : <frontend/e2e/validation/xxxx.spec.ts>` / `non - manuel` |
| Niveau de preuve | `MOCKÉ` / `STACK RÉELLE` |

---

## Préconditions

_Décris l'état de départ attendu avant d'exécuter le scénario : environnement actif, compte utilisateur, données présentes, flags activés._

- Environnement : `<local / staging / production>`
- Compte utilisé : `<test@gerersci.fr / *@audit.test / autre>`
- Données requises : `<supabase db reset effectué / seed_billing_audit.py exécuté / autre>`
- État de départ : `<ex : aucune SCI créée / abonnement starter actif / demo_seeded=true>`

## Étapes

_Une action par ligne, formulée à l'impératif. Numérotées séquentiellement._

1. <action 1>
2. <action 2>
3. <action 3>

## Résultat attendu

_Décris ce qui doit être observable une fois les étapes exécutées : élément DOM visible, message affiché, donnée persistée, requête émise, etc. Doit être vérifiable sans ambiguïté._

<résultat attendu>

## Vérifications complémentaires

_Coche chaque point après exécution._

- [ ] Aucune erreur dans la console navigateur (onglet Console des DevTools)
- [ ] Aucune requête HTTP en erreur inattendue (4xx ou 5xx non prévus dans le scénario)
- [ ] Données persistées côté Supabase vérifiées (Studio local : `http://localhost:54323`)
- [ ] Logs Docker du service concerné sans erreur (`docker compose logs <service>`)
- [ ] Événement Stripe reçu en mode test, si applicable (webhook Stripe vers `localhost:8001/api/v1/stripe/webhook`)

## Preuves à capturer

_Spécifie ici ce qui doit être conservé comme preuve de ce scénario._

- Capture PNG annotée du résultat visible : à déposer dans `validation/reports/artifacts/<DOMAINE-NNN>-<AAAA-MM-JJ>.png`
- Rapport Playwright HTML (chemin relatif, ne pas copier dans `artifacts/`) : `frontend/playwright-report/validation/index.html`
- Extrait de log pertinent : à coller directement dans la section Résultat ci-dessous, jamais dans `validation/reports/artifacts/`

> **Règle de sécurité.** Ne jamais déposer dans `validation/reports/artifacts/` : trace Playwright (`.zip`), fichier `storageState`, fichier `.har`, valeur de JWT, token, clé ou URL signée. Ce répertoire n'est PAS dans `.gitignore` : tout fichier qui y est versé est accessible publiquement.

## Résultat

| Date | Version / commit | Statut | Preuve | Note |
|---|---|---|---|---|
| `<AAAA-MM-JJ>` | `<sha-court>` | `PASS` / `FAIL` / `BLOCKED` / `NOT_TESTED` | `<chemin PNG ou "cf. rapport Playwright">` | `<note>` |

---

> **Note sur les specs mockées.** Si ce scénario s'appuie sur une spec Playwright qui intercepte les requêtes via `page.route` (import de `../fixtures/api-mocks`), le résultat `PASS` prouve uniquement le contrat UI et **ne prouve pas** que le backend répond correctement. Le niveau de preuve doit alors être `MOCKÉ`. Pour une preuve de bout en bout, rejouer le scénario avec la stack réelle (`local` ou `staging`).
