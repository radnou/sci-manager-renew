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

## 8. Jeu de tests de référence

## 8.1 Public / acquisition

| ID | Criticité | Cas |
|---|---|---|
| PUB-001 | P0 | landing charge sans erreur |
| PUB-002 | P0 | CTA hero mène vers pricing/login/register cohérent |
| PUB-003 | P1 | simulateur CERFA calcule correctement un cas IR simple |
| PUB-004 | P0 | register crée un compte ou déclenche le flux attendu |
| PUB-005 | P0 | login password fonctionne |
| PUB-006 | P1 | login magic link fonctionne |
| PUB-007 | P1 | forgot password affiche confirmation propre |
| PUB-008 | P0 | pricing affiche les 3 plans et les prix corrects |
| PUB-009 | P0 | échec checkout affiche un message explicite |
| PUB-010 | P0 | checkout invité ouvre Stripe si catalogue valide |

## 8.2 Dashboard / navigation

| ID | Criticité | Cas |
|---|---|---|
| NAV-001 | P0 | `/dashboard` protégé redirige vers login si non connecté |
| NAV-002 | P0 | dashboard connecté charge sans boucle |
| NAV-003 | P0 | sidebar navigue vers tous les modules principaux |
| NAV-004 | P1 | SCI switcher recharge le bon contexte |
| NAV-005 | P1 | breadcrumbs n’affichent pas d’UUID brut |
| NAV-006 | P1 | notifications s’ouvrent et se marquent lues |
| NAV-007 | P1 | déconnexion invalide l’accès aux routes protégées |

## 8.3 SCI / gouvernance

| ID | Criticité | Cas |
|---|---|---|
| SCI-001 | P0 | créer une SCI |
| SCI-002 | P1 | modifier une SCI |
| SCI-003 | P1 | supprimer une SCI avec confirmation |
| SCI-004 | P1 | afficher la liste des associés |
| SCI-005 | P1 | inviter un associé |
| SCI-006 | P1 | contrôle de rôle: un associé ne peut pas éditer |
| SCI-007 | P1 | total des parts = 100% avec alerting cohérent |
| SCI-008 | P2 | mouvements de parts |
| SCI-009 | P2 | assemblées générales |

## 8.4 Bien / exploitation

| ID | Criticité | Cas |
|---|---|---|
| BIEN-001 | P0 | créer un bien |
| BIEN-002 | P0 | consulter fiche bien |
| BIEN-003 | P0 | créer / modifier bail |
| BIEN-004 | P1 | rattacher / détacher locataire |
| BIEN-005 | P0 | enregistrer un loyer |
| BIEN-006 | P1 | marquer un loyer payé |
| BIEN-007 | P1 | ajouter une charge |
| BIEN-008 | P1 | ajouter une PNO |
| BIEN-009 | P1 | ajouter des frais d’agence |
| BIEN-010 | P1 | calculs de rentabilité visibles |
| BIEN-011 | P1 | modales exclusives ou pattern de remplacement stable |

## 8.5 Quittances

| ID | Criticité | Cas |
|---|---|---|
| QUI-001 | P0 | bouton quittance visible sur loyer payé |
| QUI-002 | P0 | génération quittance fonctionne |
| QUI-003 | P1 | message explicite si aucun bail actif |
| QUI-004 | P1 | message explicite si aucun locataire |
| QUI-005 | P1 | message explicite si aucun loyer payé |

## 8.6 Documents

| ID | Criticité | Cas |
|---|---|---|
| DOC-001 | P0 | liste documents SCI charge |
| DOC-002 | P1 | regroupement par bien |
| DOC-003 | P1 | état vide utile pour gérant |
| DOC-004 | P0 | upload document |
| DOC-005 | P0 | suppression document |
| DOC-006 | P1 | lien document signé encore valide après refresh liste |
| DOC-007 | P1 | suppression nettoie aussi le storage |

## 8.7 Fiscalité

