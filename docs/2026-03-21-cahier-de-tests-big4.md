# Cahier de Tests Big4 — Référentiel de Validation GererSCI
**Date** : 2026-03-21  
**Auteur** : Codex  
**Objectif** : définir le jeu de tests de référence de GererSCI, à enrichir jusqu’à couverture fonctionnelle cible et à rejouer automatiquement à chaque déploiement.

---

## 1. Positionnement

Ce document n’est pas un simple compte-rendu de recette.  
C’est le référentiel de validation fonctionnelle de GererSCI:

- base de recette manuelle experte
- base d’automatisation technique
- base de `Go / No-Go` avant mise en production
- base de régression à rejouer à chaque déploiement

La logique retenue est celle d’une équipe de validation fonctionnelle Big4:

- raisonner par processus métier complets
- tester les droits, erreurs, exceptions et états vides
- vérifier la cohérence entre UI, API et règle métier SCI
- séparer les tests `bloquants business` des tests `de confort`
- exiger des preuves automatiques réexécutables

---

## 2. Verdict actuel

### 2.1 Score fonctionnel actuel

| Domaine | Score / 5 | Commentaire |
|---|---:|---|
| Authentification & accès | 4.0 | Base saine, mais lien magique expiré et quelques flux à revalider en prod dédiée |
| Navigation & structure app | 4.0 | Parcours principaux stables, liens dynamiques corrigés |
| Gestion SCI | 4.0 | CRUD principal présent, encore peu de validations E2E profondes sur cas limites |
| Gestion biens / bail / loyers / charges | 4.0 | Fiche bien nettement améliorée, encore trop modale dans son design |
| Documents | 4.0 | Vue agrégée et état vide corrigés |
| Fiscalité | 3.0 | Paywall fonctionnel, mais implémentation bruyante (`402` console) |
| Paiement / monétisation | 1.0 | `No-Go` tant que Stripe prod renvoie `503` |
| Résilience / offline / déploiement | 2.0 | Bannière présente, mais pas de vrai mécanisme de maintenance/sync |

### 2.2 Go / No-Go

**Verdict du jour** : `NO-GO commercial`

Motif principal:

