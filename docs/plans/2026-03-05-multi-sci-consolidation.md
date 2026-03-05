# 2026-03-05 Multi-SCI Consolidation Audit

## Objectif

Fournir un cadrage produit/technique pour faire évoluer GererSCI d'un cockpit mono-contexte vers une solution multi-SCI pilotable, avec une fiche d'identité SCI exploitable, une distinction claire entre menu public et menu connecté, et un espace paramètres structuré.

## Inventaire Markdown audité

### Documents métier et cadrage

- `docs/FUNCTIONAL_REQUIREMENTS.md`
- `docs/BUSINESS_FUNCTIONAL_OVERVIEW.md`
- `AUDIT_BIG4_2026-03-04.md`
- `.github/copilot-instructions.md`
- `README.md`
- `ARCHITECTURE.md`

### Documents d'exécution et conformité

- `docs/plans/2026-03-05-production-readiness-blockers.md`
- `claudedocs/solution_audit_2026-03-05.md`
- `claudedocs/compliance-audit-report.md`
- `backend/docs/deployment-checklist.md`
- `backend/docs/secrets-management.md`

### Constat clé

Le corpus documentaire converge sur quatre besoins prioritaires:

1. fiabiliser le coeur métier `SCI -> biens -> loyers -> documents`,
2. rendre le pilotage multi-SCI réellement fluide,
3. améliorer la lisibilité métier du dashboard et supprimer les IDs techniques de l'expérience,
4. clarifier la conformité RGPD, le naming et les espaces de gestion du compte.

## Cas d'usage consolidés

### UC-01: Gérer plusieurs SCI depuis un même compte

- L'utilisateur visualise la liste des SCI auxquelles il a accès.
- Il change de contexte actif sans se reconnecter.
- Tous les écrans `dashboard`, `biens`, `loyers` et `documents` se recalculent selon la SCI active.

### UC-02: Ouvrir une vraie fiche d'identité SCI

- L'utilisateur consulte les informations de base de la SCI: nom, SIREN, régime fiscal, statut d'exploitation.
- Il voit la gouvernance: associés, rôle, part détenue.
- Il accède aux biens, aux loyers récents, aux charges et aux repères fiscaux associés à cette SCI.

### UC-03: Distinguer l'expérience publique de l'espace connecté

- Le visiteur non connecté voit un menu marketing simple.
- L'utilisateur connecté voit un shell de pilotage: cockpit, SCI, biens, loyers, compte, paramètres, confidentialité.

### UC-04: Gérer les paramètres opérateur

- L'utilisateur définit sa page d'ouverture favorite.
- Il règle sa densité d'affichage, la prévisualisation PDF et ses alertes.
- Il distingue clairement les paramètres d'application des paramètres de compte.

### UC-05: Exercer les droits compte / privacy

- L'utilisateur retrouve un espace compte.
- Il peut rejoindre l'espace confidentialité / données sans friction.
- Le wording, le domaine et l'email de contact utilisent la marque actuelle `GererSCI`.

## Consolidation des entités solution

### Entité `SCI`

État avant audit:

- liste synthétique disponible,
- contexte actif stocké en local,
- pas de page dédiée au portefeuille SCI,
- pas de fiche d'identité consolidée.

État cible:

- `SCIOverview`: vue liste / navigation,
- `SCIDetail`: vue portefeuille avec:
  - identité (`nom`, `siren`, `regime_fiscal`, `statut`),
  - gouvernance (`associes`, `user_role`, `user_part`),
  - patrimoine (`biens`, `total_monthly_rent`, `total_monthly_property_charges`),
  - flux (`recent_loyers`, `paid_loyers_total`, `pending_loyers_total`),
  - charges (`recent_charges`, `total_recorded_charges`, `charges_count`),
  - repères fiscaux (`fiscalite`).

### Entité `Associé`

Rôle produit:

- représenter la gouvernance d'une SCI,
- préciser la part détenue,
- afficher le rôle opérationnel visible par l'utilisateur.

### Entité `Bien`

Rôle produit:

- rester rattachée à une SCI,
- servir de source de vérité pour les loyers et charges,
- exposer l'adresse comme identifiant métier principal.

### Entité `Charge`

Rôle produit:

- matérialiser les sorties par bien,
- alimenter la fiche SCI,
- compléter le pilotage portefeuille sans forcer une comptabilité générale complète.

## Écarts identifiés avant remédiation

- Pas de route dédiée aux détails d'une SCI.
- Pas de page produit dédiée à la gestion multi-SCI.
- Menu connecté encore trop proche du menu public.
- Paramètres compte / application absents.
- Résidus de marque `SCI Manager` / `scimanager.fr` encore visibles dans la privacy.
- Dépendance locale forte au backend/Supabase pour les démonstrations réelles.

## Remédiation livrée dans cette phase

- Ajout d'un endpoint backend `GET /api/v1/scis/{sci_id}` pour exposer une fiche SCI consolidée.
- Ajout d'une page frontend `scis/+page.svelte` dédiée au portefeuille multi-SCI.
- Ajout d'un espace `settings/+page.svelte` pour les paramètres d'application.
- Ajout d'un espace `account/+page.svelte` pour les paramètres de compte.
- Enrichissement du menu connecté avec des accès distincts `SCI`, `Compte`, `Paramètres`, `Confidentialité`.
- Nettoyage des résidus de renommage sur les écrans privacy principaux.

## Backlog recommandé

### Priorité haute

- CRUD complet sur les SCI et les associés.
- CRUD des charges pour éviter une fiche SCI uniquement consultative.
- normalisation des labels métier dans tous les tableaux et PDF.
- stabilisation E2E sur le shell connecté.

### Priorité moyenne

- préférences d'application persistées côté backend par utilisateur,
- paramétrage des notifications / digest,
- historique d'audit visible par SCI.

### Priorité basse

- fiscalité simulée par SCI,
- documents packagés par exercice,
- benchmark portefeuille inter-SCI.
