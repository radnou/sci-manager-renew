# GTM & Metrics Strategy - GererSCI (France)

## 1) Objectif

Definir un plan go-to-market exploitable avec un cadre de pilotage KPI orienté decisions.

## 2) Strategic thesis

These de croissance recommandee:
- `Beachhead` sur SCI 1-20 biens en France,
- acquisition par preuve de valeur (temps gagne + controle + simplicite),
- conversion rapide par packaging lisible,
- retention par usage recurrent du module loyers/dashboard.

## 3) Positionnement et message

Probleme client:
- "La gestion est diffuse, je manque de visibilite et je perds du temps sur le suivi."

Promesse GererSCI:
- "Piloter vos SCI avec une execution professionnelle et une charge administrative reduite."

Piliers de preuve:
- rapidite de prise en main,
- fiabilite des donnees,
- reduction des oublis et retards,
- documentation generee a la demande.

## 4) Segments et priorisation commerciale

## Segment S1 - SCI familiales (1-5 biens)

- objectif: acquisition volume et cas d'usage repetables,
- offre recommandee: Starter.

## Segment S2 - Investisseurs patrimoniaux (6-20 biens)

- objectif: ARPA superieur et adoption profonde,
- offre recommandee: Pro.

## Segment S3 - Cabinets partenaires (post-PMF)

- objectif: canal scalable B2B2C,
- prerequis: robustesse produit et support.

Priorite: S1 + S2 en direct, S3 en pilote controle.

## 5) Funnel de reference et definitions

## 5.1 Funnel

1. Acquisition: visite qualifiee landing.
2. Activation: `1 SCI + 1 bien + 1 loyer`.
3. Adoption: usage recurrent hebdomadaire.
4. Conversion: abonnement payant.
5. Expansion: ajout biens/SCI ou upgrade plan.

## 5.2 Definitions strictes

- "Compte active" = au moins 1 loyer cree sur 30 jours.
- "Compte adopte" = au moins 2 sessions/semaine pendant 4 semaines.
- "Compte converti" = abonnement payant actif.

## 6) KPI tree (pilotage de direction)

North Star KPI:
- nombre de SCI actives (30 jours).

Leviers primaires:
- Acquisition qualifiee,
- Activation rapide,
- Retention,
- Monetisation.

## 6.1 KPI acquisition

- trafic organique qualifie,
- CTR CTA primary (`/login`, `/pricing`),
- CAC par canal,
- taux de rebond landing.

## 6.2 KPI activation

- `% comptes avec 1 bien en <24h`,
- `% comptes avec 1 loyer en <7 jours`,
- median `time_to_first_value`.

## 6.3 KPI retention

- WAU/MAU,
- retention cohortes M1/M3,
- frequence usage module loyers,
- taux de retour hebdomadaire des comptes actifs.

## 6.4 KPI monetisation

- conversion free/trial -> paid,
- ARPA,
- MRR net,
- churn logos,
- churn revenu.

## 7) Objectifs cibles (cadre 90 jours)

Cibles a ajuster apres baseline instrumentee:
- activation: +30% vs baseline,
- time_to_first_value: -40% vs baseline,
- conversion payante: +20% vs baseline,
- churn mensuel: -15% vs baseline.

Note de gouvernance:
- ces cibles sont des hypotheses de travail et doivent etre confirmees au 1er cycle de mesure.

## 8) Plan d'actions GTM

## 8.1 Acquisition

1. SEO editorial cible SCI France (fiscalite, loyers, quitus, erreurs frequentes).
2. distribution communautes investisseurs (contenu pratique + cas reels).
3. campagnes paid testees en micro-budget avec seuils d'arret explicites.

## 8.2 Activation

1. simplifier le parcours onboarding,
2. proposer templates de donnees initiales,
3. ajouter checklists "premiere valeur" dans le produit.

## 8.3 Conversion

1. clarifier la comparaison Starter vs Pro,
2. proposer preuve de ROI (temps gagne / erreurs evitees),
3. sequence email orientee activation puis conversion.

## 8.4 Expansion

1. scenarii d'upgrade lie au nombre de biens,
2. offres partenaire pilote (cabinet),
3. programme referral cible investisseurs.

## 9) Backlog experimentation (priorise)

1. Test headline landing: "gain de temps" vs "controle du cashflow".
2. Test CTA principal: "Demarrer" vs "Demander une demo".
3. Test pricing page: comparaison simple vs detaillee.
4. Test onboarding: formulaire long vs parcours guide en 3 etapes.
5. Test preuve sociale: cas clients chiffres vs temoignages qualitatifs.

## 10) Instrumentation minimale requise

Events prioritaires:
- `signup_completed`,
- `sci_created`,
- `bien_created`,
- `loyer_created`,
- `checkout_started`,
- `checkout_succeeded`,
- `quitus_generated`.

Attributs minimum:
- `user_id`, `account_id`, `plan`, `channel`, `timestamp`, `device_type`.

Regles:
- nomenclature stable,
- horodatage UTC,
- source unique de verite KPI (dashboard unique).

## 11) Operating model de pilotage

Hebdomadaire:
- review activation + incidents bloquants + experiments en cours.

Mensuel:
- review funnel complet + allocation budget canaux + decisions produit.

Trimestriel:
- revue positionnement, pricing, segments, roadmap.

## 12) Alerting management (seuils)

Declencher plan d'action si:
- activation chute >20% vs moyenne 4 semaines,
- churn revenu > seuil directeur 2 mois consecutifs,
- conversion pricing baisse >15% apres un changement.
