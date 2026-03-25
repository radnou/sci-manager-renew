# MEGA AUDIT GO/NO-GO — GérerSCI

## MISSION

Tu es un panel d'experts réunis pour un audit de due diligence pré-lancement de **GérerSCI** (https://gerersci.fr), une application SaaS de gestion de SCI (Sociétés Civiles Immobilières) en France.

**Objectif** : Déterminer si l'application est **GO** (prête à vendre avec confiance) ou **NO-GO** (blockers à résoudre avant commercialisation).

**Standard de qualité** : Big4 (Deloitte/PwC/EY/KPMG) pour la rigueur technique + Solopreneur elite (Hormozi/Belfort) pour la conviction commerciale.

**Règle absolue** : CHAQUE finding doit être accompagné d'une PREUVE (fichier:ligne, output de commande, screenshot, URL). Zéro jugement subjectif sans evidence.

---

## PANEL D'EXPERTS

| # | Persona | Rôle | Question centrale |
|---|---------|------|-------------------|
| 1 | **CTO Big4** | Tech Due Diligence | "Est-ce que j'investirais dans cette stack ?" |
| 2 | **Alex Hormozi** | Grand Slam Offer | "Est-ce que l'offre est irrésistible ?" |
| 3 | **Jordan Belfort** | Straight Line Selling | "Est-ce que je peux closer avec conviction absolue ?" |
| 4 | **QA Lead** | Bug Hunter | "Est-ce que ça casse en production ?" |
| 5 | **CISO** | Security Auditor | "Est-ce que les données clients sont en sécurité ?" |
| 6 | **UX Lead** | User Experience | "Est-ce que l'utilisateur comprend, adopte, et revient ?" |

---

## PHASE 0 — CONTEXT LOADING

Avant tout audit, charge le contexte complet du projet :

```
1. Lire CLAUDE.md (racine du projet) — architecture, patterns, gotchas
2. Lire package.json (frontend/) — dépendances, scripts
3. Lire requirements.txt (backend/) — dépendances Python
4. Lire docker-compose.yml — infrastructure
5. Lire les migrations SQL (supabase/migrations/) — schéma DB
6. git log --oneline -30 — activité récente
7. Structure des fichiers : ls -la backend/app/ && ls -la frontend/src/routes/
```

**Output attendu** : Résumé du contexte en 10 lignes max, puis passage aux phases d'audit.

---

## PHASE 1 — AUDIT TECHNIQUE (CTO Big4)

### 1.1 Architecture & Code Quality

**Vérifications** :
```bash
# Backend
cd backend
find app/ -name "*.py" | wc -l                    # Nombre de fichiers
grep -r "TODO\|FIXME\|HACK\|XXX" app/ --include="*.py" | head -20  # Code debt markers
grep -r "import" app/api/v1/ --include="*.py" | grep -c "from app"  # Internal imports (coupling)
grep -r "async def" app/ --include="*.py" | wc -l  # Async endpoints

# Frontend
cd frontend
grep -r "// @ts-ignore\|// @ts-expect-error\|any" src/ --include="*.ts" --include="*.svelte" | wc -l  # Type safety
grep -r "console.log\|console.error\|console.warn" src/ --include="*.ts" --include="*.svelte" | head -10  # Debug leaks
pnpm run check 2>&1 | tail -5                      # TypeScript errors
pnpm run lint 2>&1 | tail -10                       # Lint errors
```

**Checklist** :
- [ ] Séparation des couches (API → Service → DB) respectée
- [ ] Pas de logique métier dans les routes API
- [ ] Schemas Pydantic pour validation input/output
- [ ] Types TypeScript stricts (pas de `any` sauvage)
- [ ] Error handling cohérent (pas de try/catch vides)
- [ ] Pas de secrets hardcodés dans le code
- [ ] Pas de `console.log` en production
- [ ] Imports circulaires absents

### 1.2 Tests & Couverture

```bash
# Backend
cd backend
PYTHONPATH=. pytest --co -q 2>&1 | tail -5          # Nombre de tests
PYTHONPATH=. pytest --cov=app --cov-report=term-missing 2>&1 | tail -30  # Couverture
PYTHONPATH=. pytest -x 2>&1 | tail -10              # Tous les tests passent ?

# Frontend
cd frontend
pnpm run test:unit 2>&1 | tail -20                   # Tests unitaires
pnpm run test:high-value 2>&1 | tail -20             # Tests high-value (≥90%)
```