| ID | Criticité | Cas |
|---|---|---|
| FISC-001 | P1 | page fiscalité charge |
| FISC-002 | P1 | création exercice |
| FISC-003 | P1 | bouton CERFA visible pour SCI IR |
| FISC-004 | P0 | CERFA 2044 interdit pour SCI IS |
| FISC-005 | P1 | génération PDF CERFA fonctionne quand autorisée |
| FISC-006 | P1 | paywall Pro propre sans erreur console |

## 8.8 Finances / exports

| ID | Criticité | Cas |
|---|---|---|
| FIN-001 | P0 | page finances charge |
| FIN-002 | P1 | filtre période met à jour les données |
| FIN-003 | P1 | répartition par SCI cohérente |
| FIN-004 | P1 | export loyers CSV |
| FIN-005 | P1 | export biens CSV |

## 8.9 Paiement / abonnement

| ID | Criticité | Cas |
|---|---|---|
| PAY-001 | P0 | page pricing affiche catalogue |
| PAY-002 | P0 | checkout invité starter fonctionne |
| PAY-003 | P0 | checkout invité pro fonctionne |
| PAY-004 | P0 | checkout connecté fonctionne |
| PAY-005 | P1 | portail client Stripe accessible pour abonné |
| PAY-006 | P0 | entitlement free limite 1 SCI |
| PAY-007 | P1 | entitlement starter limite SCI / biens correcte |
| PAY-008 | P1 | entitlement pro débloque fiscalité / associés / documents |
| PAY-009 | P0 | health readiness bloque la prod si catalogue Stripe invalide |

## 8.10 Résilience / exploitation

| ID | Criticité | Cas |
|---|---|---|
| OPS-001 | P1 | bannière offline visible lors perte réseau |
| OPS-002 | P1 | bannière reconnecting visible au retour réseau |
| OPS-003 | P0 | ne pas promettre une synchronisation si aucune queue offline n’existe |
| OPS-004 | P1 | health/live et health/ready cohérents |
| OPS-005 | P2 | message maintenance explicite pendant déploiement |
| OPS-006 | P2 | notification de nouvelle version frontend |
| OPS-007 | P2 | refresh propre après redeploy backend/front |

---

## 9. Cartographie de l’automatisation actuelle

### 9.1 Déjà automatisé

Références existantes:

- [auth.spec.ts](/Users/radnoumanemossabely/Code/sci-manager-renew/frontend/e2e/validation/auth.spec.ts)
- [dashboard.spec.ts](/Users/radnoumanemossabely/Code/sci-manager-renew/frontend/e2e/validation/dashboard.spec.ts)
- [navigation.spec.ts](/Users/radnoumanemossabely/Code/sci-manager-renew/frontend/e2e/validation/navigation.spec.ts)
- [sci-management.spec.ts](/Users/radnoumanemossabely/Code/sci-manager-renew/frontend/e2e/validation/sci-management.spec.ts)
- [bien-management.spec.ts](/Users/radnoumanemossabely/Code/sci-manager-renew/frontend/e2e/validation/bien-management.spec.ts)
- [documents.spec.ts](/Users/radnoumanemossabely/Code/sci-manager-renew/frontend/e2e/validation/documents.spec.ts)
- [quittances.spec.ts](/Users/radnoumanemossabely/Code/sci-manager-renew/frontend/e2e/validation/quittances.spec.ts)
- [fiscalite.spec.ts](/Users/radnoumanemossabely/Code/sci-manager-renew/frontend/e2e/validation/fiscalite.spec.ts)
- [finances.spec.ts](/Users/radnoumanemossabely/Code/sci-manager-renew/frontend/e2e/validation/finances.spec.ts)
- [paywall.spec.ts](/Users/radnoumanemossabely/Code/sci-manager-renew/frontend/e2e/validation/paywall.spec.ts)
- [onboarding.spec.ts](/Users/radnoumanemossabely/Code/sci-manager-renew/frontend/e2e/validation/onboarding.spec.ts)
- [settings-account.spec.ts](/Users/radnoumanemossabely/Code/sci-manager-renew/frontend/e2e/validation/settings-account.spec.ts)
- [notifications.spec.ts](/Users/radnoumanemossabely/Code/sci-manager-renew/frontend/e2e/validation/notifications.spec.ts)

