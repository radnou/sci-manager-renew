# Audit Solution & Landing Page - GererSCI

**Date**: 5 mars 2026
**Scope**: backend FastAPI, frontend SvelteKit, documentation métier `docs/*.md` et études `claudedocs/*.md`

## 1) Résumé exécutif

La solution couvre déjà le coeur de valeur du MVP SCI (auth, biens, loyers, KPI, quittance PDF, paiement Stripe). La proposition est pertinente pour un segment SCI familiale / petit portefeuille.

Le point bloquant principal est l'alignement entre promesse commerciale et réalité produit, avec un risque de confiance (claims de landing/pricing/FAQ plus avancés que la couverture réelle). Un point technique critique est aussi présent sur la couche data (`owner_id` utilisé par l'API mais absent du schéma SQL initial).

## 2) Fonctionnalités présentes et valeur ajoutée

### Fonctionnalités effectivement en place

- **Authentification passwordless (magic link)** via Supabase.
- **Gestion multi-SCI** (sélecteur de contexte, persistance locale).
- **CRUD Biens** avec calculs de rentabilité/cashflow.
- **CRUD Loyers** avec filtres période/statut.
- **Dashboard KPI** consolidé biens + loyers.
- **Génération de quittance PDF** et prévisualisation.
- **Checkout Stripe** (session de paiement).
- **Pages RGPD** (politique + espace “mes données”).
- **Observabilité de base** (logging middleware, request id, `/health/live`, `/health/ready`).

### Valeur business immédiate

- **Gain de temps opérationnel**: moins de tableurs et de ressaisie.
- **Visibilité cashflow**: suivi rapide des encaissements et retards.
- **Standardisation documentaire**: quittance générée depuis la plateforme.
- **Capacité de monétisation**: tunnel pricing + Stripe déjà en place.

## 3) Gaps et risques (priorité)

### Critique

1. **Incohérence modèle de données API/DB**
- L'API filtre `biens` et `loyers` sur `owner_id`, alors que le schéma `supabase/migrations/001_init.sql` ne crée pas cette colonne.
- Risque: erreurs runtime SQL ou filtrage incohérent en production.

2. **Promesse marketing > produit réel**
- Exemples visibles: imports CSV/Excel guidés, Cerfa 2072, chat support, API access, reporting avancé mentionnés côté landing/pricing/FAQ alors que la couverture code est partielle ou absente.
- Risque: baisse conversion qualifiée et churn précoce après essai.

### Important

3. **Quittance non persistée durablement**
- Stockage in-memory des PDF (`_quitus_files`) côté backend.
- Risque: perte des documents au redémarrage, non compatible scaling multi-instance.

4. **RGPD endpoints encore “placeholder”**
- `data-summary`, `data-export`, `delete-account` renvoient des réponses simulées.
- Risque: non-conformité opérationnelle si présenté comme fully compliant.

5. **Parcours d'activation incomplet**
- `LoyerForm` demande un `id_bien` manuel, pas de sélection guidée depuis les biens de la SCI active.
- Risque: friction forte pour les nouveaux utilisateurs.

## 4) Fonctionnalités faisables (pain points -> solutions)

| Pain point client | Fonctionnalité proposée | Faisabilité technique | Impact |
|---|---|---|---|
| "Je perds du temps à migrer depuis Excel" | Import CSV/Excel avec mapping colonnes + prévalidation | **Élevée** (frontend wizard + endpoint d'import + validations Pydantic) | **Très fort** (activation) |
| "Je découvre les retards trop tard" | Alertes automatiques retards (email + digest hebdo) | **Élevée** (jobs planifiés + Resend + statut loyers) | **Très fort** (rétention) |
| "Je veux transmettre au comptable sans retraitement" | Export comptable standardisé (CSV fiscal + journaux loyers/charges) | **Élevée** (tables existantes + endpoint export) | **Fort** |
| "Je veux une preuve documentaire fiable" | Stockage persistant des quittances (Supabase Storage) + historique | **Élevée** (service storage déjà présent) | **Fort** |
| "Je gère plusieurs SCI avec associés" | Gestion des rôles par SCI (admin/associe/comptable) | **Moyenne** (RLS + UI permissions) | **Fort** |
| "Je veux comprendre ma rentabilité réelle" | Module fiscal IR/IS + simulation scénarios | **Moyenne** (tables fiscalité existantes, moteur calcul) | **Fort** |

## 5) Plan recommandé (90 jours)

### Sprint 1 (0-30 jours)

- Corriger l'alignement API/DB (`owner_id` vs RLS/membership).
- Rendre le messaging landing/pricing strictement conforme aux features réelles.
- Passer les quittances sur stockage persistant + liens signés.

### Sprint 2 (30-60 jours)

- Livrer import CSV/Excel guidé (biens + loyers).
- Livrer alertes retards basiques (J+3/J+7).
- Livrer export comptable v1.

### Sprint 3 (60-90 jours)

- RGPD opérationnel réel (export + suppression orchestrée).
- Simulation fiscale IR/IS v1.
- Parcours onboarding assisté (wizard premier bien + premier loyer).

## 6) Audit landing page et mise à jour effectuée

Des modifications ont été appliquées pour intégrer les études du fichier `claudedocs/landing_page_update_2026-03-05.md` et améliorer la cohérence UX:

- Ajout d'une section **"Études détaillées consultées"** avec liens source vérifiables.
- Ajout d'ancres de navigation (`#features`, `#market-data`, `#studies`).
- Correction du footer (suppression des liens morts, remplacement par des routes/sections existantes).
- Mise à jour de la mention légale de l'année (`© 2026`).

## 7) Recommandation stratégique

Pour gagner des clients durablement:

1. **Vendre ce qui est déjà robuste** (biens, loyers, KPI, quittance, multi-SCI de base).
2. **Arrêter les claims non livrés** jusqu'à disponibilité réelle.
3. **Prioriser activation et rétention** (import, alertes, export) avant l'élargissement des features avancées.

