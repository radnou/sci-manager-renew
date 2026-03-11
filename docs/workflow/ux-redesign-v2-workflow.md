# GererSCI — Workflow d'Implementation UX Redesign V2

> Date: 2026-03-10
> Sources: `docs/specs/ux-redesign-v2.md`, `docs/architecture/ux-redesign-v2-architecture.md`
> Stack: SvelteKit 2.x + FastAPI 0.x + Supabase (PostgreSQL) + Stripe
> Branch: `feature/ux-redesign-v2`

---

## Vue d'ensemble

8 sprints, chaque sprint produit un incrément fonctionnel deployable.

```
S1 ─── Foundation (DB + Paywall + Routes)
 │
S2 ─── Dashboard + Sidebar V2
 │
S3 ─── Fiche Bien Core (identite + loyers)
 │
S4 ─── Bail + Locataires + Colocation
 │
S5 ─── Charges + PNO + Frais Agence + Permissions
 │
S6 ─── Notifications email + Preferences
 │
S7 ─── Documents + Finances + Rentabilite
 │
S8 ─── Cleanup + Tests E2E + Deploy
```

### Conventions

- **Checkpoint**: point de validation avant de passer au sprint suivant
- **Dependencies**: prerequis techniques du sprint
- **Files**: fichiers a creer ou modifier (exhaustif)
- **Tests**: tests unitaires et/ou d'integration attendus

---

## Sprint 1 — Foundation: DB + Paywall + Onboarding + Route Structure

> **Priority**: P0 | **Dependencies**: none | **User Stories**: US-P0.1, US-P0.2, US-P0.3

### Phase 1.1 — Database Migration 008

**Objectif**: Creer toutes les nouvelles tables et colonnes.

#### Taches

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 1.1.1 | Creer migration 008 | `supabase/migrations/008_ux_redesign_v2.sql` | Tables: baux, bail_locataires, assurances_pno, frais_agence, notification_preferences, documents_bien. Colonnes: biens (surface_m2, nb_pieces, dpe_classe, photo_url, prix_acquisition), locataires (telephone), subscriptions (onboarding_completed) |
| 1.1.2 | Ajouter RLS policies | Dans migration 008 | SELECT pour tous associes, INSERT/UPDATE/DELETE pour gerants uniquement. Pattern: biens.id_sci -> associes.user_id. notification_preferences: owner-only |
| 1.1.3 | Ajouter triggers updated_at | Dans migration 008 | baux, assurances_pno, frais_agence |
| 1.1.4 | Ajouter indexes | Dans migration 008 | idx_baux_id_bien, idx_baux_statut, idx_assurances_pno_id_bien, idx_frais_agence_id_bien, idx_documents_bien_id_bien, idx_notification_prefs_user |
| 1.1.5 | Data migration: locataires -> baux | Dans migration 008 | INSERT INTO baux FROM locataires JOIN biens, puis bail_locataires. Condition: seulement si locataires existent |
| 1.1.6 | Existing users onboarding bypass | Dans migration 008 | `UPDATE subscriptions SET onboarding_completed = true WHERE is_active = true` |

**Tests**:
- [ ] Migration s'applique sans erreur sur staging
- [ ] Tables creees avec contraintes CHECK
- [ ] RLS policies fonctionnelles (test SELECT/INSERT avec differents users)
- [ ] Data migration: baux crees pour chaque locataire existant

### Phase 1.2 — Backend Paywall Middleware

**Objectif**: Bloquer l'acces API sans abonnement actif.

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 1.2.1 | Creer dependency paywall | `backend/app/core/paywall.py` | `require_active_subscription()`: verifie subscriptions.is_active, raise HTTP 402 si non. Retourne SubscriptionInfo (plan_key, is_active, onboarding_completed) |
| 1.2.2 | Creer dependency membership | `backend/app/core/paywall.py` | `require_sci_membership(sci_id)`: verifie associes membership, retourne role. `require_gerant_role()`: chaine membership + check role='gerant' |
| 1.2.3 | Schema SubscriptionInfo | `backend/app/schemas/subscription.py` | Ajouter `onboarding_completed: bool` au schema existant |
| 1.2.4 | Enrichir GET /stripe/subscription | `backend/app/api/v1/stripe.py` | Retourner `onboarding_completed` dans la reponse |
| 1.2.5 | Creer router onboarding | `backend/app/api/v1/onboarding.py` | GET /onboarding (status), POST /onboarding (complete step). Logic: track steps in subscriptions metadata ou via queries (sci exists? bien exists? bail exists? prefs set?) |
| 1.2.6 | Enregistrer router | `backend/app/main.py` | `app.include_router(onboarding.router, prefix="/api/v1")` |