**Seuils GO** :
- Backend : ≥80% couverture globale, 0 test en échec
- Frontend high-value : ≥90% couverture
- 0 test skippé sans justification

### 1.3 Performance & Scalabilité

**Vérifications** :
```bash
# Recherche N+1 queries
grep -rn "for.*await\|for.*\.execute\|for.*supabase" backend/app/ --include="*.py" | head -10

# Indexes manquants
grep -r "CREATE INDEX\|CREATE UNIQUE INDEX" supabase/migrations/ | wc -l

# Pagination
grep -r "\.limit\|\.range\|offset\|page" backend/app/api/ --include="*.py" | head -10

# Bundle size frontend
cd frontend && pnpm run build 2>&1 | grep -i "chunk\|size\|bundle" | head -10
```

**Checklist** :
- [ ] Pagination sur toutes les listes (biens, loyers, charges)
- [ ] Pas de N+1 queries dans les boucles
- [ ] Indexes sur les colonnes de filtrage (sci_id, user_id, created_at)
- [ ] Lazy loading des composants lourds (PDF, charts)
- [ ] Rate limiting configuré sur les endpoints sensibles

### 1.4 Infrastructure & DevOps

```bash
# CI/CD
cat .github/workflows/*.yml 2>/dev/null | head -50  # Pipeline

# Docker
cat docker-compose.yml | head -50
cat Dockerfile* | head -30

# Health checks
curl -s https://api.gerersci.fr/api/v1/health 2>/dev/null | head -5

# Backups
grep -r "backup\|cron\|pg_dump" . --include="*.sh" --include="*.yml" | head -10
```

**Checklist** :
- [ ] CI/CD fonctionnel (push → test → deploy)
- [ ] Health check endpoint actif
- [ ] Backup DB automatique (quotidien minimum)
- [ ] Logs structurés (pas de print sauvages)
- [ ] Monitoring/alerting configuré (Sentry ou équivalent)
- [ ] SSL/TLS en production
- [ ] Docker containers rootless ou user non-root

---

## PHASE 2 — AUDIT FONCTIONNEL (QA Lead)

### 2.1 Feature Completeness Matrix

Vérifier que CHAQUE feature listée existe ET fonctionne :

| Feature | Route/Endpoint | Backend | Frontend | Test |
|---------|---------------|---------|----------|------|
| Auth magic link | POST /api/v1/auth/magic-link | ? | /login | ? |
| Dashboard multi-SCI | GET /api/v1/dashboard | ? | /dashboard | ? |
| CRUD SCI | /api/v1/scis | ? | /scis | ? |
| CRUD Biens | /api/v1/scis/{id}/biens | ? | /scis/[id]/biens | ? |
| CRUD Baux | /api/v1/scis/{id}/biens/{id}/baux | ? | fiche-bien onglet | ? |
| Loyers + alertes | /api/v1/scis/{id}/biens/{id}/loyers | ? | fiche-bien onglet | ? |
| Charges | /api/v1/scis/{id}/biens/{id}/charges | ? | fiche-bien onglet | ? |
| Associés + invitation | /api/v1/associes | ? | /scis/[id]/associes | ? |
| Documents GED | /api/v1/scis/{id}/biens/{id}/documents | ? | fiche-bien onglet | ? |
| Quittances PDF | GET /api/v1/quitus | ? | QuitusGenerator | ? |
| CERFA 2044 | GET /api/v1/cerfa | ? | /simulateur-cerfa | ? |
| Fiscalité IR/IS | /api/v1/fiscalite | ? | /scis/[id]/fiscalite | ? |
| AG + PV | /api/v1/assemblees-generales | ? | /scis/[id]/assemblees | ? |
| Mouvements parts | /api/v1/mouvements-parts | ? | /scis/[id]/mouvements | ? |
| Export CSV | /api/v1/export | ? | bouton export | ? |
| Import CSV | /api/v1/import-csv | ? | bouton import | ? |
| Notifications | /api/v1/notifications | ? | NotificationCenter | ? |
| Onboarding wizard | /api/v1/onboarding | ? | /onboarding | ? |
| Stripe checkout | /api/v1/stripe | ? | /pricing | ? |
| Stripe portal | /api/v1/stripe/customer-portal | ? | /settings#abo | ? |
| Résiliation 3 clics | /api/v1/stripe/cancel | ? | /settings#abo | ? |
| GDPR export | /api/v1/gdpr/data-export | ? | /settings#confidentialite | ? |
| GDPR suppression | DELETE /api/v1/gdpr/account | ? | /settings#confidentialite | ? |
| Admin dashboard | /api/v1/admin | ? | /admin | ? |
| Lead capture | /api/v1/leads/capture | ? | EmailCapture | ? |
| Settings complet | — | — | /settings (5 onglets) | ? |
| SCI lifecycle | dissolution, cession, capital | ? | modals/forms | ? |

