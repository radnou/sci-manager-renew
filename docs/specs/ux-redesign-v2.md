# GererSCI — Spec UX Redesign V2

> Date: 2026-03-10
> Statut: VALIDÉ (brainstorm)
> Prochaine étape: /sc:design (architecture) ou /sc:workflow (implémentation)

---

## 1. Principes directeurs

1. **Paywall obligatoire** : pas d'accès à l'app sans abonnement actif, zéro trial
2. **Navigation top-down** : SCI → Biens → Fiche Bien (tout dans l'URL, bookmarkable)
3. **Dashboard compartimenté** : 4 blocs distincts, pas de tabs, pas de surcharge
4. **Fiche Bien = coeur opérationnel** : bail, locataire, charges, assurance PNO, frais agence, documents
5. **Associés = utilisateurs** : accès lecture seule aux SCI dont ils sont membres
6. **Onboarding progressif** : découverte guidée à la 1ère connexion
7. **Notifications configurables** : in-app + email (opt-in, configurable dans paramètres et onboarding)

---

## 2. Flow d'accès

```
Visiteur
  → / (landing page)
  → /pricing (choix forfait obligatoire)
  → Stripe checkout
  → Email magic link (inscription + paiement liés)
  → 1ère connexion

1ère connexion (onboarding obligatoire, non-skippable) :
  Step 1: Créer ta 1ère SCI (nom, SIREN, régime fiscal)
  Step 2: Ajouter ton 1er bien (adresse, type, loyer, surface)
  Step 3: Configurer le bail + locataire
  Step 4: Préférences notifications (email alertes: oui/non)
  Step 5: Tour guidé rapide de l'interface
  → Accès complet

Connexions suivantes :
  → /dashboard (alertes + KPIs + SCI cards)

Utilisateur sans abonnement actif :
  → Redirigé vers /pricing (middleware layout)

Associé invité :
  → Magic link → Onboarding allégé (pas de création SCI)
  → Accès lecture seule
```

### Règles d'accès

- `/login` n'existe plus en accès direct libre — l'inscription passe par `/pricing` → Stripe
- `/login` reste accessible pour les utilisateurs existants (reconnexion)
- Middleware dans le layout : vérifie abonnement actif + onboarding complété
- Flag `onboarding_completed` en base (table `subscriptions` ou nouvelle colonne)

---

## 3. Navigation restructurée

### Sidebar

```
Logo GererSCI
─────────────────────
📊 Tableau de bord           /dashboard
─────────────────────
🏢 Mes SCI                   /scis
   └─ [SCI active]           /scis/:sciId
      ├─ Vue d'ensemble      /scis/:sciId
      ├─ Biens               /scis/:sciId/biens
      ├─ Associés            /scis/:sciId/associes
      ├─ Fiscalité           /scis/:sciId/fiscalite
      └─ Documents           /scis/:sciId/documents
─────────────────────
💰 Finances                  /finances
─────────────────────
⚙️ Paramètres               /settings
👤 Compte                    /account
```

### Routage complet

```
/                                    → Landing page (public)
/pricing                             → Choix forfait (public)
/login                               → Reconnexion (public)
/auth/callback                       → Callback Supabase
/success                             → Confirmation paiement

/onboarding                          → Wizard 1ère connexion (protégé)
/dashboard                           → Tableau de bord global (protégé)

/scis                                → Liste des SCI
/scis/:sciId                         → Vue d'ensemble SCI
/scis/:sciId/biens                   → Biens de la SCI
/scis/:sciId/biens/:bienId           → Fiche Bien complète
/scis/:sciId/biens/:bienId/baux      → Historique des baux du bien
/scis/:sciId/associes                → Associés de la SCI
/scis/:sciId/fiscalite               → Exercices fiscaux
/scis/:sciId/documents               → Documents SCI

/finances                            → Vue financière transversale

/settings                            → Paramètres (notifications, interface)
/account                             → Compte & abonnement
/account/privacy                     → RGPD
/admin                               → Panel admin (admin only)
```

---

## 4. Dashboard — 4 blocs compartimentés

### Bloc 1 — Alertes & Actions urgentes (haut, pleine largeur)

Cards d'alerte avec icône, texte, et bouton d'action :
- 🔴 Loyers en retard : "{n} loyers en retard ({montant}€)" → "Voir détails"
- 🟡 Baux expirant < 90j : "{n} baux arrivent à échéance" → "Voir les baux"
- 🔵 Quittances du mois non générées : "{n} quittances à générer" → "Générer"
- Vide si aucune alerte → message positif "Tout est en ordre"

### Bloc 2 — KPIs Portfolio (ligne de 4 cards)

| KPI | Calcul |
|-----|--------|
| SCI actives | COUNT(sci via associes) |
| Biens totaux | COUNT(biens) |
| Taux recouvrement | loyers payés / loyers attendus × 100 |
| Cashflow net mensuel | SUM(loyers payés) - SUM(charges) du mois |

### Bloc 3 — Mes SCI (grille de cards cliquables)

Card par SCI :
- Nom + statut badge
- {n} biens | {loyer_total}€/mois
- Taux recouvrement (mini bar)
- Clic → `/scis/:sciId`

### Bloc 4 — Activité récente (timeline, 10 items max)

- "Loyer de 850€ enregistré pour [bien]" — il y a 2h
- "Quittance générée pour [locataire]" — hier
- "Nouveau bien ajouté: [adresse]" — 3 mars
- Icônes par type d'événement

---

## 5. Fiche Bien — `/scis/:sciId/biens/:bienId`

Page complète en sections avec ancres. Layout : header fixe + sections scrollables.

### Header

- Breadcrumb : Mes SCI > [SCI nom] > Biens > [Adresse du bien]
- Titre : adresse complète
- Badges : type locatif, DPE, statut bail
- Actions : Modifier, Supprimer, Générer quittance

### Section A — Identité du bien

| Champ | Type | Existant ? |
|-------|------|-----------|
| Adresse | text | ✅ |
| Ville | text | ✅ |
| Code postal | text (5 digits) | ✅ |
| Type locatif | enum: nu, meublé, mixte | ✅ |
| Date acquisition | date | ✅ |
| Prix acquisition | numeric | ✅ |
| Surface (m²) | numeric | ❌ nouveau |
| Nombre de pièces | integer | ❌ nouveau |
| DPE (classe) | enum: A-G | ❌ nouveau |
| Photo | URL (upload Supabase Storage) | ❌ nouveau |

### Section B — Bail actif + Historique

**Bail actif** (card principale, mise en avant) :
| Champ | Type | Nouveau ? |
|-------|------|-----------|
| Locataire(s) | FK locataires (1 ou N pour colocation) | ✅ enrichi |
| Date début | date | ✅ (sur locataire → migré vers bail) |
| Date fin | date, nullable | ✅ idem |
| Loyer HC | numeric | ❌ nouveau |
| Charges locatives | numeric | ❌ nouveau |
| Dépôt de garantie | numeric | ❌ nouveau |
| Indice IRL de référence | text | ❌ nouveau |
| Date de révision | date | ❌ nouveau |
| État des lieux entrée | date | ❌ nouveau |
| État des lieux sortie | date, nullable | ❌ nouveau |
| Statut | enum: en_cours, expiré, résilié | ❌ nouveau |
| Document bail (PDF) | URL upload | ❌ nouveau |

**Historique des baux** : liste des baux passés avec locataires, dates, montants.
- Accessible via sous-page `/scis/:sciId/biens/:bienId/baux`

**Colocation** : un bail peut référencer N locataires.
- Table de jointure `bail_locataires` (id_bail, id_locataire)

### Section C — Loyers (de ce bien uniquement)

- Tableau : mois, montant, statut, locataire, quittance générée
- Actions inline : marquer payé, générer quittance, modifier
- Bouton "Enregistrer un loyer"
- Filtre par période (date range picker)
- Pagination si > 12 mois

### Section D — Charges & Frais

**Sous-section D1 — Charges récurrentes & ponctuelles**
- Tableau existant (type_charge, montant, date_paiement)
- Catégories prédéfinies : taxe foncière, copropriété, entretien, travaux, divers

**Sous-section D2 — Assurance PNO** (nouvelle table)
| Champ | Type |
|-------|------|
| Compagnie | text |
| N° contrat | text, nullable |
| Montant annuel | numeric |
| Date échéance | date |

**Sous-section D3 — Frais d'agence** (nouvelle table)
| Champ | Type |
|-------|------|
| Nom agence | text |
| Contact | text, nullable |
| Type | enum: pourcentage, fixe |
| Montant ou % | numeric |

### Section E — Rentabilité (calculée, lecture seule)

| Indicateur | Formule |
|-----------|---------|
| Rentabilité brute | (loyer_annuel / prix_acquisition) × 100 |
| Rentabilité nette | (loyer_annuel - charges_annuelles - assurance_pno - frais_agence) / prix_acquisition × 100 |
| Cashflow mensuel | loyer_cc - charges_mensuelles - (assurance_pno / 12) - frais_agence_mensuel |
| Cashflow annuel | cashflow_mensuel × 12 |

### Section F — Documents du bien

- Upload multi-fichiers vers Supabase Storage
- Catégories : bail, diagnostics (DPE, amiante, plomb, électricité, gaz), état des lieux, quittances, photos, autres
- Affichage en grille avec miniature + nom + date
- Téléchargement / suppression

---

## 6. Vue Finances — `/finances`

Vue transversale multi-SCI.

### Agrégats prioritaires

| Indicateur | Périmètre |
|-----------|-----------|
| Revenus locatifs mensuels | SUM loyers payés du mois, toutes SCI |
| Charges mensuelles | SUM charges du mois, toutes SCI |
| Cashflow net mensuel | Revenus - Charges |
| Taux recouvrement global | Payés / (Payés + Retard + Attente) × 100 |
| Loyers en retard (montant) | SUM montant des loyers en_retard |
| Patrimoine total | SUM prix_acquisition tous biens |
| Rentabilité moyenne | Moyenne pondérée des rentabilités nettes |

### Visualisations

- Graphique évolution revenus/charges sur 12 mois (bar chart)
- Répartition revenus par SCI (donut chart)
- Tableau récapitulatif par SCI (nom, revenus, charges, cashflow, recouvrement)

---

## 7. Accès Associés — Matrice de permissions

| Fonctionnalité | Gérant | Associé |
|---|---|---|
| Dashboard (lecture) | ✅ | ✅ |
| Voir biens | ✅ | ✅ |
| Ajouter/modifier/supprimer bien | ✅ | ❌ |
| Voir fiche bien (bail, charges, etc.) | ✅ | ✅ |
| Voir loyers | ✅ | ✅ |
| Enregistrer/modifier loyer | ✅ | ❌ |
| Générer quittance | ✅ | ❌ |
| Voir charges | ✅ | ✅ |
| Ajouter/modifier charge | ✅ | ❌ |
| Voir associés | ✅ | ✅ |
| Inviter/supprimer associé | ✅ | ❌ |
| Fiscalité (lecture) | ✅ | ✅ |
| Fiscalité (modification) | ✅ | ❌ |
| Documents (lecture/téléchargement) | ✅ | ✅ |
| Documents (upload/suppression) | ✅ | ❌ |
| Finances transversales | ✅ | ✅ (ses SCI) |
| Paramètres compte | ✅ | ✅ (les siens) |
| Inviter associé | ✅ | ❌ |

### Implémentation

- Rôle stocké dans `associes.role` : `gerant` | `associe`
- Backend : vérifier le rôle avant toute mutation (POST/PATCH/DELETE)
- Frontend : masquer les boutons d'action si role === 'associe'
- RLS Supabase : policies différenciées SELECT (tous) vs INSERT/UPDATE/DELETE (gérant only)

---

## 8. Notifications — Configurables

### Types de notifications

| Type | In-app | Email (opt-in) |
|------|--------|---------------|
| Loyer en retard (> 5 jours) | ✅ | ✅ |
| Bail expirant (< 90 jours) | ✅ | ✅ |
| Quittance du mois à générer | ✅ | ✅ |
| Assurance PNO échéance (< 30j) | ✅ | ✅ |
| Nouveau loyer enregistré | ✅ | ❌ |
| Nouvel associé ajouté | ✅ | ✅ |
| Abonnement expirant | ✅ | ✅ |

### Configuration

- **Onboarding step 4** : "Souhaitez-vous recevoir des alertes par email ?" (toggle global)
- **Paramètres > Notifications** : toggle par type de notification
- Stockage : table `notification_preferences` (user_id, type, email_enabled, in_app_enabled)

---

## 9. Modèle de données — Changements requis

### Colonnes à ajouter

**Table `biens`** :
```sql
ALTER TABLE biens ADD COLUMN surface_m2 NUMERIC;
ALTER TABLE biens ADD COLUMN nb_pieces INTEGER;
ALTER TABLE biens ADD COLUMN dpe_classe TEXT CHECK (dpe_classe IN ('A','B','C','D','E','F','G'));
ALTER TABLE biens ADD COLUMN photo_url TEXT;
```

**Table `locataires`** :
```sql
ALTER TABLE locataires ADD COLUMN telephone TEXT;
```

**Table `subscriptions`** :
```sql
ALTER TABLE subscriptions ADD COLUMN onboarding_completed BOOLEAN DEFAULT FALSE;
```

### Nouvelles tables

```sql
-- Baux (remplace le lien direct locataire-bien pour les dates)
CREATE TABLE baux (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  id_bien UUID NOT NULL REFERENCES biens(id) ON DELETE CASCADE,
  date_debut DATE NOT NULL,
  date_fin DATE,
  loyer_hc NUMERIC NOT NULL CHECK (loyer_hc >= 0),
  charges_locatives NUMERIC DEFAULT 0 CHECK (charges_locatives >= 0),
  depot_garantie NUMERIC DEFAULT 0 CHECK (depot_garantie >= 0),
  indice_irl_reference TEXT,
  date_revision DATE,
  etat_lieux_entree DATE,
  etat_lieux_sortie DATE,
  statut TEXT NOT NULL DEFAULT 'en_cours' CHECK (statut IN ('en_cours','expire','resilie')),
  document_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Jointure bail-locataires (colocation)
CREATE TABLE bail_locataires (
  id_bail UUID NOT NULL REFERENCES baux(id) ON DELETE CASCADE,
  id_locataire UUID NOT NULL REFERENCES locataires(id) ON DELETE CASCADE,
  PRIMARY KEY (id_bail, id_locataire)
);

-- Assurance PNO
CREATE TABLE assurances_pno (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  id_bien UUID NOT NULL REFERENCES biens(id) ON DELETE CASCADE,
  compagnie TEXT NOT NULL,
  numero_contrat TEXT,
  montant_annuel NUMERIC NOT NULL CHECK (montant_annuel >= 0),
  date_echeance DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Frais d'agence
CREATE TABLE frais_agence (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  id_bien UUID NOT NULL REFERENCES biens(id) ON DELETE CASCADE,
  nom_agence TEXT NOT NULL,
  contact TEXT,
  type_frais TEXT NOT NULL CHECK (type_frais IN ('pourcentage','fixe')),
  montant_ou_pourcentage NUMERIC NOT NULL CHECK (montant_ou_pourcentage >= 0),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Préférences notifications
CREATE TABLE notification_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  type TEXT NOT NULL,
  email_enabled BOOLEAN DEFAULT FALSE,
  in_app_enabled BOOLEAN DEFAULT TRUE,
  UNIQUE(user_id, type)
);

-- Documents bien
CREATE TABLE documents_bien (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  id_bien UUID NOT NULL REFERENCES biens(id) ON DELETE CASCADE,
  categorie TEXT NOT NULL CHECK (categorie IN ('bail','diagnostic','etat_lieux','quittance','photo','autre')),
  nom TEXT NOT NULL,
  file_url TEXT NOT NULL,
  file_size INTEGER,
  uploaded_at TIMESTAMPTZ DEFAULT NOW()
);
```

### RLS à ajouter

Toutes les nouvelles tables : policies basées sur `biens.id_sci → associes.user_id = auth.uid()`
- SELECT : tous les associés de la SCI
- INSERT/UPDATE/DELETE : uniquement les associés avec role = 'gerant'

---

## 10. User Stories — Priorisées

### P0 — Bloquant (avant lancement)

| US | Description |
|----|-------------|
| US-P0.1 | Paywall : pas d'accès sans abonnement actif |
| US-P0.2 | Onboarding : wizard 5 étapes à la 1ère connexion |
| US-P0.3 | Navigation top-down : routes `/scis/:id/biens/:id` |
| US-P0.4 | Dashboard 4 blocs compartimentés |
| US-P0.5 | Fiche Bien sections A+C (identité + loyers) |

### P1 — Important (sprint suivant)

| US | Description |
|----|-------------|
| US-P1.1 | Fiche Bien section B : bail + locataire + colocation |
| US-P1.2 | Fiche Bien section D : charges + assurance PNO + frais agence |
| US-P1.3 | Historique des baux par bien |
| US-P1.4 | Accès associés en lecture seule |
| US-P1.5 | Notifications email configurables |

### P2 — Nice to have

| US | Description |
|----|-------------|
| US-P2.1 | Fiche Bien section F : documents uploadés |
| US-P2.2 | Vue Finances transversale |
| US-P2.3 | Fiche Bien section E : rentabilité enrichie |
| US-P2.4 | Génération automatique de bail type |
| US-P2.5 | DPE, surface, photos sur fiche bien |

---

## 11. Hors scope (pour plus tard)

- Comptabilité complète (grand livre, bilan)
- Intégration bancaire (rapprochement automatique)
- Signature électronique de bail
- Gestion des AG (assemblées générales)
- App mobile native
- Multi-langue