**Tests**:
- [ ] 402 retourne si pas d'abonnement
- [ ] 200 avec abonnement actif
- [ ] Onboarding status correctement calcule

### Phase 1.3 — Frontend Route Restructuring

**Objectif**: Creer le route group (app)/ avec paywall guard et structure imbriquee.

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 1.3.1 | Creer (app) route group | `frontend/src/routes/(app)/+layout.ts` | Load: auth check + fetchSubscriptionEntitlements. Redirect: /login si !auth, /pricing si !is_active, /onboarding si !onboarding_completed |
| 1.3.2 | Creer (app) layout | `frontend/src/routes/(app)/+layout.svelte` | Sidebar + main content area. setContext('user'), setContext('subscription') |
| 1.3.3 | Deplacer dashboard | `frontend/src/routes/(app)/dashboard/+page.svelte` | Copier l'existant, adapter les imports |
| 1.3.4 | Creer skeleton routes SCI | `frontend/src/routes/(app)/scis/+page.svelte` | Page liste SCI (stub) |
| 1.3.5 | Creer skeleton route SCI detail | `frontend/src/routes/(app)/scis/[sciId]/+layout.ts`, `+layout.svelte`, `+page.svelte` | Layout: load SCI + membership. Page: stub |
| 1.3.6 | Creer skeleton route biens | `frontend/src/routes/(app)/scis/[sciId]/biens/+page.svelte` | Stub |
| 1.3.7 | Creer skeleton route fiche bien | `frontend/src/routes/(app)/scis/[sciId]/biens/[bienId]/+page.svelte` | Stub |
| 1.3.8 | Deplacer account/settings/admin | Sous `(app)/` | Conserver la logique existante |
| 1.3.9 | Creer page onboarding | `frontend/src/routes/(app)/onboarding/+page.svelte` | Wizard 5 etapes (composant separe) |
| 1.3.10 | Creer OnboardingWizardV2 | `frontend/src/lib/components/OnboardingWizardV2.svelte` | Stepper 5 steps: SCI, Bien, Bail, Notifications, Tour guide. Chaque step = formulaire + validation API |
| 1.3.11 | Creer SCI context store | `frontend/src/lib/stores/sci-context.ts` | writable currentSci, derived isGerant |
| 1.3.12 | Modifier root layout | `frontend/src/routes/+layout.svelte` | Retirer sidebar rendering pour les routes authentifiees (deplace dans (app)/+layout.svelte). Garder nav publique, footer, auth effect |
| 1.3.13 | Mettre a jour route-guard | `frontend/src/lib/auth/route-guard.ts` | Ajouter /onboarding aux routes protegees. Simplifier: tout (app)/ gere par son layout |

**Tests**:
- [ ] Visiteur non-auth redirige vers /login
- [ ] User sans abonnement redirige vers /pricing
- [ ] User sans onboarding redirige vers /onboarding
- [ ] User complet arrive sur /dashboard
- [ ] Routes imbriquees /scis/[id]/biens resolvent correctement

### Checkpoint S1

- [ ] Migration 008 deployee sur staging
- [ ] Paywall fonctionnel (402 sans abo, 200 avec)
- [ ] Onboarding wizard fonctionnel (5 steps)
- [ ] Nouvelle structure de routes accessible
- [ ] Anciennes routes encore fonctionnelles (pas de regression)
- [ ] `pnpm run check` passe sans erreur

---

## Sprint 2 — Dashboard 4 Blocs + Sidebar V2

> **Priority**: P0 | **Dependencies**: S1 | **User Stories**: US-P0.4

### Phase 2.1 — Backend Dashboard Endpoint

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 2.1.1 | Creer router dashboard | `backend/app/api/v1/dashboard.py` | GET /api/v1/dashboard: retourne {alertes, kpis, scis, activite} |
| 2.1.2 | Service alertes | `backend/app/services/dashboard_service.py` | get_alertes(user_id): loyers en retard (>5j), baux expirant (<90j), quittances non generees |
| 2.1.3 | Service KPIs | Dans dashboard_service.py | get_portfolio_kpis(user_id): sci_count, biens_count, taux_recouvrement, cashflow_net |
| 2.1.4 | Service SCI cards | Dans dashboard_service.py | get_sci_cards(user_id): list[{nom, statut, biens_count, loyer_total, recouvrement}] |
| 2.1.5 | Service activite | Dans dashboard_service.py | get_recent_activity(user_id, limit=10): derniers loyers, quittances, biens ajoutes |
| 2.1.6 | Enregistrer router | `backend/app/main.py` | include_router avec prefix /api/v1, dependencies=[Depends(require_active_subscription)] |

