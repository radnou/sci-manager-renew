<!-- Scénario HORS-CAHIER : ne figure pas dans docs/cahier-de-recette-interactif.json. Créé pour falsifier une hypothèse d'audit. -->

| Champ | Valeur |
|---|---|
| ID | `AUTH-000` (HORS-CAHIER) |
| Domaine | `AUTH` |
| Priorité | `P0` |
| Type | `régression` |
| Automatisé | `oui - spec : frontend/e2e/production/smoke-auth.spec.ts` (via `frontend/e2e/fixtures/auth.fixture.ts`, mode 2) |
| Niveau de preuve | `STACK RÉELLE` |

> **Ce scénario est FALSIFIANT, pas confirmant.** Il ne cherche pas à prouver que l'authentification fonctionne : il cherche à invalider une hypothèse d'audit non vérifiée. Il doit être joué **avant tout autre scénario authentifié**. Tant qu'il n'a pas tourné, aucun résultat portant la mention « authentifié » dans un rapport de recette n'a de valeur probante.

---

## Hypothèse testée

`frontend/src/lib/supabase.ts:6` appelle `createClient(url, key)` sans option `auth.storageKey`. Le client supabase-js applique donc sa clé de session par défaut, supposée dérivée du **premier segment** du hostname.

Or `frontend/e2e/fixtures/auth.fixture.ts:65-66` et `frontend/e2e/production/auth.setup.ts:40-41` calculent la clé avec le **hostname complet** :

```js
const hostname = new URL(supabaseUrl).hostname;
const storageKey = `sb-${hostname}-auth-token`;
```

| `VITE_SUPABASE_URL` | Clé lue par l'application (si l'hypothèse est vraie) | Clé écrite par la fixture | Verdict attendu |
|---|---|---|---|
| `http://127.0.0.1:54321` | `sb-127-auth-token` | `sb-127.0.0.1-auth-token` | désalignement |
| `http://localhost:54321` | `sb-localhost-auth-token` | `sb-localhost-auth-token` | alignement |

Corroboration interne : `auth.fixture.ts:109` écrit en dur `sb-api-auth-token`, ce qui correspond exactement au premier segment de `api.gerersci.fr`. Quelqu'un a trouvé la bonne valeur empiriquement pour la production sans corriger la dérivation générale.

L'hypothèse **n'a pas pu être vérifiée à la lecture** : `frontend/node_modules` était absent au moment de l'audit. Seule l'exécution tranche.

## Préconditions

- Environnement : `local`
- Compte utilisé : `test@gerersci.fr` / `testpassword123` (créé par `supabase/seed.sql:12-13`, email pré-confirmé)
- Données requises : `supabase db reset` effectué, `pnpm install` effectué, stack démarrée via `./start-dev.sh`
- État de départ : navigateur sans session préexistante
- **`VITE_SUPABASE_URL` volontairement positionné sur l'hôte À POINTS** : `http://127.0.0.1:54321`

## Étapes

1. Vérifier que la stack locale répond : `curl -sf -o /dev/null -w '%{http_code}\n' http://localhost:5173` et `curl -sf -o /dev/null -w '%{http_code}\n' http://localhost:8001/docs`.
2. Exporter les variables avec l'hôte à points, délibérément : `export VITE_SUPABASE_URL=http://127.0.0.1:54321`, `export E2E_BASE_URL=http://localhost:5173`, `export E2E_EMAIL=test@gerersci.fr`, `export E2E_PASSWORD=testpassword123`.
3. Lancer une spec authentifiée qui consomme la fixture en mode 2 : `zsh -lc 'cd frontend && pnpm exec playwright test --config=e2e/playwright.production.config.ts e2e/production/smoke-auth.spec.ts'`.
4. Après l'injection de session par la fixture, naviguer sur `/dashboard` et observer si un élément réservé aux utilisateurs authentifiés est **effectivement rendu**.
5. Répéter les étapes 2 à 4 en remplaçant l'hôte par `http://localhost:54321`.
6. Consigner les deux résultats dans le tableau ci-dessous.

## Résultat attendu