**Pour chaque "?"** : Vérifier que le code existe, que l'endpoint répond, et qu'un test couvre le cas.

### 2.2 Parcours Utilisateur Critiques

Tester mentalement (ou via Playwright) ces 5 parcours :

1. **Nouveau client** : Landing → Pricing → Checkout Stripe → Onboarding → Dashboard
2. **Usage quotidien** : Login → Dashboard → Sélectionner SCI → Fiche bien → Enregistrer loyer → Générer quittance
3. **Gestion avancée** : Créer bail → Ajouter locataire → Avenant → Congé → Clôture
4. **Associé invité** : Recevoir invitation → Login → Vue associé (lecture seule)
5. **Départ client** : Settings → Résiliation 3 clics → Export données → Suppression compte

### 2.3 Edge Cases & Error Handling

- [ ] Que se passe-t-il si le JWT expire pendant une action ?
- [ ] Que se passe-t-il si Stripe webhook arrive en double ?
- [ ] Que se passe-t-il si l'utilisateur a 0 SCI ?
- [ ] Que se passe-t-il avec des montants négatifs (loyers, charges) ?
- [ ] Que se passe-t-il si deux utilisateurs modifient le même bien ?
- [ ] Que se passe-t-il si le fichier uploadé fait 100MB ?
- [ ] Que se passe-t-il si l'email de magic link n'arrive pas ?
- [ ] Que se passe-t-il si la DB Supabase est indisponible ?

---

## PHASE 3 — AUDIT SÉCURITÉ (CISO)

### 3.1 OWASP Top 10

```bash
cd backend

# A01 - Broken Access Control
grep -rn "get_current_user\|get_admin_user\|require_plan" app/api/ --include="*.py" | wc -l
# Chaque endpoint doit avoir un guard d'authentification

# A02 - Cryptographic Failures
grep -rn "md5\|sha1\|base64.*password\|hardcoded.*key\|SECRET" app/ --include="*.py" | head -10

# A03 - Injection
grep -rn "f\".*{.*}\"|\.format(" app/ --include="*.py" | grep -i "select\|insert\|update\|delete" | head -10
# Supabase client devrait empêcher SQL injection, mais vérifier les raw queries

# A07 - XSS
grep -rn "{@html\|innerHTML\|dangerouslySetInnerHTML" frontend/src/ --include="*.svelte" | head -10

# Scan bandit
cd backend && bandit -r app -f json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Issues: {len(d.get(\"results\",[]))}, Severity: {[r[\"issue_severity\"] for r in d.get(\"results\",[])]}')"
```

### 3.2 Authentification & Autorisation

**Checklist** :
- [ ] JWT vérifié sur TOUS les endpoints protégés (pas de bypass)
- [ ] RLS activé sur TOUTES les tables (vérifier migrations)
- [ ] Admin protégé par secret key (pas accessible publiquement)
- [ ] Rate limiting sur login/magic-link (brute force protection)
- [ ] Tokens JWT avec expiration raisonnable (<1h access, <7d refresh)
- [ ] CORS configuré restrictif (pas `*`)
- [ ] Headers de sécurité (X-Frame-Options, CSP, HSTS)

### 3.3 Protection des Données

- [ ] Mots de passe hashés (vérifier Supabase Auth)
- [ ] Données sensibles chiffrées au repos
- [ ] URLs signées avec expiration pour les documents
- [ ] Pas de données personnelles dans les logs
- [ ] Pas de données sensibles dans les URLs (query params)

---

## PHASE 4 — AUDIT BUSINESS (Hormozi + Belfort)

### 4.1 Grand Slam Offer (Hormozi)

**Value Equation** : `Value = (Dream Outcome × Perceived Likelihood) / (Time Delay × Effort & Sacrifice)`

Évaluer chaque composant :

**Dream Outcome** (score /25) :
- Le prospect se dit "je ne veux plus gérer ma SCI sur Excel" ?
- La promesse "cockpit SCI professionnel" est-elle claire ?
- Le résultat rêvé est-il tangible et mesurable ?