### Phase 2.2 — Frontend Dashboard

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 2.2.1 | Types dashboard API | `frontend/src/lib/api.ts` | Ajouter types: DashboardAlerte, DashboardKpis, SCICard, ActivityItem, DashboardData. Ajouter fetchDashboard() |
| 2.2.2 | Composant DashboardAlerts | `frontend/src/lib/components/dashboard/DashboardAlerts.svelte` | Cards d'alerte: loyers retard (rouge), baux expirant (jaune), quittances (bleu). Message positif si vide |
| 2.2.3 | Composant DashboardKpis | `frontend/src/lib/components/dashboard/DashboardKpis.svelte` | 4 KPI cards en ligne: SCI actives, Biens, Recouvrement %, Cashflow net |
| 2.2.4 | Composant DashboardSciCards | `frontend/src/lib/components/dashboard/DashboardSciCards.svelte` | Grille cards SCI cliquables: nom, badge statut, biens_count, loyer_total, mini progress bar recouvrement. Lien → /scis/:sciId |
| 2.2.5 | Composant DashboardActivity | `frontend/src/lib/components/dashboard/DashboardActivity.svelte` | Timeline 10 items max: icone par type, texte, temps relatif |
| 2.2.6 | Page dashboard V2 | `frontend/src/routes/(app)/dashboard/+page.svelte` | Layout: Alerts (full width) → KPIs (row) → SCI Cards (grid) → Activity (timeline). fetchDashboard() on mount |

### Phase 2.3 — Sidebar V2

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 2.3.1 | Creer AppSidebarV2 | `frontend/src/lib/components/AppSidebarV2.svelte` | Nav dynamique: Dashboard, Mes SCI (expandable tree), Finances, Parametres, Compte. SCI sub-nav: Vue d'ensemble, Biens, Associes, Fiscalite, Documents. Responsive: drawer mobile, fixed desktop |
| 2.3.2 | Integrer dans (app) layout | `frontend/src/routes/(app)/+layout.svelte` | Remplacer AppSidebar par AppSidebarV2 |
| 2.3.3 | Creer SCI switcher dans sidebar | Integre dans AppSidebarV2 | Liste les SCI de l'user, expand/collapse sub-nav, highlight active SCI basee sur URL |
| 2.3.4 | Adapter breadcrumbs | `frontend/src/lib/components/AppBreadcrumbs.svelte` | Parser /scis/:sciId/biens/:bienId pour generer le fil d'ariane avec noms resolus |

**Tests**:
- [ ] Dashboard charge et affiche 4 blocs
- [ ] Alertes vides → message "Tout est en ordre"
- [ ] KPIs calcules correctement
- [ ] SCI cards cliquables, lien correct
- [ ] Sidebar V2 responsive (mobile drawer)
- [ ] Sidebar expand/collapse SCI sub-nav

### Checkpoint S2

- [ ] Dashboard fonctionnel avec donnees reelles
- [ ] Sidebar V2 operationnelle
- [ ] Navigation SCI → sous-pages fonctionne
- [ ] `pnpm run check` passe

---

## Sprint 3 — Fiche Bien Core (Sections A + C)

> **Priority**: P0 | **Dependencies**: S1, S2 | **User Stories**: US-P0.5

### Phase 3.1 — Backend API Nested Biens

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 3.1.1 | Creer router nested scis/biens | `backend/app/api/v1/scis_biens.py` | GET /scis/{sci_id}/biens (list), POST (create), GET /scis/{sci_id}/biens/{bien_id} (fiche complete), PATCH, DELETE. Dependencies: require_sci_membership (GET), require_gerant_role (POST/PATCH/DELETE) |
| 3.1.2 | Endpoint fiche bien agrege | Dans scis_biens.py | GET /scis/{sci_id}/biens/{bien_id}: retourne FicheBienResponse (bien + bail_actif + loyers_recents + charges + assurance_pno + frais_agence + documents + rentabilite) |
| 3.1.3 | Schemas fiche bien | `backend/app/schemas/fiche_bien.py` | FicheBienResponse, RentabiliteCalculee (brute, nette, cashflow_mensuel, cashflow_annuel) |
| 3.1.4 | Enrichir BienCreate/BienUpdate schemas | `backend/app/schemas/biens.py` | Ajouter: surface_m2, nb_pieces, dpe_classe, photo_url, prix_acquisition |
| 3.1.5 | Service rentabilite | `backend/app/services/rentabilite_service.py` | calculate_rentabilite(bien, loyers, charges, pno, agence): formules de l'architecture |
| 3.1.6 | Nested loyers endpoints | `backend/app/api/v1/scis_biens.py` | GET /scis/{sci_id}/biens/{bien_id}/loyers (filtered par date range), POST, PATCH /{loyer_id}, DELETE /{loyer_id} |

