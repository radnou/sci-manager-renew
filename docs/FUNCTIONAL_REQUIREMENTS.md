# Functional Requirements (MVP+)

## 1) Périmètre fonctionnel

Le périmètre actuel couvre les domaines à plus fort ROI opérationnel:

- `Biens`: création et suivi portefeuille.
- `Loyers`: enregistrement, statuts, historique.
- `Documents`: génération de quittances/quitus.
- `Dashboard`: synthèse exécution business.

## 2) Parcours clés

## Parcours A: Onboarding gestionnaire

1. Connexion.
2. Ajout du premier bien.
3. Saisie du premier loyer.
4. Visualisation des KPI.

**Critère de succès**: parcours complet en moins de 10 minutes.

## Parcours B: Suivi d'encaissement

1. Ouvrir l'espace loyers.
2. Filtrer/identifier les statuts en retard.
3. Ajouter un nouveau loyer ou corriger un statut.

**Critère de succès**: identification d'un retard en moins de 60 secondes.

## Parcours C: Production documentaire

1. Générer un quittus depuis l'interface.
2. Prévisualiser le PDF.
3. Préparer le partage vers locataire ou comptable.

**Critère de succès**: document lisible et récupérable sans outil tiers.

## 3) User stories prioritaires

### Biens

- En tant que gérant, je veux enregistrer une adresse, une ville, un loyer et un statut pour suivre chaque actif.
- En tant que gérant, je veux voir les biens dans un tableau lisible avec état vide/chargement.

### Loyers

- En tant que gérant, je veux saisir rapidement un paiement avec date, bien et montant.
- En tant que gérant, je veux distinguer `payé`, `en attente`, `retard` pour prioriser mes actions.

### Dashboard

- En tant que décideur, je veux visualiser les KPI (potentiel, encaissements, taux d'occupation) sans retraitement manuel.

### Documents

- En tant que gestionnaire, je veux générer un quittus et vérifier le rendu PDF depuis l'outil.

## 4) Exigences non fonctionnelles

- UX responsive desktop/mobile.
- Temps de chargement raisonnable pour tableaux standards.
- Gestion explicite des erreurs API côté UI.
- Typage strict et composants réutilisables.

## 5) État de couverture haute valeur

Les modules critiques sont couverts par `pnpm run test:high-value` avec seuil à 90%:

- `src/lib/api.ts`
- `src/lib/high-value/biens.ts`
- `src/lib/high-value/loyers.ts`
- `src/lib/high-value/formatters.ts`

## 6) Backlog fonctionnel recommandé

1. Authentification/autorisation alignée RLS + contexte utilisateur.
2. Gestion multi-SCI complète (sélecteur contexte).
3. Export comptable structuré (CSV/PDF standardisé).
4. Alertes proactives (retards, anomalies de cashflow).
