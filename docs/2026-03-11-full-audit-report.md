# Audit Complet GererSCI — 2026-03-11

## Vue d'Ensemble

**8 dimensions auditées** en parallèle par des agents spécialisés.

| Dimension | Findings |
|-----------|----------|
| Backend Code Quality | 4 CRITICAL, 8 HIGH, 10 MEDIUM, 8 LOW |
| Frontend Code Quality | 0 CRITICAL, 17 HIGH, 12 MEDIUM, 4 LOW |
| Sécurité | 2 CRITICAL, 4 HIGH, 7 MEDIUM, 5 LOW |
| Tests & Couverture | 2 modules à 0%, 5 modules <70%, E2E 100% mocké |
| Infrastructure & DevOps | 3 CRITICAL, 6 IMPORTANT, 11 RECOMMENDED |
| Documentation | Précise mais gaps (API docs, CONTRIBUTING.md) |
| UI/UX Parcours | 7 boutons morts CRITICAL, double nav, breadcrumbs UUID |
| Fonctionnalités Métier | 8/23 COMPLETE, 14/23 PARTIAL, 1/23 BROKEN |

**Pattern dominant** : Le backend implémente les endpoints CRUD, mais **les boutons frontend ne sont pas câblés aux API calls**. Sur 23 features, seules 8 sont end-to-end complètes.

---

## SECTION 1 — BUGS CRITIQUES (Action Immédiate)

### B-1: `export.py` + `loyers.py` — `user["sub"]` crash runtime
- **Fichiers** : `backend/app/api/v1/export.py:33,84` + `backend/app/api/v1/loyers.py:270`
- **Problème** : `get_current_user` retourne un `str`, pas un `dict`. `user["sub"]` → `TypeError`
- **Impact** : Export CSV et stats loyers complètement cassés
- **Fix** : Changer en `user_id: str = Depends(get_current_user)`

### B-2: `notification_cron.py` — Mauvais nom de table
- **Fichier** : `backend/app/services/notification_cron.py:150`
- **Problème** : `table("assurance_pno")` au lieu de `table("assurances_pno")`
- **Impact** : Cron PNO expiry silencieusement vide, aucune notification envoyée

### B-3: `loyers.py` — `GererSCIException` non importé
- **Fichier** : `backend/app/api/v1/loyers.py:260`
- **Problème** : `except GererSCIException` mais ce nom n'est pas importé → `NameError` si la branche s'exécute
- **Impact** : Erreurs de suppression masquées en `DatabaseError` générique

### B-4: `CommandPalette` — Routes inexistantes
- **Fichier** : `frontend/src/lib/components/CommandPalette.svelte:23-25`
- **Problème** : Links vers `/biens`, `/loyers`, `/documents`, `/fiscalite` (routes inexistantes)
- **Impact** : 404 pour tout utilisateur de la palette de commandes

### B-5: Onboarding resume — `createdSciId` perdu
- **Fichier** : `frontend/src/routes/(app)/onboarding/+page.svelte:26`
- **Problème** : À la reprise, `createdSciId = ''` → step 2 crée un bien avec `id_sci: ''`
- **Impact** : Erreur API si l'utilisateur reprend l'onboarding

---

## SECTION 2 — SÉCURITÉ

### S-CRITICAL

| # | Finding | Fichier |
|---|---------|---------|
| S-1 | **Service role key bypass RLS** — toutes les requêtes DB utilisent `supabase_service_role_key`, rendant les policies RLS inopérantes | `core/supabase_client.py` + 12 routers |
| S-2 | **File download/delete sans ownership** — tout user authentifié peut accéder/supprimer n'importe quel fichier | `api/v1/files.py:56-79` |

### S-HIGH

| # | Finding | Fichier |
|---|---------|---------|
| S-3 | Upload sans validation (type, taille, contenu) | `scis_biens.py:1011-1063` |
| S-4 | Rate limiting absent sur la majorité des endpoints CRUD | Tous les routers sauf auth/stripe/files |
| S-5 | `python-jose` non maintenu avec CVEs connus | `requirements.txt:9` |
| S-6 | `loyer_stats` type auth incorrect (crash runtime) | `loyers.py:267-274` |