### Phase 3.2 — Frontend Fiche Bien

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 3.2.1 | Types API fiche bien | `frontend/src/lib/api.ts` | Ajouter: FicheBien, Bail, AssurancePno, FraisAgence, DocumentBien. Fonctions: fetchFicheBien, fetchSciBiens |
| 3.2.2 | Page fiche bien | `frontend/src/routes/(app)/scis/[sciId]/biens/[bienId]/+page.svelte` | Load fiche bien, render sections A + C. Layout: header fixe + sections scrollables |
| 3.2.3 | Composant FicheBienHeader | `frontend/src/lib/components/fiche-bien/FicheBienHeader.svelte` | Breadcrumb, titre adresse, badges (type, DPE, statut bail), actions (modifier, supprimer, generer quittance) |
| 3.2.4 | Composant FicheBienIdentite | `frontend/src/lib/components/fiche-bien/FicheBienIdentite.svelte` | Section A: affichage/edition des champs bien. Photo preview si presente. Mode lecture/edition toggle |
| 3.2.5 | Composant FicheBienLoyers | `frontend/src/lib/components/fiche-bien/FicheBienLoyers.svelte` | Section C: tableau loyers avec statut, actions inline (marquer paye, generer quittance), filtre date, pagination. Bouton "Enregistrer un loyer" |
| 3.2.6 | Page liste biens SCI | `frontend/src/routes/(app)/scis/[sciId]/biens/+page.svelte` | Grille/liste des biens: card avec adresse, ville, type, loyer. Lien → fiche bien |
| 3.2.7 | Page vue d'ensemble SCI | `frontend/src/routes/(app)/scis/[sciId]/+page.svelte` | Resume SCI: nom, SIREN, regime fiscal, stats (biens count, loyers, recouvrement). Liens vers sous-pages |

**Tests**:
- [ ] API /scis/{id}/biens retourne la liste filtree
- [ ] API /scis/{id}/biens/{id} retourne fiche complete agregee
- [ ] Fiche bien sections A + C s'affichent correctement
- [ ] Loyers filtrables par date
- [ ] Actions loyer fonctionnelles (marquer paye, generer quittance)
- [ ] Non-membre d'une SCI → 404
- [ ] `pnpm run check` passe

### Checkpoint S3

- [ ] Navigation complete: Dashboard → SCI → Biens → Fiche Bien
- [ ] Fiche bien sections A + C operationnelles
- [ ] API nested fonctionnelle
- [ ] Breadcrumbs resolvent les noms

---

## Sprint 4 — Bail + Locataires + Colocation

> **Priority**: P1 | **Dependencies**: S3 | **User Stories**: US-P1.1, US-P1.3

### Phase 4.1 — Backend CRUD Baux

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 4.1.1 | Schemas baux | `backend/app/schemas/baux.py` | BailCreate (avec locataire_ids pour colocation), BailUpdate, BailResponse (avec locataires embeds) |
| 4.1.2 | Endpoints baux | `backend/app/api/v1/scis_biens.py` | GET /scis/{sci_id}/biens/{bien_id}/baux (historique), POST (creer bail + attacher locataires), PATCH /{bail_id}, DELETE /{bail_id} |
| 4.1.3 | Attach/detach locataires | Dans scis_biens.py | POST /scis/{sci_id}/biens/{bien_id}/baux/{bail_id}/locataires (attach), DELETE /{locataire_id} (detach) |
| 4.1.4 | Logic: un seul bail en_cours | Dans service | Validation: max 1 bail avec statut='en_cours' par bien. Passer les anciens en 'expire' automatiquement |

### Phase 4.2 — Frontend Section B

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 4.2.1 | Composant FicheBienBail | `frontend/src/lib/components/fiche-bien/FicheBienBail.svelte` | Card bail actif: locataire(s), dates, loyer HC, charges, depot, IRL, statut. Mode creation/edition. Support colocation (multi-locataires) |
| 4.2.2 | Page historique baux | `frontend/src/routes/(app)/scis/[sciId]/biens/[bienId]/baux/+page.svelte` | Liste des baux passes avec locataires, dates, montants. Timeline verticale |
| 4.2.3 | Dialog creation bail | Composant dans fiche-bien/ | Formulaire multi-step: infos bail → selection locataires (existants ou creation) → confirmation |
| 4.2.4 | API client baux | `frontend/src/lib/api.ts` | fetchBienBaux, createBail, updateBail, attachLocataireToBail |

**Tests**:
- [ ] CRUD bail fonctionnel via API
- [ ] Colocation: bail avec 2+ locataires
- [ ] Un seul bail en_cours par bien
- [ ] Historique baux affiche correctement
- [ ] Transition bail en_cours → expire

### Checkpoint S4

