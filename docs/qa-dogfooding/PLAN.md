# QA Dogfooding — GérerSCI

## Objectif

Utiliser systématiquement GérerSCI comme un vrai gérant de SCI pour identifier les bugs, frictions UX et incohérences métier que les tests automatisés ne captent pas.

## Architecture 3 niveaux

```
Level 3 : Scénarios manuels    (30min/semaine)  — exploratoire guidé
Level 2 : Dogfooding automatisé (15min/jour)     — parcours métier complets
Level 1 : Smoke cron            (5min/heure)     — santé de base
```

---

## Level 1 — Smoke Cron (existant)

**Fichier** : `frontend/e2e/production/smoke-public.spec.ts`
**Fréquence** : Toutes les heures (ou post-deploy)
**Durée** : ~2 minutes

| Check | Status |
|-------|--------|
| Health API `/health/ready` | ✅ Existant |
| Landing, login, register, simulateur | ✅ Existant |
| Pricing + guest checkout URL | ✅ Existant |

---

## Level 2 — Dogfooding Automatisé (nouveau)

**Fichier** : `frontend/e2e/production/dogfooding.spec.ts`
**Fréquence** : Quotidien (cron ou post-deploy)
**Durée** : ~15 minutes
**Prérequis** : `E2E_EMAIL` + `E2E_PASSWORD` du compte démo

### Parcours couverts

| # | Parcours | Risque | Ce qu'on vérifie |
|---|----------|--------|------------------|
| DF-01 | Dashboard KPIs cohérents | P1 | Les chiffres sont > 0, les montants formatés, pas de NaN |
| DF-02 | CRUD Loyer complet | P0 | Créer → vérifier dans liste → supprimer |
| DF-03 | CRUD Charge complète | P1 | Créer → vérifier montant → supprimer |
| DF-04 | Quittance PDF generation | P1 | Générer → vérifier réponse PDF (Content-Type) |
| DF-05 | Navigation 10 onglets fiche bien | P1 | Chaque onglet charge sans erreur console |
| DF-06 | Bilan mensuel données cohérentes | P2 | Entrées + sorties = solde affiché |
| DF-07 | Fiscalité sans crash | P1 | Page charge, revenus fonciers affichés |
| DF-08 | Demo banner + LockedAction | P0 | Actions write verrouillées pour user demo |
| DF-09 | Dark mode visuels | P2 | Toggle dark → pas de texte invisible |
| DF-10 | Mobile responsive critical | P1 | Dashboard + fiche bien sur 375px |
| DF-11 | Console error audit | P0 | 0 erreurs console (hors Supabase noise) |
| DF-12 | API latency check | P1 | Endpoints critiques < 2s |

### Exécution

```bash
# Avec le compte démo production
E2E_EMAIL=demo@gerersci.fr \
E2E_PASSWORD=<password> \
pnpm exec playwright test \
  --config e2e/playwright.production.config.ts \
  e2e/production/dogfooding.spec.ts
```

---

## Level 3 — Scénarios Manuels (hebdomadaire)

### Persona 1 : Jean-Pierre, Gérant solo (première visite)

**Profil** : 58 ans, possède 2 SCI (3 biens), gère sur Excel depuis 10 ans
**Objectif** : Découvrir GérerSCI et comprendre la valeur

| # | Action | Ce qu'on cherche |
|---|--------|------------------|
| 1 | Arriver sur gerersci.fr | Hero clair, CTA visible, pas de jargon tech |
| 2 | Scroller la landing | Features compréhensibles, pas de "Lorem ipsum" |
| 3 | Cliquer "Voir les tarifs" | Plans clairs, prix TTC, lifetime visible |
| 4 | Cliquer "Essayer gratuitement" | Inscription fluide, pas de friction |
| 5 | Arriver sur /welcome | Animation crédible, pas de bug visuel |
| 6 | Explorer le dashboard | KPIs lisibles, données demo réalistes |
| 7 | Ouvrir une fiche bien | 10 onglets accessibles, pas de page blanche |
| 8 | Tenter de créer un loyer | LockedAction → UpgradePrompt cohérent |
| 9 | Cliquer "Souscrire" dans le banner | Redirect pricing fluide |