**Perceived Likelihood** (score /25) :
- Le prospect croit-il que l'outil va réellement résoudre son problème ?
- Y a-t-il des preuves sociales (témoignages, logos, chiffres) ?
- Le onboarding inspire-t-il confiance ?
- La garantie 30 jours réduit-elle le risque perçu ?

**Time Delay** (score /25 — plus c'est bas, mieux c'est) :
- En combien de temps le prospect voit-il la valeur ?
- Le onboarding wizard crée-t-il un "aha moment" rapidement ?
- Combien de clics pour enregistrer son premier loyer ?

**Effort & Sacrifice** (score /25 — plus c'est bas, mieux c'est) :
- L'import CSV facilite-t-il la migration depuis Excel ?
- L'UX est-elle intuitive sans formation ?
- Le prix (19€/mois) est-il perçu comme un non-sacrifice vs le ROI ?

### 4.2 Straight Line System (Belfort)

**Certainty Trilogy** — chaque composant doit être ≥8/10 pour closer :

**Certitude #1 — Le Produit** (score /10) :
- "GérerSCI fait exactement ce qu'il promet ?"
- Features complètes vs promesses marketing ?
- Bugs visibles qui cassent la confiance ?

**Certitude #2 — Toi (le fondateur)** (score /10) :
- "Est-ce que tu crois à fond en ton produit ?"
- Peux-tu faire une démo live sans stress ?
- Connais-tu les objections et as-tu les réponses ?

**Certitude #3 — L'entreprise** (score /10) :
- "GérerSCI sera encore là dans 2 ans ?"
- Stack technique moderne et maintenable ?
- Infrastructure solide (pas de single point of failure) ?

### 4.3 Analyse Concurrentielle & Positionnement

```
Comparer avec :
- Ownily (comptabilité SCI, 8.25€/mois) — JTBD différent
- Rentila (gestion locative, pas SCI-spécifique)
- Excel/Google Sheets (concurrent #1 réel)
- Expert comptable (500-2000€/an)

Questions :
- Quel est le JTBD unique de GérerSCI ?
- Pourquoi pas Ownily + Excel ?
- Quel est le switching cost une fois adopté ?
- Y a-t-il un network effect possible ?
```

### 4.4 Unit Economics (projection)

```
Calculer / estimer :
- CAC (coût d'acquisition client) via SEO organique
- LTV (lifetime value) : ARPU × durée moyenne
  - Gestion : 19€/mois × 24 mois = 456€
  - Pilotage : 39€/mois × 24 mois = 936€
  - Fondateur : 349€ one-time
- LTV/CAC ratio (cible ≥3:1)
- Break-even : combien de clients payants pour couvrir les coûts fixes ?
  - VPS : ~30€/mois
  - Supabase : ~25€/mois (free tier au début)
  - Stripe fees : 1.4% + 0.25€
  - Domaine + email : ~50€/an
```

---

## PHASE 5 — AUDIT UX (UX Lead)

### 5.1 Navigation & Architecture

```
Vérifier :
- [ ] Sidebar navigation cohérente et prédictible
- [ ] Breadcrumbs fonctionnels sur toutes les pages imbriquées
- [ ] SCI switcher accessible et clair
- [ ] Retour arrière toujours possible (pas de dead-ends)
- [ ] URL bookmarkable (pas de state perdu au refresh)
```

### 5.2 Visual Consistency

```
Vérifier dans le code Svelte :
- [ ] Dark mode : TOUTES les classes ont un équivalent dark:
- [ ] Couleurs cohérentes (pas de hex hardcodés hors du design system)
- [ ] Typographie : hiérarchie claire (h1 > h2 > h3 > body)
- [ ] Spacing : utilisation cohérente du système Tailwind (pas de valeurs arbitraires)
- [ ] Composants UI réutilisés (pas de HTML dupliqué)
```

### 5.3 States (Empty / Loading / Error)

```bash
# Chercher les patterns d'états
cd frontend
grep -rn "loading\|isLoading\|Loading" src/ --include="*.svelte" | wc -l
grep -rn "error\|Error\|erreur" src/ --include="*.svelte" | wc -l
grep -rn "empty\|Aucun\|aucun\|Pas de\|pas de" src/ --include="*.svelte" | wc -l
```

- [ ] Chaque liste a un empty state informatif (pas juste vide)
- [ ] Chaque action async a un loading state (spinner ou skeleton)
- [ ] Chaque erreur a un message user-friendly (pas de stack trace)
- [ ] Les toasts de succès/erreur sont cohérents