- [ ] Section B fiche bien operationnelle
- [ ] Colocation fonctionnelle
- [ ] Historique baux accessible
- [ ] Data migration locataires→baux validee

---

## Sprint 5 — Charges + PNO + Frais Agence + Permissions

> **Priority**: P1 | **Dependencies**: S3 | **User Stories**: US-P1.2, US-P1.4

### Phase 5.1 — Backend Charges Enrichies

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 5.1.1 | Endpoints charges nested | `backend/app/api/v1/scis_biens.py` | GET/POST/PATCH/DELETE /scis/{sci_id}/biens/{bien_id}/charges |
| 5.1.2 | Endpoints assurance PNO | `backend/app/api/v1/scis_biens.py` | GET/POST/PATCH/DELETE /scis/{sci_id}/biens/{bien_id}/assurance-pno |
| 5.1.3 | Endpoints frais agence | `backend/app/api/v1/scis_biens.py` | GET/POST/PATCH/DELETE /scis/{sci_id}/biens/{bien_id}/frais-agence |
| 5.1.4 | Schemas PNO + frais | `backend/app/schemas/assurance_pno.py`, `backend/app/schemas/frais_agence.py` | Create, Update, Response pour chaque |

### Phase 5.2 — Frontend Section D

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 5.2.1 | Composant FicheBienCharges | `frontend/src/lib/components/fiche-bien/FicheBienCharges.svelte` | 3 sous-sections: D1 (charges existantes), D2 (assurance PNO card), D3 (frais agence card). CRUD inline pour chaque |
| 5.2.2 | API client PNO + frais | `frontend/src/lib/api.ts` | Types + fonctions CRUD pour assurances_pno et frais_agence |

### Phase 5.3 — Permissions Associes

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 5.3.1 | Appliquer require_gerant_role | Tous les POST/PATCH/DELETE dans scis_biens.py | Dependency gerant sur toutes les mutations |
| 5.3.2 | Endpoints associes nested | `backend/app/api/v1/scis_biens.py` ou nouveau fichier | GET /scis/{sci_id}/associes, POST (invite), PATCH, DELETE. POST/PATCH/DELETE → gerant only |
| 5.3.3 | Composant RoleGate | `frontend/src/lib/components/RoleGate.svelte` | Wrapper conditionnel: affiche children si gerant, fallback sinon. Utilise getContext('userRole') |
| 5.3.4 | Integrer RoleGate | Dans toutes les pages SCI | Masquer boutons d'action pour les associes (lecture seule) |
| 5.3.5 | Page associes SCI | `frontend/src/routes/(app)/scis/[sciId]/associes/+page.svelte` | Liste associes avec role badge. Bouton inviter (gerant only) |

**Tests**:
- [ ] Charges CRUD nested fonctionnel
- [ ] PNO et frais agence CRUD
- [ ] Associe ne peut pas POST/PATCH/DELETE (403)
- [ ] RoleGate masque les actions cote frontend
- [ ] Page associes affiche roles correctement

### Checkpoint S5

- [ ] Section D fiche bien complete (charges + PNO + frais)
- [ ] Permissions gerant/associe appliquees backend + frontend
- [ ] Page associes fonctionnelle

---

## Sprint 6 — Notifications Email + Preferences

> **Priority**: P1 | **Dependencies**: S1 | **User Stories**: US-P1.5

### Phase 6.1 — Backend Notifications

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 6.1.1 | Endpoints preferences | `backend/app/api/v1/notification_preferences.py` | GET /user/notification-preferences, PUT /user/notification-preferences (bulk update) |
| 6.1.2 | Schema preferences | `backend/app/schemas/notification_preferences.py` | NotificationPreference (type, email_enabled, in_app_enabled), NotificationPreferencesUpdate (list of prefs) |
| 6.1.3 | Service notifications enrichi | `backend/app/services/notification_service.py` | create_notification_with_email(user_id, type, data): check preferences → create in-app + send email via Resend si enabled |
| 6.1.4 | Cron-like triggers | `backend/app/services/notification_cron.py` | Fonctions: check_late_payments(), check_expiring_bails(), check_pending_quittances(), check_expiring_pno(). Appelees via endpoint admin ou scheduled task |
| 6.1.5 | Endpoint trigger cron | `backend/app/api/v1/admin.py` | POST /admin/trigger-notifications (admin only) — ou integrer dans un scheduler |

### Phase 6.2 — Frontend Preferences

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 6.2.1 | Page settings V2 | `frontend/src/routes/(app)/settings/+page.svelte` | Section notifications: toggles par type (late_payment, bail_expiring, quittance_pending, pno_expiring, new_loyer, new_associe, subscription_expiring). Toggle email ON/OFF + in-app ON/OFF |
| 6.2.2 | API client preferences | `frontend/src/lib/api.ts` | fetchNotificationPreferences, updateNotificationPreferences |
| 6.2.3 | Onboarding step 4 integration | `frontend/src/lib/components/OnboardingWizardV2.svelte` | Step 4: toggle global email. Popule les preferences par defaut |

