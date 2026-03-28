# Demo-First "Full Steak" — Données demo + paywall soft

**Date**: 2026-03-28
**Principe**: "Don't give a free sample. Give them the FULL steak and charge them after." — Hormozi
**Dark pattern crédibilité**: Écrans de chargement façon Kayak/Skyscanner pour ancrer la valeur perçue

---

## Vue d'ensemble

```
AVANT:  Landing → Inscription → Payer → Onboarding → Dashboard (vide)
APRÈS:  Landing → Inscription → Loading crédibilité → Dashboard (demo) → Explorer → 🔒 → Payer → Ses vraies données
```

### Flow utilisateur détaillé

```
1. User clique "Inscription" sur la landing
2. Page /register — email + magic link (existant)
3. User confirme son email → connecté
4. NOUVEAU: Écran de chargement "crédibilité" (5-8 secondes)
   - "Création de votre espace de gestion..."        ████████░░
   - "Importation des données de démonstration..."    ████████████░░
   - "Calcul des indicateurs de votre portefeuille..." ████████████████░░
   - "Préparation de votre tableau de bord..."        ████████████████████
5. Redirect vers /dashboard avec données demo pré-chargées
6. Bandeau demo persistant en haut
7. User explore librement (lecture)
8. User clique un bouton d'action → 🔒 UpgradePrompt
9. User souscrit → données demo supprimées → onboarding pour ses vraies données
```

---

## Composant 1 : Écran de chargement "crédibilité"

### Route : `/welcome` (nouvelle)

Page interstitielle après la première connexion (inscription), avant le dashboard.

### Design

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│              [Logo GérerSCI]                             │
│                                                          │
│     Bienvenue ! Nous préparons votre espace.             │
│                                                          │
│     ┌──────────────────────────────────────┐             │
│     │  ✅ Création de votre espace         │ (fade in)   │
│     │  ✅ Chargement des données demo      │ (1.5s)      │
│     │  🔄 Calcul de vos indicateurs...     │ (2s)        │
│     │  ⏳ Préparation du tableau de bord   │ (attente)   │
│     └──────────────────────────────────────┘             │
│                                                          │
│     [████████████████████░░░░░░] 72%                     │
│                                                          │
│     💡 Saviez-vous ? Un loyer impayé non détecté         │
│     coûte en moyenne 800€ au propriétaire.               │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Étapes du loading (timing chorégraphié)

| Étape | Texte | Durée | Icône |
|-------|-------|-------|-------|
| 1 | Création de votre espace de gestion | 1.5s | ✅ (terminé) |
| 2 | Chargement des données de démonstration | 2.0s | ✅ → 🔄 → ✅ |
| 3 | Calcul de vos indicateurs financiers | 2.0s | ✅ → 🔄 → ✅ |
| 4 | Préparation de votre tableau de bord | 1.5s | ✅ → 🔄 → ✅ |
| **Total** | | **~7s** | |

### Faits rotatifs (pendant le chargement)

Affichés en bas, changent toutes les 2.5s :
1. "Un loyer impayé non détecté coûte en moyenne 800€ au propriétaire."
2. "Les gestionnaires digitalisés réduisent leurs impayés de 63%."
3. "GérerSCI pré-remplit votre CERFA 2044 automatiquement."
4. "72% des gestionnaires constatent une amélioration en 12 mois."

### Comportement réel