### S-MEDIUM

| # | Finding |
|---|---------|
| S-7 | SCI INSERT RLS policy `with check (true)` — tout user authentifié peut insérer |
| S-8 | IP dans audit log GDPR pour comptes supprimés |
| S-9 | GDPR deletion ne couvre pas toutes les tables (baux, locataires, notifications) |
| S-10 | Validation input manquante sur schemas (montants négatifs, strings illimitées) |
| S-11 | CORS `allow_methods=["*"]` et `allow_headers=["*"]` |
| S-12 | Error details leak en non-production |
| S-13 | Table `documents` potentiellement sans RLS |

---

## SECTION 3 — FONCTIONNALITÉS MÉTIER

### Matrice de Complétude

| Feature | Backend | Frontend | Status |
|---------|---------|----------|--------|
| SCI Management | ⚠️ Pas de PATCH/DELETE | ❌ Bouton "Nouvelle SCI" → self | ⚠️ PARTIAL |
| Bien Management | ✅ CRUD complet | ❌ "Ajouter un bien" inert | ⚠️ PARTIAL |
| Bail Management | ✅ CRUD complet | ❌ Créer/Modifier bail inerts | ⚠️ PARTIAL |
| Locataire Management | ✅ CRUD complet | ❌ Aucune UI standalone | ⚠️ PARTIAL |
| Loyer Management | ✅ CRUD complet | ❌ Enregistrer/Payé/Quittance inerts | ⚠️ PARTIAL |
| Charges Management | ✅ CRUD complet | ❌ Ajouter/Supprimer inerts | ⚠️ PARTIAL |
| Assurance PNO | ✅ CRUD complet | ❌ Ajouter/Modifier/Supprimer inerts | ⚠️ PARTIAL |
| Frais Agence | ⚠️ Pas de PATCH | ❌ Ajouter/Supprimer inerts | ⚠️ PARTIAL |
| Document Management | ✅ Upload/List/Delete | ✅ Fonctionnel (confirm/alert) | ⚠️ PARTIAL |
| Associé Management | ✅ Invite + CRUD | ❌ "Inviter" inert | ⚠️ PARTIAL |
| Fiscalité | ✅ CRUD + CERFA | ❌ Read-only, "prochainement" | ⚠️ PARTIAL |
| Dashboard | ✅ | ✅ | ✅ COMPLETE |
| Finances | ✅ | ✅ | ✅ COMPLETE |
| Rentabilité | ✅ | ✅ | ✅ COMPLETE |
| Notifications | ✅ | ✅ | ✅ COMPLETE |
| Onboarding | ✅ | ⚠️ Steps 3-4 no-ops | ⚠️ PARTIAL |
| Export CSV | ❌ CRASH runtime | ❌ Pas d'UI | ❌ BROKEN |
| Quittance PDF | ✅ | ❌ Bouton inert | ⚠️ PARTIAL |
| CERFA 2044 | ✅ | ❌ "Prochainement" | ⚠️ PARTIAL |
| Stripe Payments | ✅ | ✅ | ✅ COMPLETE |
| Admin Panel | ✅ | ✅ | ✅ COMPLETE |
| GDPR | ✅ | ✅ (raw fetch) | ✅ COMPLETE |
| Role-Based Access | ✅ | ✅ | ✅ COMPLETE |

---

## SECTION 4 — UI/UX

### Boutons Morts (CRITICAL — bloquent les flows utilisateur)