**Tests**:
- [ ] Preferences CRUD fonctionnel
- [ ] Email envoye quand email_enabled = true
- [ ] Email non envoye quand email_enabled = false
- [ ] Cron identifie correctement les alertes

### Checkpoint S6

- [ ] Preferences notifications configurables
- [ ] Emails envoyes selon config
- [ ] Settings page fonctionnelle
- [ ] Onboarding step 4 popule les prefs

---

## Sprint 7 — Documents + Finances + Rentabilite

> **Priority**: P2 | **Dependencies**: S3, S5 | **User Stories**: US-P2.1, US-P2.2, US-P2.3

### Phase 7.1 — Backend Documents + Finances

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 7.1.1 | Endpoints documents bien | `backend/app/api/v1/scis_biens.py` | GET /scis/{sci_id}/biens/{bien_id}/documents, POST (upload multipart), DELETE /{doc_id}. Upload vers Supabase Storage bucket |
| 7.1.2 | Schema documents | `backend/app/schemas/documents.py` | DocumentBienCreate (categorie, nom), DocumentBienResponse |
| 7.1.3 | Router finances | `backend/app/api/v1/finances.py` | GET /finances?period=12m: agregate cross-SCI (revenus, charges, cashflow, recouvrement, patrimoine, rentabilite, evolution 12m, repartition par SCI) |
| 7.1.4 | Service finances | `backend/app/services/finances_service.py` | Calculs agreges multi-SCI. Queries optimisees (pas de N+1) |

### Phase 7.2 — Frontend Documents + Finances + Rentabilite

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 7.2.1 | Composant FicheBienDocuments | `frontend/src/lib/components/fiche-bien/FicheBienDocuments.svelte` | Section F: upload multi-fichiers, grille avec miniature + nom + date + categorie. Download/delete |
| 7.2.2 | Composant FicheBienRentabilite | `frontend/src/lib/components/fiche-bien/FicheBienRentabilite.svelte` | Section E: 4 indicateurs calcules (brute, nette, cashflow mensuel/annuel). Cards lecture seule |
| 7.2.3 | Page finances | `frontend/src/routes/(app)/finances/+page.svelte` | KPI cards + bar chart (evolution 12m) + donut chart (repartition SCI) + tableau recapitulatif. Lib chart: chart.js ou lightweight alternative |
| 7.2.4 | API client finances | `frontend/src/lib/api.ts` | fetchFinances, uploadDocumentBien, deleteDocumentBien |
| 7.2.5 | Page documents SCI | `frontend/src/routes/(app)/scis/[sciId]/documents/+page.svelte` | Liste documents au niveau SCI (agrege de tous les biens) |
| 7.2.6 | Page fiscalite SCI | `frontend/src/routes/(app)/scis/[sciId]/fiscalite/+page.svelte` | Adapter l'existant dans le nouveau routage |

**Tests**:
- [ ] Upload document vers Supabase Storage
- [ ] Finances agreges correctement
- [ ] Rentabilite calculee selon formules spec
- [ ] Charts rendus correctement

### Checkpoint S7

- [ ] Documents uploadables/telechargeable par bien
- [ ] Vue finances transversale avec charts
- [ ] Rentabilite calculee sur fiche bien
- [ ] Pages fiscalite et documents SCI

---

## Sprint 8 — Cleanup + Tests E2E + Deploy

> **Priority**: Finalization | **Dependencies**: S1-S7

### Phase 8.1 — Cleanup Anciennes Routes

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 8.1.1 | Supprimer routes plates | `frontend/src/routes/biens/`, `locataires/`, `loyers/`, `charges/`, `associes/`, `fiscalite/`, `exploitation/`, `finance/`, `documents/` | Supprimer completement ces dossiers |
| 8.1.2 | Redirect /register → /pricing | `frontend/src/routes/register/+page.svelte` | Redirect automatique |
| 8.1.3 | Nettoyer route-guard.ts | `frontend/src/lib/auth/route-guard.ts` | Retirer les anciennes routes de la liste protegee |
| 8.1.4 | Nettoyer root layout | `frontend/src/routes/+layout.svelte` | Retirer references aux anciennes routes dans nav mobile et footer |
| 8.1.5 | Supprimer AppSidebar.svelte | `frontend/src/lib/components/AppSidebar.svelte` | Remplace par AppSidebarV2 |
| 8.1.6 | Supprimer OnboardingWizard.svelte | `frontend/src/lib/components/OnboardingWizard.svelte` | Remplace par OnboardingWizardV2 |
| 8.1.7 | Deprecate flat API endpoints | `backend/app/api/v1/*.py` | Ajouter @deprecated warning header aux anciens endpoints plats. Garder fonctionnels pour retrocompat temporaire |

