# SCI Manager Renew

Plateforme SaaS de pilotage pour SCI et parc locatif, conçue pour transformer une gestion artisanale (tableurs, emails, relances manuelles) en système opérationnel structuré.

## 1) Vision business

SCI Manager vise 3 résultats business mesurables pour ses utilisateurs:

- réduire le temps administratif hebdomadaire de gestion locative,
- sécuriser le cashflow (retards, suivi des loyers, quittances),
- professionnaliser le reporting pour associés, comptable et partenaires financiers.

## 2) Problèmes adressés

Les gestionnaires de SCI rencontrent souvent:

- des données dispersées (Excel, mails, dossiers PDF),
- une faible visibilité sur la performance par bien,
- un suivi irrégulier des encaissements,
- une dépendance forte à des routines manuelles.

SCI Manager unifie ces flux dans une interface unique (biens, loyers, documents), avec une logique orientée décision.

## 3) Cibles et cas d'usage

- **Gérant SCI familiale**: centraliser les biens et suivre les paiements.
- **Investisseur multi-biens**: arbitrer par rentabilité et occupation.
- **Cabinet/comptable partenaire**: récupérer des données propres et exploitables.

Cas d'usage prioritaires:

1. Ajouter et maintenir un portefeuille de biens.
2. Enregistrer les loyers et surveiller les retards.
3. Générer des quittances/quitus et constituer un historique documentaire.
4. Consolider les indicateurs de pilotage sur un dashboard.

## 4) État du produit (mars 2026)

- Frontend SvelteKit avec parcours `landing`, `dashboard`, `biens`, `loyers`, `login`, `pricing`.
- Backend FastAPI (`/v1/biens`, `/v1/loyers`, `/v1/quitus`).
- Base Supabase (migrations initiales).
- Storybook professionnel pour documenter design system et écrans.
- Gate de couverture haute valeur à 90% sur logique métier critique.

## 5) Modèle de revenu (à affiner)

Hypothèse actuelle:

- Freemium (1 bien),
- offre Standard (jusqu'à 5 biens),
- offre Pro (multi-biens illimités),
- option onboarding / accompagnement premium.

## 6) Indicateurs de pilotage recommandés

- **North Star**: nombre de SCI actives avec au moins 1 loyer enregistré sur 30 jours.
- Activation: délai moyen entre création de compte et premier bien ajouté.
- Valeur: ratio biens actifs / loyers saisis.
- Rétention: cohortes mensuelles SCI actives.
- Monétisation: conversion freemium -> payant, ARPA, churn logo.

## 7) Stack technique

- Backend: FastAPI, Python 3.12
- Frontend: SvelteKit, TypeScript, Tailwind CSS
- Base de données: Supabase (PostgreSQL)
- Paiements: Stripe
- Outils: Docker, Playwright, Vitest, Storybook

## 8) Démarrage rapide local

```bash
# 1. Démarrer les dépendances locales
cd /workspaces/sci-manager-renew
docker-compose up -d

# 2. Configurer les variables d'environnement
cp .env.example .env

# 3. Lancer l'API
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# 4. Lancer le frontend
cd ../frontend
pnpm install
pnpm run dev -- --port 5173
```

- API: `http://localhost:8001`
- Frontend: `http://localhost:5173`

## 9) Qualité et tests

### Vérifications principales

```bash
cd frontend
pnpm run check
pnpm run build
pnpm run test:high-value
```

`test:high-value` applique un seuil de couverture >= 90% (lignes/fonctions/statements/branches) sur les modules métier critiques.

## 10) Documentation

- Vision & positionnement: [`docs/BUSINESS_FUNCTIONAL_OVERVIEW.md`](docs/BUSINESS_FUNCTIONAL_OVERVIEW.md)
- Parcours fonctionnels et exigences MVP: [`docs/FUNCTIONAL_REQUIREMENTS.md`](docs/FUNCTIONAL_REQUIREMENTS.md)
- Go-to-market & métriques: [`docs/GTM_AND_METRICS.md`](docs/GTM_AND_METRICS.md)
- Architecture technique: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- Audit de maturité: [`AUDIT_BIG4_2026-03-04.md`](AUDIT_BIG4_2026-03-04.md)

## 11) Skills et sub-agents projet

Le dossier [`skills/`](skills/) contient des skills internes pour standardiser les travaux orientés business/produit (documentation, backlog fonctionnel, stratégie go-to-market).
