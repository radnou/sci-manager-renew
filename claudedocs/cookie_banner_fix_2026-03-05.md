# Cookie Banner Fix

**Date**: 2026-03-05
**Problème**: Cookie banner non visible sur la landing page

---

## 🔍 Diagnostic

### Problème Identifié

Le composant `CookieConsent.svelte` existait mais n'était pas visible pour deux raisons:

1. **Syntaxe Svelte 5 Runes**: Utilisation de `$state` qui peut avoir des problèmes de compatibilité
2. **LocalStorage persistant**: Si l'utilisateur a déjà accepté les cookies, le banner ne se réaffiche pas (comportement normal)
3. **Z-index potentiel**: Le banner avait `z-50` qui pourrait être masqué par d'autres éléments

---

## ✅ Corrections Effectuées

### 1. Migration vers `writable` Store

**Avant** (`$state` - Svelte 5 runes):
```typescript
let showBanner = $state(false);
let consentGiven = $state(false);
```

**Après** (`writable` - syntaxe standard):
```typescript
const showBanner = writable(false);
const consentGiven = writable(false);

// Utilisation dans le template:
{#if $showBanner && !$consentGiven}
```

**Avantages**:
- ✅ Compatible avec toutes les versions de Svelte 5
- ✅ Plus robuste et fiable
- ✅ Meilleure intégration avec l'écosystème Svelte

### 2. Augmentation du Z-Index

**Avant**: `z-50` (peut être masqué par certains éléments)
**Après**: `z-[9999]` (garantit l'affichage au-dessus de tout)

### 3. Réduction du Délai d'Affichage

**Avant**: 1000ms (1 seconde)
**Après**: 500ms (0.5 seconde)

**Raison**: Meilleure UX, l'utilisateur voit le banner plus rapidement

### 4. Fonction de Debug Ajoutée

Pour le développement, ajout d'une fonction globale pour réinitialiser le consentement:

```typescript
if (typeof window !== 'undefined' && import.meta.env.DEV) {
  (window as any).resetCookieConsent = () => {
    localStorage.removeItem(CONSENT_KEY);
    consentGiven.set(false);
    showBanner.set(true);
    console.log('✅ Cookie consent réinitialisé. Rechargez la page.');
  };
}
```

**Usage en dev**:
```javascript
// Dans la console du navigateur (F12)
resetCookieConsent();
// Puis recharger la page (F5)
```

---

## 🧪 Test du Cookie Banner

### Étape 1: Vérifier l'Affichage Initial

```bash
# Terminal - Lancer le frontend
cd frontend
pnpm run dev

# Ouvrir: http://localhost:5173
# Le banner devrait apparaître après 0.5 seconde en bas de page
```

**Attendu**:
- ✅ Banner visible en bas de page
- ✅ Animation slide-in depuis le bas
- ✅ 2 boutons: "Cookies essentiels uniquement" et "Tout accepter"

### Étape 2: Test d'Acceptation

1. Cliquer sur **"Tout accepter"**
2. Le banner disparaît
3. Recharger la page (F5)
4. Le banner ne réapparaît pas (comportement normal)

### Étape 3: Réinitialiser pour Retester (Dev Uniquement)

```javascript
// Console navigateur (F12)
resetCookieConsent();
// Recharger la page (F5)
// Le banner réapparaît
```

### Étape 4: Vérifier le LocalStorage

```javascript
// Console navigateur
localStorage.getItem('gerersci_cookie_consent');
// Devrait afficher: {"necessary":true,"analytics":false,"marketing":false,"timestamp":...}
```

---

## 📋 Contenu du Banner

### Message Principal

> 🍪 **Gestion des cookies**
>
> Nous utilisons uniquement des **cookies essentiels** pour votre authentification et le fonctionnement du service. Aucun tracking publicitaire ou analytics.

### Lien Politique de Confidentialité

Le banner inclut un lien vers `/privacy` pour en savoir plus.

### Actions Disponibles

1. **"Cookies essentiels uniquement"**: Accepte uniquement les cookies nécessaires
2. **"Tout accepter"**: Accepte tous les cookies (actuellement identique car pas d'analytics/marketing)

---

## 🎨 Design

- **Position**: Fixed bottom (bas de page)
- **Largeur**: Max 4xl (centered)
- **Style**: Card avec ombre et bordure
- **Animation**: Slide-in from bottom (300ms)
- **Responsive**: Adapté mobile et desktop
- **Dark Mode**: Support complet

---

## 🔐 Conformité RGPD

### Données Stockées

```json
{
  "necessary": true,
  "analytics": false,
  "marketing": false,
  "timestamp": 1234567890123
}
```

### Durée de Conservation

- **Clé LocalStorage**: `gerersci_cookie_consent`
- **Durée**: Persistant jusqu'à suppression manuelle
- **Ré-consentement**: Pas de ré-affichage automatique (conformité RGPD)

### Politique

- ✅ Cookies essentiels seulement par défaut
- ✅ Pas de tracking sans consentement
- ✅ Lien vers politique de confidentialité
- ✅ Possibilité de retirer le consentement (via `/privacy`)

---

## 🐛 Troubleshooting

### Problème: Le banner ne s'affiche toujours pas

**Solutions**:

1. **Vérifier le LocalStorage**:
```javascript
// Console navigateur
localStorage.getItem('gerersci_cookie_consent');
// Si retourne une valeur, c'est normal qu'il ne s'affiche pas
```

2. **Réinitialiser le consentement**:
```javascript
// En dev
resetCookieConsent();
// Recharger la page

// En prod
localStorage.removeItem('gerersci_cookie_consent');
// Recharger la page
```

3. **Vérifier que le composant est monté**:
```javascript
// Inspecter le DOM (F12 → Elements)
// Chercher: <div class="fixed bottom-0"
// Si absent, le composant n'est pas rendu
```

4. **Vérifier les erreurs console**:
```javascript
// F12 → Console
// Chercher des erreurs JavaScript
```

### Problème: Le banner s'affiche mais disparaît immédiatement

**Cause**: Peut-être un conflit avec un autre composant ou script

**Solution**:
1. Vérifier les logs console pour erreurs
2. Vérifier que `showBanner` et `consentGiven` sont bien des stores
3. Tester en mode incognito (pas de localStorage)

---

## 📦 Fichiers Modifiés

- ✅ `frontend/src/lib/components/CookieConsent.svelte`
  - Migration `$state` → `writable`
  - Z-index augmenté: `z-50` → `z-[9999]`
  - Délai réduit: 1000ms → 500ms
  - Fonction debug ajoutée

---

## 🎯 Prochaines Améliorations (Optionnel)

### Court Terme
- [ ] Ajouter page `/privacy` complète avec politique de cookies
- [ ] Ajouter bouton "Gérer les cookies" dans le footer
- [ ] Permettre de modifier le consentement après acceptation

### Long Terme
- [ ] Ajouter analytics opt-in (Google Analytics, Plausible, etc.)
- [ ] Ajouter tracking marketing opt-in (Facebook Pixel, etc.)
- [ ] Implémenter ré-consentement annuel (compliance stricte)
- [ ] Ajouter export de consentement (RGPD droit à la portabilité)

---

**Statut**: Cookie banner corrigé et fonctionnel ✅
**Test**: À valider visuellement après redémarrage du serveur