### Phase 8.2 — Tests E2E

| # | Tache | Fichier | Details |
|---|-------|---------|---------|
| 8.2.1 | Test flow inscription | `frontend/tests/e2e/onboarding.spec.ts` | Visiteur → /pricing → checkout → callback → onboarding wizard → dashboard |
| 8.2.2 | Test paywall | `frontend/tests/e2e/paywall.spec.ts` | User sans abo → redirect /pricing. User avec abo → acces app |
| 8.2.3 | Test navigation SCI | `frontend/tests/e2e/sci-navigation.spec.ts` | Dashboard → SCI → Biens → Fiche Bien → retour |
| 8.2.4 | Test fiche bien | `frontend/tests/e2e/fiche-bien.spec.ts` | Voir identite, enregistrer loyer, voir charges |
| 8.2.5 | Test permissions | `frontend/tests/e2e/permissions.spec.ts` | Gerant voit actions, associe ne voit pas |
| 8.2.6 | Tests backend integration | `backend/tests/test_nested_api.py` | Test CRUD nested endpoints, test paywall 402, test gerant-only 403 |

### Phase 8.3 — Deploy

| # | Tache | Details |
|---|-------|---------|
| 8.3.1 | Deploy migration 008 sur staging | Via SSH, appliquer SQL sur Supabase staging |
| 8.3.2 | Deploy backend staging | Docker build + restart backend container |
| 8.3.3 | Deploy frontend staging | Docker build avec VITE_ vars, restart frontend |
| 8.3.4 | Smoke test staging | Verifier flow complet manuellement |
| 8.3.5 | Deploy production | Meme process que staging. Backup DB avant migration |
| 8.3.6 | Verif post-deploy | Test flow complet sur production |

### Checkpoint S8

- [ ] Anciennes routes supprimees, pas de 404
- [ ] Tests E2E passent
- [ ] `pnpm run check` passe
- [ ] `pnpm run lint` passe
- [ ] `pytest` passe
- [ ] Staging valide
- [ ] Production deployee

---

## Matrice de dependances inter-sprints

```
S1 ──┬──→ S2 ──→ S3 ──┬──→ S4
     │                 │
     │                 └──→ S5
     │
     └──→ S6
                  S3 + S5 ──→ S7
                               │
     S1-S7 ───────────────────→ S8
```

- S1 est prerequis pour tout
- S2 et S6 peuvent etre parallelises (independants)
- S3 depend de S2 (sidebar V2 pour navigation)
- S4 et S5 dependent de S3 (fiche bien core)
- S4 et S5 peuvent etre parallelises
- S7 depend de S3 (fiche bien) et S5 (charges pour rentabilite)
- S8 attend tout

### Parallelisation possible

```
Thread A: S1 → S2 → S3 → S4 → S7 → S8
Thread B: S1 → S6
Thread C: S3 → S5
```

---

## Fichiers crees/modifies — Resume exhaustif

### Nouveaux fichiers