### Persona 2 : Marie, Comptable cabinet (utilisatrice quotidienne)

**Profil** : 35 ans, gère 15 SCI pour des clients, utilise Ownily + Excel
**Objectif** : Workflow quotidien — loyers, charges, quittances

| # | Action | Ce qu'on cherche |
|---|--------|------------------|
| 1 | Se connecter (magic link) | Email arrive < 30s, lien fonctionne |
| 2 | Dashboard → vérifier alertes | Loyers en retard visibles et clairs |
| 3 | SCI Belleville → biens → fiche | Navigation fluide, breadcrumb correct |
| 4 | Enregistrer un loyer payé | Formulaire rapide, montant pré-rempli |
| 5 | Générer une quittance PDF | PDF lisible, accents corrects, logo |
| 6 | Vérifier le bilan mensuel | Chiffres cohérents avec les loyers/charges |
| 7 | Exporter CSV | Fichier se télécharge, colonnes correctes |
| 8 | Consulter la fiscalité | Revenus fonciers = somme des loyers |
| 9 | Vérifier les échéances | Baux expirants, PNO à renouveler |

### Persona 3 : Thomas, Investisseur analytique (évaluation avant achat)

**Profil** : 42 ans, 5 SCI, cherche un outil pour remplacer ses tableurs
**Objectif** : Évaluer si l'outil vaut 39€/mois

| # | Action | Ce qu'on cherche |
|---|--------|------------------|
| 1 | /simulateur-cerfa | Fonctionne sans compte, résultat crédible |
| 2 | /generateur-quittance | PDF gratuit généré, email capture non-bloquant |
| 3 | /calendrier-fiscal | Dates correctes pour 2026 |
| 4 | S'inscrire plan Pilotage | Checkout Stripe fluide, pas d'erreur |
| 5 | Première connexion post-paiement | Données demo nettoyées, onboarding proposé |
| 6 | Onboarding wizard 4 étapes | Confetti à la fin, pas avant |
| 7 | Dashboard multi-SCI | Toutes les SCI visibles, KPIs consolidés |

### Persona 4 : Admin (monitoring interne)

**Profil** : Toi, Radnoumane
**Objectif** : Vérifier la santé du produit

| # | Action | Ce qu'on cherche |
|---|--------|------------------|
| 1 | /admin?secret=... | Dashboard admin charge, KPIs cohérents |
| 2 | Funnel conversion | Chiffres réalistes (pas 0 partout) |
| 3 | Users récents | Liste à jour, pas de doublons |
| 4 | Alertes admin | Actions en attente visibles |
| 5 | Vérifier les logs VPS | Pas d'erreur 500 dans les dernières 24h |

### Persona 5 : Visiteur mobile (smartphone)

**Profil** : N'importe qui sur iPhone/Android
**Objectif** : La landing et le pricing fonctionnent sur mobile

| # | Action | Ce qu'on cherche |
|---|--------|------------------|
| 1 | gerersci.fr sur mobile | Hero lisible, pas de scroll horizontal |
| 2 | Menu hamburger | Fonctionne, liens corrects |
| 3 | Pricing page | Plans lisibles, boutons cliquables |
| 4 | Dashboard (si connecté) | KPIs empilés proprement, pas de overflow |

---

## Template de Findings

```markdown
### [DF-XXX] Titre court du bug

**Sévérité** : 🔴 P0 | 🟡 P1 | 🟢 P2
**Persona** : Jean-Pierre / Marie / Thomas / Admin / Mobile
**Parcours** : Étape X du scénario Y
**Attendu** : Ce qui devrait se passer
**Observé** : Ce qui se passe réellement
**Screenshot** : (si applicable)
**Console** : (erreurs JS si applicable)
**Reproductible** : Toujours / Intermittent / Une fois
```

---

## Calendrier

| Fréquence | Action | Responsable |
|-----------|--------|-------------|
| Post-deploy | Level 1 smoke | CI/CD auto |
| Quotidien | Level 2 dogfooding | Cron ou manuel |
| Lundi matin | Level 3 persona 1-2 | Radnoumane |
| Vendredi | Level 3 persona 3-5 | Radnoumane |
| Post-incident | Level 2 + persona ciblée | Immédiat |