| Composant | Bouton | Fichier:Ligne |
|-----------|--------|---------------|
| FicheBienBail | "Créer un bail" | `FicheBienBail.svelte:53` |
| FicheBienBail | "Modifier" bail | `FicheBienBail.svelte:87` |
| FicheBienLoyers | "Enregistrer un loyer" | `FicheBienLoyers.svelte:43` |
| FicheBienLoyers | "Marquer comme payé" | `FicheBienLoyers.svelte:107` |
| FicheBienLoyers | "Quittance" | `FicheBienLoyers.svelte:115` |
| FicheBienCharges | "Ajouter une charge" | `FicheBienCharges.svelte:34` |
| FicheBienCharges | "Supprimer" charge | `FicheBienCharges.svelte:98` |
| FicheBienCharges | PNO "Ajouter" | `FicheBienCharges.svelte:124` |
| FicheBienCharges | PNO "Modifier" | `FicheBienCharges.svelte:169` |
| FicheBienCharges | PNO "Supprimer" | `FicheBienCharges.svelte:174` |
| FicheBienCharges | Frais "Ajouter" | `FicheBienCharges.svelte:202` |
| FicheBienCharges | Frais "Supprimer" | `FicheBienCharges.svelte:269` |
| Biens page | "Ajouter un bien" | `biens/+page.svelte:48` |
| Associés page | "Inviter un associé" | `associes/+page.svelte:61` |
| SCIs page | "Nouvelle SCI" → self | `scis/+page.svelte:28` |

### Problèmes UX Majeurs

| # | Problème | Sévérité |
|---|----------|----------|
| 1 | **Double navigation** — top bar + sidebar avec brand/logout/mobile dupliqués | HIGH |
| 2 | **Breadcrumbs** affichent des UUIDs bruts (pas les noms SCI/bien) | HIGH |
| 3 | **Onboarding** steps 3-4 sont des no-ops, pas de retour arrière | HIGH |
| 4 | **`<title>`** manquant sur 16/19 routes app | MEDIUM |
| 5 | **`alert()`/`confirm()`** natifs dans FicheBienDocuments (inconsistant avec toasts) | MEDIUM |
| 6 | **Chargement documents** séquentiel (N+1 API calls) | MEDIUM |
| 7 | **Sidebar** re-fetch SCIs à chaque navigation | MEDIUM |
| 8 | **Paraglide i18n** installé mais 0 strings utilisées | LOW |

### Accessibilité

| # | Problème | Sévérité |
|---|----------|----------|
| 1 | Zero ARIA dans tout le répertoire fiche-bien (7 composants) | HIGH |
| 2 | NotificationCenter sans focus trap | HIGH |
| 3 | Icon-only buttons sans `aria-label` (utilisent `title` seulement) | MEDIUM |
| 4 | Pas de `aria-live` pour les toasts | MEDIUM |

---

## SECTION 5 — BACKEND CODE QUALITY

### Architecture

| # | Problème | Sévérité |
|---|----------|----------|
| 1 | `_get_client()` dupliqué dans 12 routers au lieu d'utiliser `get_supabase_service_client()` | HIGH |
| 2 | Architecture `api → services → db` non respectée — majorité du CRUD inline dans routers | HIGH |
| 3 | `models/` vs `schemas/` — deux répertoires servant le même but | LOW |
| 4 | N+1 queries : `get_fiche_bien` (7 séquentielles), `list_bien_baux`, onboarding, dashboard | MEDIUM |
| 5 | `notification_cron.py` jamais schedulé (fonctions jamais appelées) | HIGH |
| 6 | `admin.py` utilise `logging` au lieu de `structlog` | HIGH |
| 7 | `security.py` : appel HTTP synchrone bloquant pour JWKS dans contexte async | HIGH |
| 8 | `cerfa.py` : feature flag absent sur la variante PDF | HIGH |
| 9 | Entitlements Pro = 10 SCI / 20 biens mais CLAUDE.md dit "illimité" | LOW |

### Dead Code

| Élément | Fichier |
|---------|---------|
| `files.py:upload_quitus` est un stub qui ne fait rien | `api/v1/files.py:22-43` |
| Services `biens_service.py`, `loyers_service.py`, `sci_service.py` quasi-vides | `services/` |
| Routes dupliquées `""` et `"/"` sur tous les routers | Multiple |

---

## SECTION 6 — FRONTEND CODE QUALITY

### Dead Code Frontend

