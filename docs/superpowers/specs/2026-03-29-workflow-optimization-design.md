# Workflow Optimization — Navigation + Checkout + Triggers Conversion

**Date**: 2026-03-29
**Contexte**: Retours vidéos Playwright — le workflow n'est pas optimal
**Validé par**: Panel Hormozi

---

## Problèmes identifiés

1. **Checkout confus** : visiteur clique plan → modale consent → échec → register sans contexte
2. **Navigation trop profonde** : 4 clics pour un bien (Dashboard → SCI → Biens → Fiche)
3. **Navbar surchargée** : 7 items, l'user ne sait pas où aller
4. **Pas de trigger de conversion** dans l'expérience démo
5. **Message register** vend des features au lieu de la transformation

---

## Changement 1 : Checkout simplifié pour visiteurs

### Règle
- **Visiteur anonyme** clique un plan → redirect `/register?plan=<key>` (PAS de modale)
- **User connecté** clique un plan → modale checkout consent → Stripe (comportement actuel)

### Fichiers
- `routes/+page.svelte` : dans `openCheckoutModal()`, vérifier `isAuthenticated`. Si non → `goto('/register?plan=' + planKey)`
- `routes/pricing/+page.svelte` : idem

### Détection
```typescript
const { data: { session } } = await supabase.auth.getSession();
if (!session) {
  goto(`/register?plan=${planKey}`);
  return;
}
// Sinon: ouvrir modale checkout comme avant
```

---

## Changement 2 : Message register Hormozi

### Page `/register` — nouveau contenu

Quand `?plan=` est présent dans l'URL :

```
Badge:    "Accès gratuit — aucune carte bancaire requise"

H1:       "Voyez ce que donnerait votre SCI
           dans un vrai cockpit de gestion."

Sub:      "Données de démo pré-remplies. Zéro carte bancaire.
           2 minutes pour comprendre."

[Formulaire email + mdp + CGU]

Info plan: "Plan retenu : Pilotage — SCI illimitées, CERFA 2044, fiscalité complète.
            Activable après exploration. Annulable sous 30 jours."
```

Quand PAS de `?plan=` :

```
H1:       "Créez votre compte"
Sub:      "Explorez GérerSCI avec des données de démonstration."
```

### Règles
- Pas de prix visible sur la page register
- Nom du plan + features clés = ancrage de valeur
- "Annulable sous 30 jours" = réduction du risque

### Fichier
- `routes/register/+page.svelte`

---

## Changement 3 : Raccourci biens depuis le dashboard

### Cartes SCI enrichies

Les cartes SCI du dashboard affichent chaque bien avec indicateur d'état :

```
┌─ SCI Résidence Belleville ──────── active ─┐
│  2 biens        6 960 €                    │
│  Recouvrement   67%                        │
│  ──────────────────────────────────────── │
│  🏠 45 av. Jean Jaurès  850€  ⚠️ impayé   │  ← cliquable → fiche bien
│  🏠 12 rue Victor Hugo  620€  ✅ à jour    │  ← cliquable → fiche bien
└────────────────────────────────────────────┘
```

### Fichier
- `lib/components/dashboard/DashboardSciCards.svelte`
- Nécessite : les biens par SCI dans la réponse dashboard API (vérifier si déjà présent)

---

## Changement 4 : Navbar simplifiée + "Pilotage" vitrine

### Avant (7 items)
```
Tableau de bord | Mes SCI ▾ | Exploitation | Échéances | Finances | Bilans | [user]
```

### Après (4 items)
```
Tableau de bord | Mes SCI ▾ | Finances | Pilotage ▾ | [user]
```

### Dropdown "Mes SCI ▾"
```
Mes SCI ▾
├── SCI Résidence Belleville
│   ├── 45 av. Jean Jaurès
│   └── 12 rue Victor Hugo
├── ──────────
└── Toutes les SCI
```

### Dropdown "Pilotage ▾"
```
Pilotage ▾
├── Échéances
├── Bilans mensuels
├── Fiscalité
└── Exploitation
```

En mode demo : chaque clic dans "Pilotage" fonctionne normalement mais le label "Pilotage" rappelle subtilement le nom du plan premium.

### Items supprimés de la navbar top-level
- Exploitation → dans dropdown Pilotage
- Échéances → dans dropdown Pilotage
- Bilans → dans dropdown Pilotage

### Fichier
- `lib/components/AppNavbar.svelte`

---

## Changement 5 : Fil d'Ariane amélioré

### Améliorations CSS
- Background : `bg-slate-50 dark:bg-slate-900` (bande visible)
- Taille : `text-sm font-medium` (plus lisible)
- Bouton retour : flèche ← à gauche, cliquable
- Chaque segment cliquable

### Fichier
- `lib/components/AppNavbar.svelte` (section breadcrumb)

---

## Changement 6 (P0) : Triggers de conversion dans la démo

### Composant `DemoConversionPrompt.svelte`

Overlay léger (pas modal bloquant) qui apparaît quand un user demo réalise une action haute valeur :

```
┌──────────────────────────────────────────────────────┐
│  📄 Cette quittance a été générée avec des données   │
│     de démonstration.                                │
│                                                      │
│  Ajoutez votre première SCI pour générer les vôtres. │
│                                                      │
│  [Commencer avec mes vraies données →]  [Continuer]  │
└──────────────────────────────────────────────────────┘
```

### Triggers
| Action | Message personnalisé |
|--------|---------------------|
| Quittance PDF vue | "Cette quittance a été générée avec des données de démonstration." |
| CERFA/Fiscalité consulté | "Ce résumé fiscal est basé sur des données fictives." |
| Bilan mensuel consulté | "Ce bilan reflète des données de démonstration." |
| 3ème page visitée | "Vous explorez depuis quelques minutes. Prêt à gérer vos vraies SCI ?" |

### Boutons
- **"Commencer avec mes vraies données →"** : redirige vers `/pricing` (pas vers l'onboarding — il faut d'abord payer)
- **"Continuer l'exploration"** : ferme le prompt, ne réapparaît pas pendant 10 min (localStorage timer)

### Fichier
- Créer : `lib/components/DemoConversionPrompt.svelte`
- Intégrer dans : `FicheBienLoyers.svelte` (quittance), `bilans/+page.svelte`, `fiscalite/+page.svelte`
- Trigger "3ème page" : dans `(app)/+layout.svelte` (compteur de pages visitées en demo)

---

## Fichiers impactés — Résumé

| Fichier | Changement |
|---------|-----------|
| `routes/+page.svelte` | Redirect register au lieu de modale pour visiteurs |
| `routes/pricing/+page.svelte` | Idem |
| `routes/register/+page.svelte` | Nouveau message Hormozi, masquer prix |
| `lib/components/dashboard/DashboardSciCards.svelte` | Liens biens directs + indicateurs état |
| `lib/components/AppNavbar.svelte` | Simplification 7→4, dropdown Pilotage, breadcrumb amélioré |
| `lib/components/DemoConversionPrompt.svelte` | Nouveau — trigger conversion |
| `lib/components/fiche-bien/FicheBienLoyers.svelte` | Intégration trigger quittance |
| `routes/(app)/bilans/+page.svelte` | Intégration trigger bilan |
| `routes/(app)/scis/[sciId]/fiscalite/+page.svelte` | Intégration trigger fiscalité |
| `routes/(app)/+layout.svelte` | Compteur pages demo + trigger 3ème page |

---

## Hors scope

- Données demo plus réalistes (nom SCI crédible, scénarios reconnaissables) → spec séparé
- A/B test messages → après premiers 100 inscrits
- Refactoring complet de la navigation → itération future
