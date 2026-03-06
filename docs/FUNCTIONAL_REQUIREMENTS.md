# Functional Requirements - GererSCI (MVP -> Scale)

## 1) Objectif du document

Definir un cadre de requirements exploitable par produit, engineering et QA, avec priorisation claire et criteres d'acceptation mesurables.

## 2) Perimetre produit

## 2.1 In Scope (MVP actuel)

- Authentification par magic link,
- gestion des SCI,
- gestion des biens,
- gestion des loyers,
- generation de quittance/quitus,
- tableau de bord operationnel,
- paiement/abonnement Stripe,
- pages de conformite privacy/GDPR.

## 2.2 Out of Scope (phase suivante)

- comptabilite generale complete,
- rapprochement bancaire automatique,
- OCR de documents,
- application mobile native,
- marketplace tiers.

## 3) Personas et jobs-to-be-done

1. Gerant de SCI (owner-operator)
- JTBD: "Voir l'etat de mon portefeuille et agir vite sur les retards."

2. Investisseur multi-biens
- JTBD: "Standardiser ma gestion et fiabiliser mes decisions cashflow."

3. Cabinet comptable partenaire (phase ulterieure)
- JTBD: "Recuperer des donnees propres et coherentes sans relances."

## 4) Parcours critiques et SLA experience

## 4.1 Parcours A - Time to First Value

Etapes:
1. Connexion,
2. creation 1 SCI,
3. ajout 1 bien,
4. ajout 1 loyer,
5. visualisation dashboard.

SLA produit cible:
- parcours complet en moins de 10 minutes,
- taux de completion superieur a 60% des comptes nouveaux.

## 4.2 Parcours B - Pilotage des retards

Etapes:
1. ouverture module loyers,
2. filtration des statuts en retard,
3. mise a jour du statut apres action.

SLA produit cible:
- identification d'un retard en moins de 60 secondes,
- action corrective en moins de 3 clics depuis la liste.

## 4.3 Parcours C - Production documentaire

Etapes:
1. generation quittance/quitus,
2. previsualisation,
3. telechargement.

SLA produit cible:
- generation en moins de 5 secondes pour un document standard,
- taux d'echec de generation inferieur a 1%.

## 5) Functional Requirements (FR)

## 5.1 Authentification et acces

- FR-AUTH-001: l'utilisateur peut demander un magic link par email.
- FR-AUTH-002: un token invalide/expire retourne une erreur explicite.
- FR-AUTH-003: les endpoints proteges exigent un bearer token valide.

Criteres d'acceptation:
- tentative sans token -> HTTP 401,
- tentative avec token invalide -> HTTP 401,
- session valide -> acces endpoints autorises.

## 5.2 Gestion SCI

- FR-SCI-001: creer une SCI avec identifiant unique.
- FR-SCI-002: lister les SCI de l'utilisateur.
- FR-SCI-003: selectionner un contexte actif de SCI dans l'interface.

Criteres d'acceptation:
- donnees creees visibles immediatement dans la liste,
- aucune fuite de donnees entre utilisateurs.

## 5.3 Gestion Biens

- FR-BIEN-001: creer/modifier/supprimer un bien.
- FR-BIEN-002: champs minimaux requis (adresse, ville, code_postal, type, loyer, charges).
- FR-BIEN-003: affichage tableau avec etats loading/empty/error.

Criteres d'acceptation:
- CRUD complet sans rechargement navigateur,
- validation UI et API coherente sur les champs obligatoires.

## 5.4 Gestion Loyers

- FR-LOYER-001: creer/modifier/supprimer un loyer rattache a un bien.
- FR-LOYER-002: statuts supportes: `en_attente`, `paye`, `en_retard`.
- FR-LOYER-003: filtrer par SCI et plage de dates.

Criteres d'acceptation:
- tout changement de statut est visible en liste sans incoherence,
- requetes filtrees retournent uniquement le scope demande.

## 5.5 Documents (quittance/quitus)

- FR-DOC-001: generer un PDF a partir d'un loyer et des donnees associees.
- FR-DOC-002: telecharger le PDF genere depuis l'interface.
- FR-DOC-003: gerer proprement les erreurs de generation.

Criteres d'acceptation:
- fichier telechargeable et non corrompu,
- message d'erreur actionnable en cas d'echec.

## 5.6 Dashboard

- FR-DB-001: afficher KPI de pilotage essentiels.
- FR-DB-002: coherent avec les donnees biens/loyers courantes.
- FR-DB-003: acces rapide aux actions prioritaires.

Criteres d'acceptation:
- KPI sans retraitement manuel,
- actualisation apres mutation de donnees metier.

## 5.7 Paiement Stripe

- FR-PAY-001: creation de session checkout depuis un `plan_key`, resolu cote backend vers le `price_id` Stripe actif.
- FR-PAY-002: redirection vers page succes/annulation.
- FR-PAY-003: endpoint webhook valide la signature Stripe.
- FR-PAY-004: l'abonnement expose les entitlements de compte (SCI, biens, fonctionnalites activees).
- FR-PAY-005: les creations SCI et biens refusent proprement les depassements de quota.

Criteres d'acceptation:
- webhook signature invalide -> HTTP 400,
- paiement valide -> statut succes coherent.

## 6) Non-Functional Requirements (NFR)

- NFR-SEC-001: secrets absents du code versionne.
- NFR-SEC-002: headers de securite actifs en production.
- NFR-SEC-003: CORS strictement borne aux domaines production.
- NFR-REL-001: endpoints de sante `/health/live` et `/health/ready` operationnels.
- NFR-REL-002: restart automatique services backend/frontend.
- NFR-PERF-001: temps de reponse p95 API critique < 500 ms hors appels tiers.
- NFR-UX-001: interface responsive desktop/mobile.
- NFR-QUAL-001: tests unitaires et high-value maintenus au-dessus des seuils cibles.

## 7) Data & compliance requirements

- DCR-001: minimisation des donnees personnelles stockees,
- DCR-002: traçabilite minimale des actions critiques,
- DCR-003: capacite d'export/suppression des donnees utilisateur (privacy),
- DCR-004: coherence des bases legales communiquees dans la politique privacy.

## 8) Priorisation backlog (MoSCoW)

## Must have

1. Stabilite auth + controle d'acces,
2. fiabilite CRUD biens/loyers,
3. generation PDF robuste,
4. observabilite minimale prod (logs + health),
5. parcours activation en moins de 10 minutes.

## Should have

1. alertes retards automatiques,
2. exports operationnels structures,
3. mode multi-SCI plus fluide (contexte persistant).

## Could have

1. rappels automatiques personnalises,
2. templates de workflow par type de SCI,
3. benchmark de performance portefeuille.

## Won't have (court terme)

1. application mobile native,
2. suite comptable complete,
3. OCR massif documentaire.

## 9) Definition of Done (release gate)

Une release est "go" uniquement si:
- 100% des Must have de la release sont testes,
- aucun bug P0/P1 ouvert,
- checks health OK en environnement cible,
- tests de non-regression critiques passes,
- plan de rollback documente et teste.

## 10) Plan 90 jours recommande

1. Sprint 1-2: robustesse auth + donnees,
2. Sprint 3-4: acceleration activation + UX parcours,
3. Sprint 5-6: fiabilisation docs/paiement + observabilite,
4. Sprint 7+: optimisation conversion et retention.