Il n'y a pas de résultat « souhaité » : les deux issues sont informatives.

| Issue observée | Interprétation | Action à mener |
|---|---|---|
| Étape 4 **échoue** avec `127.0.0.1` et **réussit** avec `localhost` | Hypothèse **confirmée**. Le désalignement de clé de session est réel. | Conserver `VITE_SUPABASE_URL=http://localhost:54321` comme variable canonique dans `skills/local-environment/SKILL.md` et `validation/test-data/README.md`. Ouvrir un bug de type `manque de test` sur `frontend/e2e/production/auth.setup.ts`. |
| Étape 4 **réussit** avec `127.0.0.1` | Hypothèse **FAUSSE**. | Retirer la note « `localhost` et non `127.0.0.1` » de `skills/local-environment/SKILL.md` (section « Variables canoniques ») et de `validation/test-data/README.md`. Re-diagnostiquer l'origine réelle de tout échec d'authentification avant de conclure quoi que ce soit. |
| Étape 4 **échoue dans les deux cas** | La cause est ailleurs. | Ne pas conclure sur la clé de session. Vérifier d'abord que le compte existe et que la stack répond. |

**Critère d'observation, non négociable :** l'assertion porte sur un **élément du DOM réservé aux utilisateurs authentifiés**. Elle ne doit jamais se contenter de `localStorage.getItem(...)` ni de `fs.existsSync(...)`.

## Constat indépendant de l'issue

Quelle que soit l'issue ci-dessus, le constat suivant reste valide et doit être remonté :

`frontend/e2e/production/auth.setup.ts:63-66,73` n'assert que sur `localStorage.getItem(<sa propre clé>)` et sur `fs.existsSync(AUTH_FILE)`. Il ne vérifie jamais que l'application est rendue authentifiée. Il peut donc **passer au vert en produisant un `storageState` non authentifié**. Quatre specs consomment cette fixture : `smoke-auth.spec.ts`, `recette-complete.spec.ts`, `video-walkthrough.spec.ts`, `dogfooding.spec.ts`.

Type d'anomalie : `manque de test`. **CONSTATER, NE PAS CORRIGER** sans demande explicite.

## Vérifications complémentaires

- [ ] Aucune erreur dans la console navigateur (onglet Console des DevTools)
- [ ] Aucune requête HTTP en erreur inattendue (4xx ou 5xx non prévus dans le scénario)
- [ ] Clé réellement présente dans `localStorage` relevée et notée, sans jamais recopier la valeur du jeton
- [ ] Logs Docker du backend sans erreur d'authentification (`docker compose logs --tail=100 backend`)

## Preuves à capturer

- Capture PNG de l'état de `/dashboard` dans chacun des deux cas : `validation/reports/artifacts/AUTH-000-<AAAA-MM-JJ>-127.png` et `-localhost.png`
- Rapport Playwright (chemin relatif, ne pas copier) : `frontend/playwright-report/production/index.html`
- Nom de la clé `localStorage` observée, **sans sa valeur**

> **Règle de sécurité.** Ne jamais déposer dans `validation/reports/artifacts/` : trace Playwright (`.zip`), fichier `storageState`, fichier `.har`, valeur de JWT, token, clé ou URL signée. Ce répertoire n'est PAS dans `.gitignore`. La trace d'un run authentifié contient le JWT en clair, en argument de `page.evaluate` et dans les en-têtes HTTP.

## Résultat

| Date | Version / commit | Hôte testé | Statut | Preuve | Note |
|---|---|---|---|---|---|
| `<AAAA-MM-JJ>` | `<sha-court>` | `127.0.0.1` | `PASS` / `FAIL` / `BLOCKED` / `NOT_TESTED` | `<chemin PNG>` | `<clé localStorage observée>` |
| `<AAAA-MM-JJ>` | `<sha-court>` | `localhost` | `PASS` / `FAIL` / `BLOCKED` / `NOT_TESTED` | `<chemin PNG>` | `<clé localStorage observée>` |

**Conclusion sur l'hypothèse :** `<CONFIRMÉE / FALSIFIÉE / INDÉTERMINÉE>`