| Fichier | Sprint |
|---------|--------|
| `supabase/migrations/008_ux_redesign_v2.sql` | S1 |
| `backend/app/core/paywall.py` | S1 |
| `backend/app/api/v1/onboarding.py` | S1 |
| `backend/app/api/v1/dashboard.py` | S2 |
| `backend/app/services/dashboard_service.py` | S2 |
| `backend/app/api/v1/scis_biens.py` | S3 |
| `backend/app/schemas/fiche_bien.py` | S3 |
| `backend/app/services/rentabilite_service.py` | S3 |
| `backend/app/schemas/baux.py` | S4 |
| `backend/app/schemas/assurance_pno.py` | S5 |
| `backend/app/schemas/frais_agence.py` | S5 |
| `backend/app/api/v1/notification_preferences.py` | S6 |
| `backend/app/schemas/notification_preferences.py` | S6 |
| `backend/app/services/notification_cron.py` | S6 |
| `backend/app/api/v1/finances.py` | S7 |
| `backend/app/services/finances_service.py` | S7 |
| `backend/app/schemas/documents.py` | S7 |
| `frontend/src/routes/(app)/+layout.ts` | S1 |
| `frontend/src/routes/(app)/+layout.svelte` | S1 |
| `frontend/src/routes/(app)/onboarding/+page.svelte` | S1 |
| `frontend/src/routes/(app)/dashboard/+page.svelte` | S1/S2 |
| `frontend/src/routes/(app)/scis/+page.svelte` | S1 |
| `frontend/src/routes/(app)/scis/[sciId]/+layout.ts` | S1 |
| `frontend/src/routes/(app)/scis/[sciId]/+layout.svelte` | S1 |
| `frontend/src/routes/(app)/scis/[sciId]/+page.svelte` | S3 |
| `frontend/src/routes/(app)/scis/[sciId]/biens/+page.svelte` | S3 |
| `frontend/src/routes/(app)/scis/[sciId]/biens/[bienId]/+page.svelte` | S3 |
| `frontend/src/routes/(app)/scis/[sciId]/biens/[bienId]/baux/+page.svelte` | S4 |
| `frontend/src/routes/(app)/scis/[sciId]/associes/+page.svelte` | S5 |
| `frontend/src/routes/(app)/scis/[sciId]/fiscalite/+page.svelte` | S7 |
| `frontend/src/routes/(app)/scis/[sciId]/documents/+page.svelte` | S7 |
| `frontend/src/routes/(app)/finances/+page.svelte` | S7 |
| `frontend/src/routes/(app)/settings/+page.svelte` | S6 |
| `frontend/src/routes/(app)/account/+page.svelte` | S1 |
| `frontend/src/routes/(app)/account/privacy/+page.svelte` | S1 |
| `frontend/src/routes/(app)/admin/+layout.svelte` | S1 |
| `frontend/src/routes/(app)/admin/+page.svelte` | S1 |
| `frontend/src/routes/(app)/admin/users/+page.svelte` | S1 |
| `frontend/src/lib/stores/sci-context.ts` | S1 |
| `frontend/src/lib/components/OnboardingWizardV2.svelte` | S1 |
| `frontend/src/lib/components/AppSidebarV2.svelte` | S2 |
| `frontend/src/lib/components/RoleGate.svelte` | S5 |
| `frontend/src/lib/components/dashboard/DashboardAlerts.svelte` | S2 |
| `frontend/src/lib/components/dashboard/DashboardKpis.svelte` | S2 |
| `frontend/src/lib/components/dashboard/DashboardSciCards.svelte` | S2 |
| `frontend/src/lib/components/dashboard/DashboardActivity.svelte` | S2 |
| `frontend/src/lib/components/fiche-bien/FicheBienHeader.svelte` | S3 |
| `frontend/src/lib/components/fiche-bien/FicheBienIdentite.svelte` | S3 |
| `frontend/src/lib/components/fiche-bien/FicheBienLoyers.svelte` | S3 |
| `frontend/src/lib/components/fiche-bien/FicheBienBail.svelte` | S4 |
| `frontend/src/lib/components/fiche-bien/FicheBienCharges.svelte` | S5 |
| `frontend/src/lib/components/fiche-bien/FicheBienRentabilite.svelte` | S7 |
| `frontend/src/lib/components/fiche-bien/FicheBienDocuments.svelte` | S7 |

### Fichiers modifies

| Fichier | Sprint | Changement |
|---------|--------|------------|
| `backend/app/main.py` | S1, S2, S3, S6, S7 | Enregistrement nouveaux routers |
| `backend/app/api/v1/__init__.py` | S1+ | Export nouveaux modules |
| `backend/app/api/v1/stripe.py` | S1 | onboarding_completed dans response |
| `backend/app/schemas/biens.py` | S3 | Nouveaux champs (surface, DPE, etc.) |
| `frontend/src/lib/api.ts` | S1-S7 | Nouveaux types + fonctions |
| `frontend/src/lib/auth/route-guard.ts` | S1, S8 | Update routes, cleanup |
| `frontend/src/routes/+layout.svelte` | S1, S8 | Retirer sidebar, simplifier |
| `frontend/src/lib/components/AppBreadcrumbs.svelte` | S2 | Adapter au routage imbrique |

### Fichiers supprimes (Sprint 8)

```
frontend/src/routes/biens/
frontend/src/routes/locataires/
frontend/src/routes/loyers/
frontend/src/routes/charges/
frontend/src/routes/associes/
frontend/src/routes/fiscalite/
frontend/src/routes/exploitation/
frontend/src/routes/finance/
frontend/src/routes/documents/
frontend/src/lib/components/AppSidebar.svelte
frontend/src/lib/components/OnboardingWizard.svelte
```

---

## Commandes de validation par sprint

```bash
# Toujours valider avant de passer au sprint suivant:

# Frontend
cd frontend
pnpm run check          # TypeScript + Svelte
pnpm run lint           # ESLint
pnpm run test:unit      # Vitest

# Backend
cd backend
pytest                  # Tests
pytest --cov=app        # Couverture

# Docker (si deploiement)
docker compose build frontend backend
docker compose up -d --force-recreate frontend backend
```