### 5.4 Mobile & Responsive

```bash
# Vérifier les breakpoints
grep -rn "sm:\|md:\|lg:\|xl:" frontend/src/ --include="*.svelte" | wc -l
grep -rn "hidden sm:block\|block sm:hidden\|flex-col sm:flex-row" frontend/src/ --include="*.svelte" | wc -l
```

- [ ] Sidebar collapse sur mobile
- [ ] Tableaux scrollables horizontalement ou empilés
- [ ] Formulaires utilisables sur mobile (inputs assez grands)
- [ ] Pas de texte tronqué sans indicateur

---

## PHASE 6 — AUDIT LEGAL & COMPLIANCE

### 6.1 RGPD

```bash
# Vérifier les pages légales
ls frontend/src/routes/confidentialite/ 2>/dev/null
ls frontend/src/routes/cgu/ 2>/dev/null
ls frontend/src/routes/cgv/ 2>/dev/null
ls frontend/src/routes/mentions-legales/ 2>/dev/null

# Vérifier GDPR endpoints
grep -rn "gdpr\|data-export\|data-summary\|account.*DELETE" backend/app/api/ --include="*.py" | head -10

# Cookie consent
grep -rn "cookie\|consent\|CookieBanner\|cookie-consent" frontend/src/ --include="*.svelte" | head -5
```

**Checklist RGPD** :
- [ ] Politique de confidentialité complète et à jour
- [ ] Droit d'accès (data summary) — Art. 15
- [ ] Droit à la portabilité (export JSON) — Art. 20
- [ ] Droit à l'effacement (suppression compte) — Art. 17
- [ ] Consentement cookies (banner + préférences)
- [ ] Base légale du traitement identifiée (contrat, consentement)
- [ ] Sous-traitants listés (Supabase, Stripe, Resend, Matomo)
- [ ] DPO / contact RGPD accessible

### 6.2 CGU/CGV

- [ ] CGV conformes au droit français de la consommation
- [ ] Droit de rétractation / garantie 30 jours mentionné
- [ ] Article L221-28 (contenu numérique) référencé
- [ ] Clause résiliation 3 clics (loi 16 août 2022)
- [ ] Mentions obligatoires (SIRET, hébergeur, éditeur)

### 6.3 Stripe & Paiement

- [ ] PCI-DSS via Stripe (pas de données carte côté serveur)
- [ ] Webhooks vérifiés avec signature Stripe
- [ ] Factures/reçus accessibles via Stripe portal
- [ ] Remboursement possible via portal ou API

---

## PHASE 7 — SCORECARD & VERDICT

### Template de Scorecard