| Élément | Impact |
|---------|--------|
| 6 composants V1 (BienTable, LoyerTable, BienForm, LoyerForm, QuitusGenerator, KPI-Card) | Storybook only |
| SidebarSCISwitcher.svelte — jamais importé | Orphelin |
| 9 composants dashboard V1 (CockpitHeader, PortfolioKPIStrip, etc.) | Non utilisés |
| Fonctions API flat (fetchBiens, fetchLoyers, etc.) — supersédées par nested | `api.ts:348-508` |
| `/register` route — juste un redirect vers `/pricing` | Stub |

### TypeScript

| # | Problème | Fichier |
|---|----------|---------|
| 1 | ~15 fonctions API retournent `Promise<any[]>` malgré types définis | `api.ts:725-824` |
| 2 | `FicheBien.loyers_recents` et `charges_list` sont `Array<any>` | `api.ts:710-711` |
| 3 | Props `Array<any>` sur FicheBienLoyers et FicheBienCharges | Composants fiche-bien |
| 4 | Layout `data: any` au lieu de `LayoutData` | `(app)/+layout.svelte` |

### Error Handling

| # | Problème |
|---|----------|
| 1 | `alert()`/`confirm()` en production dans FicheBienDocuments |
| 2 | Admin page — catch vide, page blanche si erreur |
| 3 | Privacy page — `fetch` brut au lieu de `apiFetch` (3 occurrences) |
| 4 | Pas d'`AbortController` dans les `$effect` loaders |

---

## SECTION 7 — TESTS & COUVERTURE

### Gaps Backend

| Module | Couverture | Tests Dédiés |
|--------|-----------|--------------|
| `admin.py` | ~29% | ❌ Aucun |
| `export.py` | ~30% | ❌ Aucun |
| `cerfa.py` | ~54% | ⚠️ Partiel (paywall testé, success path non) |
| `notification_cron.py` | ~50% | ⚠️ 2/4 fonctions testées |
| `onboarding.py` | ~60% | ⚠️ Partiel |

### Gaps Frontend

- **78 composants Svelte avec 0 tests unitaires**
- **16 routes app sans tests** (ni unit ni E2E)
- **E2E 100% mocké** — aucun test contre le vrai backend

### Qualité des Tests

- Assertions faibles dans `test_nested_api.py` (existence checks seulement)
- `FakeQuery` incomplet (manque `.not_`, `.lt()`, `.maybe_single()`)
- Pas de factories (data construite manuellement dans chaque test)
- Mocks E2E dupliqués dans 8+ fichiers spec

---

## SECTION 8 — INFRASTRUCTURE & DEVOPS

### CRITICAL

| # | Finding |
|---|---------|
| 1 | Pas de `.dockerignore` backend — `.env` potentiellement dans l'image |
| 2 | Pas de rollback déploiement — `git reset --hard` forward-only |
| 3 | Backup script existe mais **pas schedulé** (pas de cron) |
| 4 | Pas de rollback migrations SQL |

### IMPORTANT

| # | Finding |
|---|---------|
| 5 | CI utilise `npm` au lieu de `pnpm` (lockfile différent) |
| 6 | Containers tournent en root (pas de non-root user) |
| 7 | Pas de log shipping vers Loki (dashboards Grafana vides) |
| 8 | `bandit` et `npm audit` silencés avec `|| true` |
| 9 | Pas de notifications de déploiement |
| 10 | Pas de CDN (assets servis directement par nginx) |
| 11 | Pas de headers sécurité sur le server block API nginx |

---

## SECTION 9 — DOCUMENTATION

### Accuracy
- **CLAUDE.md** : ✅ Précis et à jour
- **MEMORY.md** : ✅ Précis

### Gaps

| Documentation | Status | Priorité |
|--------------|--------|----------|
| API Documentation (OpenAPI/Swagger) | ❌ Manquant | HIGH |
| CONTRIBUTING.md | ❌ Manquant | HIGH |
| .env.example complet | ⚠️ Partiel | MEDIUM |
| ARCHITECTURE.md V2 | ⚠️ Outdated (V1) | MEDIUM |
| Troubleshooting guide | ❌ Manquant | LOW |