### 9.2 Partiellement couvert

- checkout réel live
- customer portal Stripe
- magie du lien email réel
- RGPD exécution réelle
- import CSV bout en bout
- admin complet
- assemblées générales
- mouvements de parts
- comportement en panne réseau réelle

### 9.3 Non couvert à un niveau satisfaisant

- smoke tests prod authentifiés automatisés après déploiement
- tests de compatibilité frontend/backend pendant rolling deploy
- vraie recette offline / resync
- rollback validation

---

## 10. Stratégie d’exécution automatique

## 10.1 À chaque push

- `backend pytest`
- `frontend unit`
- `frontend build`
- `Playwright validation mockée`

Déjà en grande partie porté par:

- [quality-gate.yml](/Users/radnoumanemossabely/Code/sci-manager-renew/.github/workflows/quality-gate.yml)

## 10.2 À chaque déploiement

Ajouter un vrai `post-deploy smoke` automatisé:

- compte de recette dédié
- SCI seedée dédiée
- bien seedé dédié
- cas `checkout`, `dashboard`, `documents`, `fiche bien`, `fiscalité`, `finances`

### Suite recommandée

- `smoke-prod-public`
- `smoke-prod-auth`
- `smoke-prod-billing`
- `smoke-prod-resilience`

### Go / No-Go post-deploy

Le déploiement doit être marqué en échec si un seul des cas suivants échoue:

- login impossible
- dashboard inaccessible
- documents KO
- fiche bien KO
- quittance KO
- checkout KO
- readiness `not_ready`

---

## 11. Ce qui doit changer côté offline / déploiement

### 11.1 Ce qu’il faut éviter

Ne pas garder une bannière qui promet une synchronisation réelle alors qu’il n’y a pas:

- de file de mutations locale
- de retry orchestré
- d’idempotence frontend
- de reprise après conflit

### 11.2 Ce qu’il faut mettre en place si la promesse produit reste

Minimum crédible:

1. service worker ou couche offline explicite
2. queue locale des mutations
3. reprise idempotente à la reconnexion
4. toast “X modifications synchronisées”
5. état “lecture seule / maintenance” pendant déploiement
6. détection de version frontend/back incompatibles
7. refresh forcé ou reload assisté après déploiement

### 11.3 Variante plus pragmatique

Si vous ne voulez pas construire une vraie sync offline maintenant:

- garder la bannière `Connexion perdue`
- supprimer la phrase `vos modifications seront synchronisées au retour`
- passer temporairement l’app en lecture seule quand l’API devient indisponible
- afficher un message clair de maintenance / reconnexion

Cette variante est plus honnête et beaucoup moins risquée.

---

## 12. Recommandation exécutive

### Priorité immédiate

1. corriger Stripe prod
2. nettoyer le paywall fiscalité pour supprimer le `402` visible en console
3. transformer ce document en matrice de suivi vivante
4. brancher un `smoke-prod` automatique après déploiement
5. corriger la promesse offline trompeuse

### Cible qualité

Avant de considérer GererSCI “sous contrôle”, il faut viser:

- `100%` des `P0` automatisés
- `>= 90%` des `P1` automatisés
- `100%` des `P0` verts en post-déploiement
- `0` erreur console sur parcours cœur
- `0` endpoint critique prod en `not_ready`

---

## 13. Références

- [2026-03-12-cahier-de-recette.md](/Users/radnoumanemossabely/Code/sci-manager-renew/docs/2026-03-12-cahier-de-recette.md)
- [2026-03-11-full-audit-report.md](/Users/radnoumanemossabely/Code/sci-manager-renew/docs/2026-03-11-full-audit-report.md)
- [2026-03-13-audit-expert-panel.md](/Users/radnoumanemossabely/Code/sci-manager-renew/docs/2026-03-13-audit-expert-panel.md)
- [quality-gate.yml](/Users/radnoumanemossabely/Code/sci-manager-renew/.github/workflows/quality-gate.yml)
- [deploy.yml](/Users/radnoumanemossabely/Code/sci-manager-renew/.github/workflows/deploy.yml)