```
╔══════════════════════════════════════════════════════════════╗
║                 GERERSCI — AUDIT GO/NO-GO                   ║
║                     Date: [DATE]                            ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  PILIER 1 — TECHNIQUE (CTO Big4)              [__]/100      ║
║    Architecture & Code Quality                 [__]/25       ║
║    Tests & Couverture                          [__]/25       ║
║    Performance & Scalabilité                   [__]/25       ║
║    Infrastructure & DevOps                     [__]/25       ║
║                                                              ║
║  PILIER 2 — FONCTIONNEL (QA Lead)             [__]/100      ║
║    Feature Completeness                        [__]/30       ║
║    Parcours Utilisateur                        [__]/30       ║
║    Edge Cases & Error Handling                 [__]/20       ║
║    Conformité Métier (fiscal/SCI)              [__]/20       ║
║                                                              ║
║  PILIER 3 — SÉCURITÉ (CISO)                  [__]/100      ║
║    OWASP Top 10                                [__]/40       ║
║    Auth & Autorisation                         [__]/30       ║
║    Protection des Données                      [__]/30       ║
║                                                              ║
║  PILIER 4 — BUSINESS (Hormozi + Belfort)      [__]/100      ║
║    Grand Slam Offer (value equation)           [__]/40       ║
║    Straight Line (certainty trilogy)           [__]/30       ║
║    Unit Economics & Positioning                [__]/30       ║
║                                                              ║
║  PILIER 5 — UX/DESIGN (UX Lead)              [__]/100      ║
║    Navigation & Architecture                   [__]/25       ║
║    Visual Consistency                          [__]/25       ║
║    States (Empty/Loading/Error)                [__]/25       ║
║    Mobile & Responsive                         [__]/25       ║
║                                                              ║
║  PILIER 6 — LEGAL & COMPLIANCE               [__]/100      ║
║    RGPD                                        [__]/40       ║
║    CGU/CGV                                     [__]/30       ║
║    Paiement & Stripe                           [__]/30       ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  SCORE GLOBAL (moyenne pondérée)              [__]/100      ║
║                                                              ║
║  Pondération:                                                ║
║    Technique: 25% | Fonctionnel: 20% | Sécurité: 20%       ║
║    Business: 15% | UX: 10% | Legal: 10%                    ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  BLOCKERS (score <50 = veto automatique):                   ║
║  ❌ [lister les blockers]                                    ║
║                                                              ║
║  WARNINGS (score 50-70 = à corriger rapidement):            ║
║  ⚠️  [lister les warnings]                                   ║
║                                                              ║
║  STRONG POINTS:                                              ║
║  ✅ [lister les points forts]                                ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  VERDICT:  [ GO ✅ / CONDITIONAL GO ⚠️ / NO-GO ❌ ]         ║
║                                                              ║
║  CONDITIONS (si conditional):                                ║
║  1. [condition à remplir]                                    ║
║  2. [condition à remplir]                                    ║
║                                                              ║
║  CONFIDENCE LEVEL:  [__]% que le produit peut être vendu    ║
║  avec conviction et fierté                                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### Règles de Verdict

| Score Global | Blockers | Verdict |
|-------------|----------|---------|
| ≥80 | 0 | **GO** ✅ — Lance et vends avec conviction |
| 70-79 | 0 | **CONDITIONAL GO** ⚠️ — Lance mais corrige les warnings sous 2 semaines |
| 60-69 | 0 | **CONDITIONAL GO** ⚠️ — Lance en beta privée, corrige avant marketing |
| <60 | 0 | **NO-GO** ❌ — Pas prêt, fix les issues avant |
| Any | ≥1 | **NO-GO** ❌ — Un blocker = veto automatique |

### Top 5 Actions Post-Audit

À la fin de l'audit, lister les 5 actions les plus impactantes ordonnées par :
1. **Impact business** (revenu, conversion, rétention)
2. **Effort requis** (heures estimées)
3. **Priorité** (P0 = blocker, P1 = cette semaine, P2 = ce mois)

```
| # | Action | Impact | Effort | Priorité |
|---|--------|--------|--------|----------|
| 1 | [action] | [impact] | [effort] | P0/P1/P2 |
| 2 | [action] | [impact] | [effort] | P0/P1/P2 |
| 3 | [action] | [impact] | [effort] | P0/P1/P2 |
| 4 | [action] | [impact] | [effort] | P0/P1/P2 |
| 5 | [action] | [impact] | [effort] | P0/P1/P2 |
```

---

## INSTRUCTIONS D'EXÉCUTION

### Option A — Audit complet en une session
```
Copier ce prompt entier dans Claude Code et laisser tourner.
Durée estimée : 30-60 minutes.
Utiliser --yolo pour auto-approve les commandes de lecture.
```

### Option B — Audit par phases
```
Découper en 7 prompts séparés (un par phase).
Compiler les scores à la fin dans la scorecard.
```

### Option C — Audit multi-agents
```
Lancer 6 agents en parallèle (un par persona).
Chaque agent produit son rapport + score.
Un agent orchestrateur compile la scorecard finale.
```

### Consignes générales
- **EVIDENCE FIRST** : Chaque finding doit citer un fichier:ligne ou une commande
- **PAS DE COMPLAISANCE** : Si c'est cassé, dis-le. Pas de "c'est bien pour un MVP"
- **SCORING HONNÊTE** : Un 90/100 doit être mérité. La plupart des apps sont entre 60-80
- **ACTIONNABLE** : Chaque finding négatif doit avoir une recommandation de fix
- **PRIORITÉ BUSINESS** : Les issues qui impactent le revenu passent en premier

---

## ANNEXE — CONTEXTE BUSINESS

- **Target** : Gérants de SCI indépendants, cabinets comptables
- **Pricing** : Gestion 19€/mo, Pilotage 39€/mo, Fondateur 349€ lifetime
- **Modèle** : Payment-first + garantie 30 jours (anti-freemium Hormozi)
- **North Star** : Nombre de SCI actives avec ≥1 loyer enregistré sur 30 jours
- **Stack** : SvelteKit + FastAPI + Supabase + Stripe + Docker
- **Concurrent #1** : Excel (le vrai ennemi)
- **URL** : https://gerersci.fr / https://api.gerersci.fr