### Divergence Code/Docs
- CLAUDE.md dit "Pro (illimité)" mais `entitlements.py` = `max_scis=10, max_biens=20`

---

## PLAN D'ACTIONS PRIORISÉ

### P0 — Immédiat (Bugs Critiques) — ~1 jour

1. Fix `export.py` + `loyers.py` : `user_id: str = Depends(get_current_user)`
2. Fix `notification_cron.py` : `assurance_pno` → `assurances_pno`
3. Fix `loyers.py` : importer `GererSCIException` ou remplacer par `SCIManagerException`
4. Fix `files.py` : ajouter vérification ownership sur download/delete
5. Créer `backend/.dockerignore`
6. Supprimer `tmp_env_test/`

### P1 — Sprint Courant (Sécurité + Fonctionnalités Core) — ~5-7 jours

7. Remplacer `python-jose` par `PyJWT`
8. Ajouter validation upload fichiers (taille max, whitelist extensions, magic bytes)
9. Étendre rate limiting aux endpoints CRUD
10. **Câbler les boutons fiche-bien** (loyers, charges, PNO, frais agence, bail) aux API calls
11. Ajouter fonctions API manquantes dans `api.ts` (~14 mutations nested)
12. Créer modals/formulaires pour : créer bail, enregistrer loyer, ajouter charge
13. Fix CommandPalette routes → utiliser SCI context
14. Fix onboarding : persister `createdSciId`, implémenter step 4 (notif prefs)

### P2 — Sprint Suivant (UX + Architecture) — ~5-7 jours

15. Résoudre double navigation (supprimer top bar pour users auth ou consolider)
16. Fix breadcrumbs → afficher noms SCI/bien au lieu d'UUIDs
17. Ajouter `<title>` sur les 16 routes manquantes
18. Remplacer `alert()`/`confirm()` par système toast
19. Ajouter `PATCH /scis/{id}` et `DELETE /scis/{id}` au backend
20. Remplacer `_get_client()` dupliqué par `get_supabase_service_client()`
21. Câbler boutons : "Nouvelle SCI", "Ajouter un bien", "Inviter un associé"
22. Activer quittance PDF et CERFA 2044 dans le frontend (backend prêt)

### P3 — Mois Suivant (Tests + Infra + Quality) — ~5-10 jours

23. Ajouter tests `admin.py` et `export.py` (0% → 70%+)
24. Ajouter tests `cerfa.py` success path et `notification_cron.py` fonctions manquantes
25. Ajouter accessibilité : ARIA labels, focus trap NotificationCenter, aria-live toasts
26. CI : migrer `npm` → `pnpm`, ajouter linting frontend, Docker build step
27. Configurer rollback déploiement (tag images Docker)
28. Scheduler backup cron automatique
29. Ajouter CDN (Cloudflare)
30. Ajouter GDPR deletion pour tables manquantes (baux, locataires, notifications)

### P4 — Backlog (Polish) — quand capacité

31. Typer les `any` dans api.ts et composants fiche-bien
32. Supprimer dead code (6 composants V1, 9 dashboard V1, fonctions API flat)
33. Ajouter log shipping vers Loki + alerting Grafana
34. Implémenter contract testing frontend/backend
35. Refactorer root `+layout.svelte` (559 lignes → extraire composants)
36. Paralléliser documents loading (`Promise.all` au lieu de `for...of await`)
37. Créer shared E2E mock helper
38. Documenter API (OpenAPI), créer CONTRIBUTING.md

---

## Métriques Clés

| Métrique | Valeur |
|----------|--------|
| Features COMPLETE | 8/23 (35%) |
| Features PARTIAL | 14/23 (61%) |
| Features BROKEN | 1/23 (4%) |
| Boutons UI morts | 15 |
| Fonctions API manquantes | ~24 |
| Findings sécurité CRITICAL | 2 |
| Findings sécurité HIGH | 4 |
| Backend coverage | 82% (gaps: admin 29%, export 30%) |
| Frontend component tests | 0/78 |
| E2E tests vs real backend | 0 |