- `P0` checkout Stripe prod indisponible sur [https://app.gerersci.fr/pricing](https://app.gerersci.fr/pricing)

Motifs secondaires:

- gating fiscalité encore bruyant
- mécanisme hors ligne/reconnexion trompeur par rapport à la promesse affichée

---

## 3. Findings prod confirmés au 21 mars 2026

### F-001 — Checkout Stripe prod KO

- **Sévérité** : `P0`
- **URL** : [https://app.gerersci.fr/pricing](https://app.gerersci.fr/pricing)
- **Constat** :
  - clic `Choisir Gestion`
  - `POST https://api.gerersci.fr/api/v1/stripe/create-guest-checkout`
  - réponse `503`
- **Cause runtime confirmée** :
  - [https://api.gerersci.fr/health/ready](https://api.gerersci.fr/health/ready) retourne désormais `status: not_ready`
  - `stripe.error = "stripe checkout catalog invalid"`
  - `invalid_price_ids = starter_monthly, starter_annual, pro_monthly, pro_annual, cabinet_monthly, cabinet_annual`
- **Impact** : conversion impossible

### F-002 — Fiscalité Pro: bon paywall, mauvaise implémentation technique

- **Sévérité** : `P2`
- **URL** : [https://gerersci.fr/scis/c4ca09ad-16cb-45e5-8273-ab62e2e09184/fiscalite](https://gerersci.fr/scis/c4ca09ad-16cb-45e5-8273-ab62e2e09184/fiscalite)
- **Constat** :
  - l’UI affiche correctement `Fonctionnalité Pro`
  - mais l’API renvoie `402`
  - une erreur console est visible
- **Impact** :
  - dette technique
  - UX moins propre
  - monitoring navigateur pollué

### F-003 — Faux sentiment de mode offline / synchronisation

- **Sévérité** : `P1` produit / `P2` technique
- **Constat code** :
  - [connectivity.ts](/Users/radnoumanemossabely/Code/sci-manager-renew/frontend/src/lib/stores/connectivity.ts) ne fait que lire `navigator.onLine`
  - [OfflineBanner.svelte](/Users/radnoumanemossabely/Code/sci-manager-renew/frontend/src/lib/components/OfflineBanner.svelte) affiche
    `Connexion perdue — vos modifications seront synchronisées au retour`
  - mais il n’existe pas de vraie file offline, ni service worker, ni replay transactionnel, ni sync queue
- **Impact** :
  - promesse UX exagérée
  - risque de mauvaise compréhension utilisateur

---

## 4. Réponse sur le “mode hors ligne / maintenance / reconnexion”

### 4.1 Ce qui existe aujourd’hui

Il existe bien un mécanisme visuel minimal:

- détection `online / offline / reconnecting`
- bannière d’alerte utilisateur

### 4.2 Ce qui n’existe pas aujourd’hui

Il n’y a pas, à ce stade:

- de service worker offline métier
- de file locale de mutations à rejouer
- de stratégie de verrouillage pendant déploiement
- de notification serveur “maintenance en cours”
- de synchronisation transactionnelle post-reconnexion
- de versioning frontend/back couplé avec invalidation de session UI

### 4.3 Conclusion

Donc votre intuition est partiellement juste sur l’intention produit, mais **ce mécanisme n’est pas réellement implémenté**.

En l’état, le système affiche un message qui suggère une synchronisation future, alors qu’il n’existe pas de moteur de synchronisation offline fiable.

### 4.4 Garde-fou retenu

À court terme, le bon dispositif est plus simple et plus honnête:

- bannière frontend qui n’annonce pas une synchronisation inexistante
- healthcheck de readiness bloquant avant remise sous trafic
- smoke tests prod publics après déploiement
- smoke tests prod authentifiés via lien magique réel ou secret dédié

---

## 5. Principe du jeu de tests cible

Le jeu de tests cible doit couvrir `100% des parcours métier critiques`, pas `100% des lignes de code`.

### 5.1 Niveaux de validation

| Niveau | Objet | Outil | Fréquence |
|---|---|---|---|
| L1 | logique pure | `pytest`, `vitest` | chaque push |
| L2 | API métier | `pytest` | chaque push |
| L3 | composants UI | `vitest-browser` | chaque push |
| L4 | parcours E2E mockés | `Playwright validation` | chaque push |
| L5 | smoke staging / prod | `Playwright live` | chaque déploiement |
| L6 | audit visuel | `Playwright screenshots` | release candidate |
| L7 | recette métier humaine | panel utilisateurs | avant release majeure |

### 5.2 Règle Big4

Un domaine n’est pas “couvert” tant que les 4 axes suivants ne sont pas validés:

1. `happy path`
2. `erreur fonctionnelle`
3. `droit / rôle`
4. `état vide / reprise`

---

## 6. Périmètre fonctionnel à couvrir

### 6.1 Public / acquisition

- landing
- pricing
- simulateur CERFA public
- register
- login
- forgot password
- magic link

### 6.2 Noyau app

- dashboard
- navigation globale
- switch SCI
- breadcrumbs
- notifications
- settings / account

### 6.3 Métier SCI

- création SCI
- modification SCI
- suppression SCI
- associés
- mouvements de parts
- assemblées générales

### 6.4 Métier immobilier

- création bien
- édition bien
- fiche bien
- bail
- locataires
- loyers
- charges
- PNO
- frais d’agence
- rentabilité
- quittances
- documents

### 6.5 Fiscalité / conformité

- exercices fiscaux
- génération CERFA 2044
- règles IR / IS
- paywall fiscalité
- exports
- RGPD

### 6.6 Paiement / abonnement

- page pricing
- checkout invité
- checkout connecté
- portail client Stripe
- entitlements plan free / starter / pro / cabinet
- limites SCI / biens

### 6.7 Exploitation / résilience

- health checks
- comportement en perte réseau
- retour réseau
- déconnexion
- déploiement en cours
- refresh de version frontend

---

## 7. Matrice de criticité

### 7.1 P0 — Bloquants business

Les cas suivants doivent être verts à `100%` avant tout déploiement prod:

- authentification
- accès dashboard après login
- création première SCI
- création premier bien
- création / consultation bail
- consultation fiche bien
- enregistrement loyer
- génération quittance
- documents: liste / upload / suppression
- pricing visible
- checkout Stripe
- redirections de sécurité

### 7.2 P1 — Cœur métier non bloquant immédiat

- finances consolidées
- associées / invitation / rôles
- fiscalité et création exercice
- exports CSV
- notifications
- onboarding complet
- responsive clé

### 7.3 P2 — Confort / durcissement / excellence

- audit visuel
- dark mode cohérent
- messages de toast
- transitions
- tolérance réseau
- état maintenance / versioning frontend

---

## 8. Jeu de tests de reference — 200 scenarios

**Classement** : P0 (bloquant business) > P1 (coeur metier) > P2 (excellence)
**Axes Big4** : HP = happy path, ERR = erreur fonctionnelle, DROIT = droit/role, VIDE = etat vide/reprise

---

### 8.1 Public / acquisition (20 scenarios)

| # | ID | P | Axe | Cas |
|---|---|---|---|---|
| 1 | PUB-001 | P0 | HP | landing charge sans erreur console |
| 2 | PUB-002 | P0 | HP | CTA hero mene vers pricing/login/register coherent |
| 3 | PUB-003 | P0 | HP | pricing affiche 3 plans avec prix corrects (mensuel) |
| 4 | PUB-004 | P0 | HP | pricing toggle annuel affiche prix reduits |
| 5 | PUB-005 | P0 | HP | checkout invite starter ouvre Stripe si catalogue valide |
| 6 | PUB-006 | P0 | HP | checkout invite fiscal ouvre Stripe si catalogue valide |
| 7 | PUB-007 | P0 | ERR | echec checkout affiche message explicite |
| 8 | PUB-008 | P0 | HP | register cree un compte ou declenche le flux attendu |
| 9 | PUB-009 | P0 | HP | login password fonctionne |
| 10 | PUB-010 | P1 | HP | login magic link fonctionne |
| 11 | PUB-011 | P1 | HP | forgot password affiche confirmation propre |
| 12 | PUB-012 | P1 | HP | simulateur CERFA calcule correctement un cas IR simple |
| 13 | PUB-013 | P1 | HP | simulateur CERFA toggle micro-foncier applique abattement 30% |
| 14 | PUB-014 | P1 | VIDE | simulateur CERFA avec 0 partout affiche 0 |
| 15 | PUB-015 | P1 | HP | footer contient liens CGU, CGV, mentions legales, confidentialite |
| 16 | PUB-016 | P1 | HP | pages legales (CGU, CGV, mentions, confidentialite) chargent |
| 17 | PUB-017 | P2 | HP | dark mode toggle fonctionne sur pages publiques |
| 18 | PUB-018 | P2 | HP | nav publique affiche Tarifs, Simulateur, Connexion, Inscription |
| 19 | PUB-019 | P1 | ERR | register avec email invalide affiche erreur |
| 20 | PUB-020 | P1 | ERR | login avec credentials invalides affiche erreur propre |

### 8.2 Dashboard / navigation (18 scenarios)

| # | ID | P | Axe | Cas |
|---|---|---|---|---|
| 21 | NAV-001 | P0 | DROIT | `/dashboard` redirige vers login si non connecte |
| 22 | NAV-002 | P0 | HP | dashboard connecte charge sans boucle |
| 23 | NAV-003 | P0 | HP | sidebar navigue vers tous les modules principaux |
| 24 | NAV-004 | P0 | HP | dashboard affiche KPIs (SCI actives, biens, recouvrement, cashflow) |
| 25 | NAV-005 | P1 | HP | SCI switcher recharge le bon contexte |
| 26 | NAV-006 | P1 | HP | breadcrumbs n’affichent pas d’UUID brut |
| 27 | NAV-007 | P1 | HP | breadcrumbs affichent les labels accentes correctement |
| 28 | NAV-008 | P1 | HP | notifications s’ouvrent et se marquent lues |
| 29 | NAV-009 | P1 | HP | deconnexion invalide l’acces aux routes protegees |
| 30 | NAV-010 | P1 | VIDE | dashboard sans SCI affiche etat vide avec CTA creer |
| 31 | NAV-011 | P1 | VIDE | dashboard avec SCI sans loyer affiche “Enregistrez un loyer” |
| 32 | NAV-012 | P1 | HP | activite recente affiche les derniers evenements |
| 33 | NAV-013 | P1 | HP | carte SCI affiche nom, statut, nb biens, revenus |
| 34 | NAV-014 | P2 | HP | command palette s’ouvre avec raccourci clavier |
| 35 | NAV-015 | P2 | HP | theme toggle clair/sombre persiste apres navigation |
| 36 | NAV-016 | P1 | DROIT | routes (app)/ redirigent vers login sans session |
| 37 | NAV-017 | P2 | HP | sidebar collapse/expand sur mobile |
| 38 | NAV-018 | P1 | HP | lien “skip to main content” present et fonctionnel |

### 8.3 SCI / gouvernance (22 scenarios)

| # | ID | P | Axe | Cas |
|---|---|---|---|---|
| 39 | SCI-001 | P0 | HP | creer une SCI avec champs obligatoires |
| 40 | SCI-002 | P0 | HP | page overview SCI affiche KPIs (loyer cible, encaisse, cashflow) |
| 41 | SCI-003 | P1 | HP | modifier une SCI (nom, SIREN, siege) |
| 42 | SCI-004 | P1 | HP | supprimer une SCI avec confirmation |
| 43 | SCI-005 | P1 | ERR | creer SCI avec SIREN invalide affiche erreur |
| 44 | SCI-006 | P0 | HP | calendrier fiscal affiche echeances 2044, 2072, TF, CFE, AG |
| 45 | SCI-007 | P1 | HP | afficher la liste des associes |
| 46 | SCI-008 | P1 | HP | ajouter un associe avec email, role, parts |
| 47 | SCI-009 | P1 | HP | inviter un associe par email |
| 48 | SCI-010 | P1 | DROIT | un associe (non-gerant) ne peut pas editer la SCI |
| 49 | SCI-011 | P1 | HP | total des parts = 100% avec alerting si depassement |
| 50 | SCI-012 | P1 | ERR | ajout associe > 100% parts affiche warning |
| 51 | SCI-013 | P2 | HP | mouvements de parts: creation d’une cession |
| 52 | SCI-014 | P2 | HP | mouvements de parts: historique consultable |
| 53 | SCI-015 | P1 | HP | AG: registre lisible (date, type, exercice, quorum) |
| 54 | SCI-016 | P1 | HP | AG: creation avec date, type, exercice, ordre du jour |
| 55 | SCI-017 | P1 | HP | AG: notes de seance et resolutions editables |
| 56 | SCI-018 | P1 | HP | AG: lien de partage PV consultable |
| 57 | SCI-019 | P1 | DROIT | AG: modification/suppression reservees au gerant |
| 58 | SCI-020 | P2 | VIDE | AG: etat vide utile avec CTA “Nouvelle AG” |
| 59 | SCI-021 | P1 | HP | export biens CSV fonctionne |
| 60 | SCI-022 | P1 | HP | export loyers CSV fonctionne |

### 8.4 Biens / exploitation (25 scenarios)

| # | ID | P | Axe | Cas |
|---|---|---|---|---|
| 61 | BIEN-001 | P0 | HP | creer un bien avec adresse, ville, CP, surface |
| 62 | BIEN-002 | P0 | HP | consulter fiche bien (7 onglets visibles) |
| 63 | BIEN-003 | P0 | HP | identite bien affiche adresse, surface, DPE, loyer |
| 64 | BIEN-004 | P1 | HP | modifier identite bien (edition inline) |
| 65 | BIEN-005 | P1 | HP | grille biens affiche prix, rendement, cashflow |
| 66 | BIEN-006 | P1 | HP | toggle grille/liste fonctionne |
| 67 | BIEN-007 | P1 | HP | supprimer un bien avec confirmation |
| 68 | BIEN-008 | P0 | HP | creer un bail (date debut, loyer HC, charges) |
| 69 | BIEN-009 | P0 | HP | modifier un bail existant |
| 70 | BIEN-010 | P1 | HP | historique des baux accessible |
| 71 | BIEN-011 | P1 | HP | rattacher un locataire au bail |
| 72 | BIEN-012 | P1 | HP | detacher un locataire du bail |
| 73 | BIEN-013 | P0 | HP | enregistrer un loyer |
| 74 | BIEN-014 | P1 | HP | marquer un loyer paye |
| 75 | BIEN-015 | P1 | HP | ajouter une charge (type, montant, frequence) |
| 76 | BIEN-016 | P1 | HP | ajouter une assurance PNO |
| 77 | BIEN-017 | P1 | HP | ajouter des frais d’agence |
| 78 | BIEN-018 | P1 | HP | calculs de rentabilite visibles (brute, nette, cashflow) |
| 79 | BIEN-019 | P1 | HP | modales exclusives (1 seule ouverte a la fois) |
| 80 | BIEN-020 | P1 | VIDE | fiche bien sans bail affiche “Aucun bail” |
| 81 | BIEN-021 | P1 | VIDE | fiche bien sans loyer affiche CTA “Enregistrer un loyer” |
| 82 | BIEN-022 | P1 | VIDE | fiche bien sans charge affiche CTA “Ajouter une charge” |
| 83 | BIEN-023 | P1 | VIDE | fiche bien sans PNO affiche “Aucune assurance PNO” |
| 84 | BIEN-024 | P1 | VIDE | fiche bien sans documents affiche CTA “Ajouter” |
| 85 | BIEN-025 | P1 | ERR | rentabilite sans prix d’acquisition affiche message explicatif |

### 8.5 Quittances (10 scenarios)

| # | ID | P | Axe | Cas |
|---|---|---|---|---|
| 86 | QUI-001 | P0 | HP | bouton quittance visible sur fiche bien avec bail actif |
| 87 | QUI-002 | P0 | HP | generation quittance PDF fonctionne |
| 88 | QUI-003 | P0 | HP | quittance PDF contient accents corrects (police TTF) |
| 89 | QUI-004 | P1 | HP | quittance PDF contient adresse bailleur et locataire |
| 90 | QUI-005 | P1 | ERR | message explicite si aucun bail actif |
| 91 | QUI-006 | P1 | ERR | message explicite si aucun locataire rattache |
| 92 | QUI-007 | P1 | ERR | message explicite si aucun loyer paye |
| 93 | QUI-008 | P1 | HP | quittance sur loyer specifique genere le bon mois |
| 94 | QUI-009 | P2 | HP | previsualisation PDF dans l’interface (si setting actif) |
| 95 | QUI-010 | P2 | HP | telechargement direct PDF (si preview desactive) |

### 8.6 Documents (12 scenarios)

| # | ID | P | Axe | Cas |
|---|---|---|---|---|
| 96 | DOC-001 | P0 | HP | liste documents SCI charge |
| 97 | DOC-002 | P0 | HP | upload document fonctionne |
| 98 | DOC-003 | P0 | HP | suppression document fonctionne |
| 99 | DOC-004 | P1 | HP | regroupement par bien |
| 100 | DOC-005 | P1 | VIDE | etat vide utile pour gerant avec CTA “Ajouter” |
| 101 | DOC-006 | P1 | HP | lien document signe valide apres refresh |
| 102 | DOC-007 | P1 | HP | suppression nettoie aussi le storage Supabase |
| 103 | DOC-008 | P1 | ERR | upload fichier trop gros affiche erreur |
| 104 | DOC-009 | P1 | ERR | upload type non autorise affiche erreur |
| 105 | DOC-010 | P2 | HP | document telecharge a le bon nom de fichier |
| 106 | DOC-011 | P2 | HP | documents accessibles depuis fiche bien (onglet Documents) |
| 107 | DOC-012 | P2 | DROIT | associe non-gerant peut consulter mais pas supprimer |

### 8.7 Fiscalite (14 scenarios)

| # | ID | P | Axe | Cas |
|---|---|---|---|---|
| 108 | FISC-001 | P0 | HP | page fiscalite charge sans erreur console |
| 109 | FISC-002 | P0 | DROIT | paywall Pro s’affiche proprement pour user free |
| 110 | FISC-003 | P0 | DROIT | CERFA 2044 interdit pour SCI IS |
| 111 | FISC-004 | P1 | HP | creation exercice fiscal |
| 112 | FISC-005 | P1 | HP | bouton CERFA visible pour SCI IR avec plan Pro |
| 113 | FISC-006 | P1 | HP | generation PDF CERFA fonctionne |
| 114 | FISC-007 | P1 | HP | CERFA PDF contient donnees fiscales correctes |
| 115 | FISC-008 | P1 | ERR | paywall ne genere pas d’erreur 402 en console |
| 116 | FISC-009 | P1 | HP | lien “Voir les offres” mene vers /pricing |
| 117 | FISC-010 | P1 | HP | regime fiscal (IR/IS) affiche correctement |
| 118 | FISC-011 | P2 | HP | exercice fiscal modifiable |
| 119 | FISC-012 | P2 | HP | exercice fiscal supprimable |
| 120 | FISC-013 | P2 | VIDE | etat vide sans exercice affiche CTA |
| 121 | FISC-014 | P2 | HP | calendrier fiscal SCI overview coherent avec regime |

### 8.8 Finances / exports (12 scenarios)

| # | ID | P | Axe | Cas |
|---|---|---|---|---|
| 122 | FIN-001 | P0 | HP | page finances charge sans erreur |
| 123 | FIN-002 | P1 | HP | KPIs affiches: revenus, charges, cashflow, patrimoine |
| 124 | FIN-003 | P1 | HP | filtre 6 mois met a jour les donnees |
| 125 | FIN-004 | P1 | HP | filtre 12 mois met a jour les donnees |
| 126 | FIN-005 | P1 | HP | filtre 24 mois met a jour les donnees |
| 127 | FIN-006 | P1 | HP | repartition par SCI en tableau |
| 128 | FIN-007 | P1 | HP | lien SCI dans tableau mene vers overview SCI |
| 129 | FIN-008 | P1 | HP | export loyers CSV fonctionne |
| 130 | FIN-009 | P1 | HP | export biens CSV fonctionne |
| 131 | FIN-010 | P1 | HP | recouvrement et rentabilite moyenne affiches |
| 132 | FIN-011 | P2 | VIDE | finances sans loyer affiche 0 partout |
| 133 | FIN-012 | P2 | HP | coherence montants finances vs dashboard vs SCI overview |

### 8.9 Paiement / abonnement (16 scenarios)

| # | ID | P | Axe | Cas |
|---|---|---|---|---|
| 134 | PAY-001 | P0 | HP | page pricing affiche catalogue complet |
| 135 | PAY-002 | P0 | HP | checkout invite starter mensuel ouvre Stripe |
| 136 | PAY-003 | P0 | HP | checkout invite fiscal mensuel ouvre Stripe |
| 137 | PAY-004 | P0 | HP | checkout invite starter annuel ouvre Stripe |
| 138 | PAY-005 | P0 | HP | checkout invite fiscal annuel ouvre Stripe |
| 139 | PAY-006 | P0 | HP | checkout connecte fonctionne |
| 140 | PAY-007 | P0 | HP | health readiness bloque prod si catalogue Stripe invalide |
| 141 | PAY-008 | P0 | DROIT | entitlement free limite 1 SCI / 2 biens |
| 142 | PAY-009 | P1 | HP | portail client Stripe accessible pour abonne |
| 143 | PAY-010 | P1 | DROIT | entitlement starter limite SCI / biens correcte |
| 144 | PAY-011 | P1 | DROIT | entitlement fiscal debloque fiscalite et illimite |
| 145 | PAY-012 | P1 | HP | upgrade banner visible quand limite atteinte |
| 146 | PAY-013 | P1 | HP | boutons grise quand plan insuffisant |
| 147 | PAY-014 | P1 | ERR | checkout sans catalogue valide retourne erreur propre |
| 148 | PAY-015 | P2 | HP | settings affiche plan actif (“Essentiel”, “Gestion”, “Fiscal”) |
| 149 | PAY-016 | P2 | HP | settings affiche SCI/biens restants |

### 8.10 Resilience / exploitation (10 scenarios)

| # | ID | P | Axe | Cas |
|---|---|---|---|---|
| 150 | OPS-001 | P0 | HP | banniere offline visible lors perte reseau (texte honnete) |
| 151 | OPS-002 | P0 | HP | banniere ne promet PAS de synchronisation |
| 152 | OPS-003 | P1 | HP | banniere reconnecting visible au retour reseau |
| 153 | OPS-004 | P1 | HP | health/live retourne alive |
| 154 | OPS-005 | P1 | HP | health/ready retourne ready quand tout est ok |
| 155 | OPS-006 | P1 | HP | health/ready retourne 503 quand Stripe KO |
| 156 | OPS-007 | P2 | HP | message maintenance explicite pendant deploiement |
| 157 | OPS-008 | P2 | HP | notification nouvelle version frontend |
| 158 | OPS-009 | P2 | HP | refresh propre apres redeploy |
| 159 | OPS-010 | P2 | HP | rate limiting retourne 429 avec message propre |

### 8.11 Settings / compte (14 scenarios)

| # | ID | P | Axe | Cas |
|---|---|---|---|---|
| 160 | SET-001 | P1 | HP | page settings charge sans erreur |
| 161 | SET-002 | P1 | HP | tous les textes ont des accents francais corrects |
| 162 | SET-003 | P1 | HP | dropdown page d’ouverture contient uniquement des routes valides |
| 163 | SET-004 | P1 | HP | changement densite persiste apres navigation |
| 164 | SET-005 | P1 | HP | toggle previsualisation PDF fonctionne |
| 165 | SET-006 | P1 | HP | toggle digest email fonctionne |
| 166 | SET-007 | P1 | HP | toggle alertes de risque fonctionne |
| 167 | SET-008 | P1 | HP | bouton “Enregistrer les parametres” sauvegarde |
| 168 | SET-009 | P1 | HP | notifications: 7 types avec toggles email/in-app |
| 169 | SET-010 | P1 | HP | notifications: sauvegarde des preferences |
| 170 | SET-011 | P1 | HP | lien vers /account fonctionne |
| 171 | SET-012 | P1 | HP | lien vers /account/privacy fonctionne |
| 172 | SET-013 | P2 | HP | panneau lateral affiche resume config active |
| 173 | SET-014 | P2 | HP | capacite active affiche plan et limites |

### 8.12 Onboarding (10 scenarios)

| # | ID | P | Axe | Cas |
|---|---|---|---|---|
| 174 | ONB-001 | P0 | HP | wizard onboarding charge pour nouveau user |
| 175 | ONB-002 | P0 | HP | etape 1: creation SCI |
| 176 | ONB-003 | P0 | HP | etape 2: ajout bien |
| 177 | ONB-004 | P1 | HP | etape 3: creation bail |
| 178 | ONB-005 | P1 | HP | etape 4: configuration notifications |
| 179 | ONB-006 | P1 | HP | progression sauvegardee entre etapes |
| 180 | ONB-007 | P1 | HP | redirect depuis dashboard si onboarding non complete |
| 181 | ONB-008 | P1 | ERR | onboarding avec champs invalides affiche erreurs |
| 182 | ONB-009 | P2 | HP | skip onboarding possible |
| 183 | ONB-010 | P2 | HP | reprendre onboarding interrompu |

### 8.13 Admin (8 scenarios)

| # | ID | P | Axe | Cas |
|---|---|---|---|---|
| 184 | ADM-001 | P1 | DROIT | /admin sans secret key redirige ou refuse |
| 185 | ADM-002 | P1 | HP | /admin?secret=KEY charge le dashboard admin |
| 186 | ADM-003 | P1 | HP | KPIs admin: users, SCI, biens, abonnes |
| 187 | ADM-004 | P1 | HP | funnel conversion visible |
| 188 | ADM-005 | P1 | HP | alertes admin (health, erreurs recentes) |
| 189 | ADM-006 | P1 | HP | actions utilisateur (details user) |
| 190 | ADM-007 | P2 | DROIT | admin non accessible depuis sidebar app |
| 191 | ADM-008 | P2 | HP | admin fonctionne hors du route group (app) |

### 8.14 Import / Export CSV (8 scenarios)

| # | ID | P | Axe | Cas |
|---|---|---|---|---|
| 192 | CSV-001 | P1 | HP | import CSV biens avec template valide |
| 193 | CSV-002 | P1 | ERR | import CSV avec colonnes manquantes affiche erreur |
| 194 | CSV-003 | P1 | ERR | import CSV avec donnees invalides affiche erreurs par ligne |
| 195 | CSV-004 | P1 | HP | export biens CSV contient toutes les colonnes |
| 196 | CSV-005 | P1 | HP | export loyers CSV contient toutes les colonnes |
| 197 | CSV-006 | P2 | HP | CSV exporte encodage UTF-8 avec accents |
| 198 | CSV-007 | P2 | HP | import CSV loyers avec template valide |
| 199 | CSV-008 | P2 | VIDE | import CSV sur SCI sans bien existant cree les biens |

### 8.15 Securite / RGPD (8 scenarios)

| # | ID | P | Axe | Cas |
|---|---|---|---|---|
| 200 | SEC-001 | P0 | DROIT | RLS empeche acces aux donnees d’un autre user |
| 201 | SEC-002 | P0 | DROIT | JWT expire retourne 401 |
| 202 | SEC-003 | P0 | DROIT | API sans token retourne 401 |
| 203 | SEC-004 | P1 | HP | page confidentialite accessible |
| 204 | SEC-005 | P1 | HP | export RGPD (donnees personnelles) |
| 205 | SEC-006 | P1 | HP | suppression compte RGPD |
| 206 | SEC-007 | P1 | HP | cookie consent banner affichee au premier acces |
| 207 | SEC-008 | P2 | HP | rate limiting actif sur endpoints sensibles (login, register) |

---

## 9. Statistiques du jeu de tests

### 9.1 Repartition par criticite

| Criticite | Nombre | % | Cible automatisation |
|---|---|---|---|
| P0 | 48 | 23% | 100% |
| P1 | 117 | 56% | >= 90% |
| P2 | 42 | 20% | >= 50% |
| **Total** | **207** | | |

### 9.2 Repartition par axe Big4

| Axe | Nombre | % |
|---|---|---|
| HP (happy path) | 152 | 73% |
| ERR (erreur) | 22 | 11% |
| DROIT (role/acces) | 18 | 9% |
| VIDE (etat vide) | 15 | 7% |

### 9.3 Repartition par domaine

| Domaine | Scenarios | P0 | P1 | P2 |
|---|---|---|---|---|
| Public / acquisition | 20 | 8 | 9 | 3 |
| Dashboard / navigation | 18 | 4 | 10 | 4 |
| SCI / gouvernance | 22 | 2 | 15 | 5 |
| Biens / exploitation | 25 | 5 | 17 | 3 |
| Quittances | 10 | 3 | 5 | 2 |
| Documents | 12 | 3 | 6 | 3 |
| Fiscalite | 14 | 3 | 7 | 4 |
| Finances / exports | 12 | 1 | 8 | 3 |
| Paiement / abonnement | 16 | 8 | 5 | 3 |
| Resilience / exploitation | 10 | 2 | 4 | 4 |
| Settings / compte | 14 | 0 | 11 | 3 |
| Onboarding | 10 | 2 | 5 | 3 |
| Admin | 8 | 0 | 5 | 3 |
| Import / Export CSV | 8 | 0 | 4 | 4 |
| Securite / RGPD | 8 | 3 | 4 | 1 |

---

## 10. Cartographie de l’automatisation actuelle

### 10.1 Deja automatise (E2E Playwright)

| Fichier spec | Domaines couverts |
|---|---|
| auth.spec.ts | PUB-008..010, NAV-001 |
| dashboard.spec.ts | NAV-002..004, NAV-010..013 |
| navigation.spec.ts | NAV-003, NAV-006..007 |
| landing.spec.ts | PUB-001..002, PUB-015..016 |
| sci-management.spec.ts | SCI-001..004 |
| bien-management.spec.ts | BIEN-001..019 |
| documents.spec.ts | DOC-001..005 |
| quittances.spec.ts | QUI-001..007 |
| fiscalite.spec.ts | FISC-001..006 |
| finances.spec.ts | FIN-001..008 |
| paywall.spec.ts | PAY-008..013 |
| onboarding.spec.ts | ONB-001..007 |
| settings-account.spec.ts | SET-001..014 |
| notifications.spec.ts | NAV-008, SET-009..010 |
| billing-audit.spec.ts | PAY-001..007 |
| assemblees-generales.spec.ts | SCI-015..020 |
| smoke-public.spec.ts | PUB-001, PUB-003, PUB-005, OPS-004..005 |
| smoke-auth.spec.ts | NAV-002, BIEN-002, FISC-001, DOC-001 |

### 10.2 Partiellement couvert

- checkout reel live (PAY-002..006)
- customer portal Stripe (PAY-009)
- magic link email reel (PUB-010)
- RGPD execution reelle (SEC-005..006)
- import CSV bout en bout (CSV-001..003, CSV-007)
- admin complet (ADM-001..008)
- mouvements de parts (SCI-013..014)
- comportement perte reseau reelle (OPS-001..003)

### 10.3 Non couvert

- smoke tests prod authentifies automatises post-deploy
- compatibilite frontend/backend pendant rolling deploy
- rollback validation
- rate limiting E2E (SEC-008, OPS-010)

---

## 11. Strategie d’execution

### 11.1 A chaque push (CI quality-gate)

- `backend pytest` (1201 tests, 92% coverage)
- `frontend check` (0 erreurs, 0 warnings)
- `frontend test:unit` + `test:high-value` (>=90% coverage)
- `Playwright validation mockee` (67+ tests)

### 11.2 A chaque deploiement (post-deploy smoke)

| Suite | Scenarios couverts | Auth requise |
|---|---|---|
| smoke-prod-public | PUB-001,003,005, OPS-004..006 | Non |
| smoke-prod-auth | NAV-002, BIEN-002, DOC-001, FISC-001, FIN-001 | Oui (E2E_AUTH_TOKEN) |
| smoke-prod-billing | PAY-001..007, PAY-014 | Non |

### 11.3 Go / No-Go post-deploy

Le deploiement est marque en echec si un seul de ces cas echoue:

- `health/ready` retourne 503
- login impossible
- dashboard inaccessible
- fiche bien KO
- checkout Stripe KO
- documents KO

---

## 12. Findings resolus dans cette session (21 mars 2026)

| ID | Severite | Finding | Correction |
|---|---|---|---|
| F-001 | P0 | docker-compose.yml manque 4 env vars Stripe (annual + cabinet) | docker-compose.yml mis a jour |
| F-002 | P2 | Fiscalite: erreur console 402 | Deja resolu (paywall frontend check avant appel API) |
| F-003 | P1 | Banniere offline promet sync inexistante | Texte corrige: “certaines fonctionnalites sont indisponibles” |
| F-004 | P1 | AG: accents manquants dans breadcrumbs | labelMap mis a jour (AppBreadcrumbs + AppNavbar) |
| F-005 | P1 | AG: absente de la sidebar | Deja present dans le code (non deploye) |
| F-006 | P1 | Settings: 30+ occurrences sans accents | Tous corriges dans settings/+page.svelte |
| F-007 | P2 | Settings: routes dropdown invalides (/exploitation, /finance) | Routes corrigees dans application-preferences.ts |

---

## 13. Recommandation executive

### Priorite immediate (avant prochain deploy)

1. Deployer les corrections accents + banniere offline + docker-compose
2. Configurer les 6 STRIPE_*_PRICE_ID dans .env.production sur le VPS
3. Verifier health/ready retourne 200 apres deploy
4. Valider checkout Stripe end-to-end sur prod

### Cible qualite Big4

| Metrique | Cible | Actuel |
|---|---|---|
| P0 automatises | 100% | ~85% |
| P1 automatises | >= 90% | ~75% |
| P0 verts post-deploy | 100% | NON (Stripe 503) |
| Erreurs console parcours coeur | 0 | 0 (corrige) |
| Endpoints critiques prod ready | 100% | NON (health/ready 503) |

### Vision “sous controle”

GererSCI sera considere “sous controle Big4” quand:

- 207 scenarios documentes, >= 180 automatises
- 0 P0 rouge apres deploiement
- smoke-prod-public + smoke-prod-auth verts en CI post-deploy
- audit visuel automatise (screenshots de reference) sur release candidate
- recette metier humaine validee par 3 utilisateurs pilotes

---

## 14. References

- [2026-03-12-cahier-de-recette.md](../docs/2026-03-12-cahier-de-recette.md)
- [2026-03-11-full-audit-report.md](../docs/2026-03-11-full-audit-report.md)
- [2026-03-13-audit-expert-panel.md](../docs/2026-03-13-audit-expert-panel.md)
- [quality-gate.yml](../.github/workflows/quality-gate.yml)
- [deploy.yml](../.github/workflows/deploy.yml)