- L'appel API `POST /api/v1/demo/seed` est lancé dès le montage du composant
- Les étapes visuelles avancent sur un timer fixe (indépendant de l'API)
- Si l'API finit avant le timer → on attend la fin de l'animation
- Si l'API échoue → on affiche quand même le dashboard (sans données demo) avec un toast d'erreur
- Après la dernière étape → redirect automatique vers `/dashboard`
- La page n'est visitée qu'UNE FOIS (flag `demo_seeded` dans le profil utilisateur ou localStorage)

---

## Composant 2 : Données demo (backend seed)

### Endpoint : `POST /api/v1/demo/seed`

Crée un jeu de données réalistes pour l'utilisateur :

```python
# Données créées :
SCI "SCI Résidence Belleville"
├── Bien: "45 avenue Jean Jaurès, Lyon 69007"
│   ├── Type: Appartement, 65m², T3, DPE C, Location nue
│   ├── Loyer CC: 850€, Charges: 50€
│   ├── Bail: actif depuis 2025-09-01
│   │   └── Locataire: "Marie Lefèvre" (marie.lefevre@demo.fr)
│   ├── Loyers: 6 derniers mois (4 payés, 1 en attente, 1 en retard)
│   ├── Charges: copropriété 150€/trim, taxe foncière 800€/an
│   └── Assurance PNO: AXA, 180€/an, expire 2027-01-15
│
└── Bien: "12 rue Victor Hugo, Lyon 69002"
    ├── Type: Studio, 28m², T1, DPE D, Meublé
    ├── Loyer CC: 620€, Charges: 40€
    ├── Bail: actif depuis 2026-01-01
    │   └── Locataire: "Thomas Durand" (thomas.durand@demo.fr)
    ├── Loyers: 3 derniers mois (2 payés, 1 en attente)
    └── Charges: copropriété 90€/trim

Associé: user lui-même, 100% des parts, rôle "gérant"
```

### Marquage demo

- Chaque enregistrement créé a un champ `is_demo: true` (ou tag metadata)
- Alternative : préfixer les IDs avec `demo_` pour identification rapide
- Recommandé : ajouter une colonne `is_demo BOOLEAN DEFAULT FALSE` aux tables `sci`, `biens`, `baux`, `loyers`, `charges`, `locataires`, `assurance_pno`

### Nettoyage

- Quand l'user souscrit un plan → `DELETE FROM xxx WHERE is_demo = true AND user_id = $1`
- Endpoint : `DELETE /api/v1/demo/cleanup` (appelé automatiquement après paiement Stripe)
- Le webhook Stripe `checkout.session.completed` trigger le cleanup

### Rate limiting

- `POST /api/v1/demo/seed` : 1/heure par user (empêche les abus)
- Ne s'exécute que si l'user n'a PAS de subscription active et n'a PAS déjà des données demo

---

## Composant 3 : Bandeau demo persistant

### Position : haut de l'app layout, sous la navbar

```
┌──────────────────────────────────────────────────────────────────┐
│ 🔍 Vous explorez des données de démonstration.                  │
│    Souscrivez pour gérer vos vraies SCI.     [Souscrire →]      │
└──────────────────────────────────────────────────────────────────┘
```

### Comportement

- Affiché quand `subscription.is_active === false` ET l'user a des données
- NON dismissable (pas de bouton fermer)
- Background : `bg-amber-50 border-amber-200` (light) / `bg-amber-950/30 border-amber-800` (dark)
- Le bouton "Souscrire →" va vers `/pricing`
- Ne s'affiche PAS sur les pages publiques (/pricing, /login, etc.)

---

## Composant 4 : Verrou + UpgradePrompt

### Composant `LockedAction.svelte`

Wrapper pour tout bouton/action qui nécessite un plan payant.

```svelte
Props:
  - children: Snippet (le bouton original)
  - action: string ("Enregistrer un loyer", "Générer une quittance", etc.)
  - isDemo: boolean

Comportement:
  - Si isDemo=false → rend les children normalement
  - Si isDemo=true → ajoute une icône cadenas + au clic, ouvre UpgradePrompt au lieu de l'action
```

### Composant `UpgradePrompt.svelte`

Modal qui s'ouvre quand un user demo clique sur une action verrouillée.

```
┌──────────────────────────────────────────────────┐
│                                                  │
│  🔒 Fonctionnalité réservée aux abonnés          │
│                                                  │
│  Pour {action}, souscrivez un plan GérerSCI.     │
│                                                  │
│  ✅ Accès complet à toutes les fonctionnalités   │
│  ✅ Vos données réelles, pas de la démo          │
│  ✅ Support email dédié                          │
│  ✅ Garantie satisfait ou remboursé 30 jours     │
│                                                  │
│  [Voir les plans →]        [Plus tard]           │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Tableau de verrouillage

| Action | Demo | Payant |
|--------|------|--------|
| Voir dashboard, KPIs, graphiques | ✅ libre | ✅ |
| Naviguer biens, fiche bien (9 onglets) | ✅ libre | ✅ |
| Voir loyers, charges, historique | ✅ libre | ✅ |
| Voir quittance PDF (1 seule) | ✅ libre | ✅ |
| Voir bilans mensuels | ✅ libre | ✅ |
| Voir associés, parts | ✅ libre | ✅ |
| Voir fiscalité, CERFA | ✅ libre | ✅ |
| **Créer/modifier/supprimer SCI** | 🔒 | ✅ |
| **Créer/modifier/supprimer bien** | 🔒 | ✅ |
| **Enregistrer/modifier loyer** | 🔒 | ✅ |
| **Générer quittance** | 🔒 | ✅ |
| **Créer/modifier bail** | 🔒 | ✅ |
| **Export CSV/PDF** | 🔒 | ✅ |
| **Configurer notifications** | 🔒 | ✅ |
| **Import CSV** | 🔒 | ✅ |

---

## Composant 5 : Modifications layout + routing

### `(app)/+layout.ts` — Bypass paywall pour demo

```typescript
// AVANT:
if (!subscription.is_active) {
    throw redirect(302, '/pricing');
}

// APRÈS:
// Laisser passer les users sans subscription (mode demo)
// Le bandeau demo + les verrous gèrent la restriction
```

### Nouveau flow post-inscription

```
/register → confirme email → première connexion détectée
  → Si !subscription.is_active ET !demo_seeded:
      → redirect vers /welcome (loading crédibilité)
      → /welcome appelle POST /api/v1/demo/seed
      → Après animation → redirect /dashboard
  → Si !subscription.is_active ET demo_seeded:
      → /dashboard direct (avec bandeau demo)
  → Si subscription.is_active:
      → /dashboard normal (comportement actuel)
```

### Onboarding

- L'onboarding actuel est CONSERVÉ mais déplacé APRÈS le paiement
- Flow: user paye → cleanup demo → redirect onboarding → crée ses vraies données
- Le check `!onboarding_completed` dans layout.ts ne s'applique QUE si `is_active === true`

---

## Migration DB

### Nouvelle colonne `is_demo`

```sql
-- Migration: 021_demo_data_support.sql
ALTER TABLE sci ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE biens ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE baux ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE loyers ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE charges ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE locataires ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE assurance_pno ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;

-- Index pour le cleanup rapide
CREATE INDEX IF NOT EXISTS idx_sci_is_demo ON sci(is_demo) WHERE is_demo = TRUE;
CREATE INDEX IF NOT EXISTS idx_biens_is_demo ON biens(is_demo) WHERE is_demo = TRUE;
```

### Nouveau flag utilisateur

```sql
-- Dans subscriptions ou une nouvelle table user_flags
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS demo_seeded BOOLEAN DEFAULT FALSE;
```

---

## Fichiers impactés

| Fichier | Action | Changement |
|---------|--------|-----------|
| `supabase/migrations/021_demo_data.sql` | Créer | Colonnes is_demo + index |
| `backend/app/api/v1/demo.py` | Créer | Endpoints seed + cleanup |
| `backend/app/services/demo_service.py` | Créer | Logique de seed des données réalistes |
| `backend/app/api/v1/stripe.py` | Modifier | Trigger cleanup dans webhook checkout.completed |
| `frontend/src/routes/welcome/+page.svelte` | Créer | Écran de chargement crédibilité |
| `frontend/src/routes/(app)/+layout.ts` | Modifier | Bypass paywall, check demo_seeded |
| `frontend/src/routes/(app)/+layout.svelte` | Modifier | Ajouter DemoBanner |
| `frontend/src/lib/components/DemoBanner.svelte` | Créer | Bandeau demo persistant |
| `frontend/src/lib/components/LockedAction.svelte` | Créer | Wrapper cadenas pour actions |
| `frontend/src/lib/components/UpgradePrompt.svelte` | Créer | Modal upgrade |
| `frontend/src/lib/api/demo.ts` | Créer | seedDemo() API function |
| Multiples pages app | Modifier | Wrapper LockedAction sur boutons d'écriture |

---

## Hors scope (futur)

- Personnalisation des données demo (choisir le type de bien)
- Analytics sur le taux de conversion demo → payant
- Email de relance 24h/72h après inscription sans paiement
- A/B test durée du loading (5s vs 8s vs 12s)
