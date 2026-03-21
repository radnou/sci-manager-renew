# Findings Recette — 21 mars 2026
## 11 OK | 8 KO | 8 Partiel

### P0 — Bugs bloquants à corriger immédiatement

| # | Test | Finding | Action |
|---|---|---|---|
| 1 | NAV-001 | Exploitation, AG, Mouvements de parts absents de la sidebar | Vérifier AppSidebarV2 déployé |
| 2 | BIEN-004 | 402 sur /fiscalite/ en plan Essentiel → erreur console pollue | Frontend doit NE PAS appeler l'API fiscalité si plan free |
| 3 | BIEN-004 | 404 sur /api/v1/import/templates/biens | Endpoint manquant |
| 4 | BIEN-004 | 422 sur /charges et /loyers | Payload validation error |
| 5 | BIEN-006 | Période et mois en anglais dans le formulaire loyer | Locale FR manquante |
| 6 | BIEN-006 | 2 boutons fermer (texte + croix) | UI doublon |
| 7 | AG-001/002 | AG KO — page ne charge pas | Vérifier route + données |
| 8 | FISC-001 | Redirect vers pricing déconnecte l'user | Bug route-guard |
| 9 | AUTH-002 | Magic link: rien dans Mailpit | Dev mode log-only, pas d'email |
| 10 | BIEN-001 | Templates CSV 404 | Endpoints import/templates non créés |

### P1 — UX/Fonctionnel important

| # | Test | Finding | Action |
|---|---|---|---|
| 11 | PUB-005 | CGV: adresse app.gerersci.fr au lieu de gerersci.fr | Corriger |
| 12 | PUB-005 | CGV: prix ne correspondent pas aux produits | Mettre à jour 19/39€ |
| 13 | PUB-005 | Pages légales: fautes d'orthographe et accents | Audit texte |
| 14 | BIEN-001 | "Loué" au lieu de "Occupé" comme badge statut | Corriger le label |
| 15 | BIEN-005 | Quittance affiche "SCI SCI Belleville Patrimoine" (doublé) | Fix préfixe |
| 16 | BIEN-002 | Type locatif "nu" en minuscule → "Nu" ou "Location nue" | Formatter |
| 17 | SCI-003 | Export CSV: IDs au lieu de noms (SCI, bien) | Humaniser les exports |
| 18 | SCI-003 | Export CSV absent de la vue d'ensemble SCI | Ajouter boutons |
| 19 | DASH-002 | Texte biens/recouvrement trop petit, tooltip manquant | UI polish |
| 20 | NAV-003 | Dark mode: alertes/contrastes pas assez lisibles | CSS dark fix |

### P2 — Améliorations produit (backlog)

| # | Test | Finding | Action |
|---|---|---|---|
| 21 | PUB-006 | Conditionner simulateur par capture email/intention | Lead capture |
| 22 | AUTH-001 | Tooltips sur alertes loyers impayés | UX enrichment |
| 23 | DASH-003 | Clic activité récente → lien vers entité | Navigation |
| 24 | SCI-002 | Infos légales sur vue SCI (pas juste settings) | Déjà implémenté ? |
| 25 | BIEN-002 | Nommer biens avec numéro lot (immeuble multi-apparts) | Data model |
| 26 | BIEN-002 | Graphiques rentabilité + tableau annuel depuis acquisition | Feature |
| 27 | BIEN-002 | Pastilles durée bail + calcul date fin + alertes | Feature |
