# Diagnostic Magic Link Authentication

**Date**: 2026-03-05
**Problème**: Le lien magic de connexion et inscription ne fonctionne pas

---

## 🔍 Analyse du Flux Actuel

### Architecture Magic Link

Le système utilise **Supabase Auth** avec OTP (One-Time Password) magic link:

```
1. User → /login → Entre email
2. Frontend → supabase.auth.signInWithOtp() → Supabase Auth
3. Supabase Auth → Envoie email avec magic link
4. User clique sur lien → Redirigé vers /auth/callback
5. Frontend → supabase.auth.getSession() → Récupère session
6. Frontend → Redirige vers /dashboard
```

### Fichiers Impliqués

#### Frontend
- `frontend/src/routes/login/+page.svelte` (lignes 14-42): Envoi du magic link
- `frontend/src/routes/auth/callback/+page.svelte` (lignes 12-49): Traitement callback
- `frontend/src/lib/supabase.ts` (lignes 1-6): Client Supabase

#### Backend
- `backend/app/api/v1/auth.py` (lignes 21-49): Endpoint `/api/v1/auth/magic-link/send` (non utilisé)
- `backend/app/services/auth_service.py` (lignes 17-31): Service magic link (non utilisé)

---

## ⚠️ Problèmes Identifiés

### 1. Configuration Supabase Manquante

**Fichier**: `frontend/src/lib/supabase.ts`

```typescript
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'http://localhost:54321';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'public-anon-key';
```

**Problème**:
- Les variables d'environnement `VITE_SUPABASE_URL` et `VITE_SUPABASE_ANON_KEY` doivent être définies
- Actuellement, utilise des valeurs par défaut qui ne sont pas configurées

**Vérification**:
```bash
# Aucun fichier .env trouvé à la racine
find . -name ".env" -maxdepth 2
# → Pas de résultat
```

### 2. Configuration Email Supabase

**Problème**: Supabase doit être configuré pour envoyer des emails via:
- **Option 1**: Supabase Email Service (par défaut, limité)
- **Option 2**: SMTP custom (Resend, SendGrid, etc.)
- **Option 3**: Resend via Supabase Extension

**État actuel**:
- Variable `RESEND_API_KEY` existe dans `backend/app/core/config.py`
- Mais Supabase Auth n'est pas configuré pour utiliser Resend

### 3. Redirect URL Non Configuré

**Code actuel** (`frontend/src/routes/login/+page.svelte:21`):
```typescript
emailRedirectTo: `${window.location.origin}/auth/callback`
```

**Problème**:
- Cette URL doit être whitelistée dans Supabase Dashboard
- Path: Authentication → URL Configuration → Redirect URLs

### 4. Flux Hybride Backend/Frontend

**Observation**:
- Le frontend envoie le magic link directement via Supabase Client
- Le backend a un endpoint `/api/v1/auth/magic-link/send` qui n'est jamais appelé
- Confusion sur qui gère l'envoi du magic link

---

## ✅ Solutions Proposées

### Solution 1: Configuration Environnement (Immédiate)

#### Étape 1.1: Créer fichier `.env` frontend

```bash
# frontend/.env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-from-supabase
VITE_API_URL=http://localhost:8000
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
VITE_STRIPE_PRICE_STARTER=price_...
VITE_STRIPE_PRICE_PRO=price_...
VITE_STRIPE_PRICE_LIFETIME=price_...
VITE_DEFAULT_SCI_ID=sci-1
```

**Obtenir les clés Supabase**:
1. Aller sur [app.supabase.com](https://app.supabase.com)
2. Sélectionner votre projet
3. Settings → API → Project URL + anon public key

#### Étape 1.2: Créer fichier `.env` backend

```bash
# backend/.env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret

RESEND_API_KEY=re_your_resend_key
RESEND_FROM_EMAIL=noreply@scimanager.fr

DATABASE_URL=postgresql://...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

#### Étape 1.3: Redémarrer les services

```bash
cd frontend && pnpm run dev
cd backend && uvicorn app.main:app --reload
```

---

### Solution 2: Configuration Supabase Dashboard (Obligatoire)

#### Étape 2.1: Configurer Redirect URLs

1. Supabase Dashboard → Authentication → URL Configuration
2. Ajouter dans **Redirect URLs**:
   - `http://localhost:5173/auth/callback` (dev)
   - `https://scimanager.fr/auth/callback` (prod)
3. Ajouter dans **Site URL**:
   - `http://localhost:5173` (dev)
   - `https://scimanager.fr` (prod)

#### Étape 2.2: Configurer SMTP avec Resend

**Option A: Via Supabase Settings**

1. Supabase Dashboard → Project Settings → Auth
2. SMTP Settings:
   - Host: `smtp.resend.com`
   - Port: `587` ou `465`
   - Username: `resend`
   - Password: `Your Resend API Key`
   - Sender email: `noreply@scimanager.fr`
   - Sender name: `SCI Manager`

**Option B: Utiliser Supabase Email Service (Temporaire)**

1. Supabase Dashboard → Project Settings → Auth
2. Enable Email Provider
3. **Limitation**: Max 3 emails/heure en mode gratuit

#### Étape 2.3: Personnaliser Email Template

1. Supabase Dashboard → Authentication → Email Templates
2. Sélectionner **Magic Link**
3. Personnaliser le contenu:

```html
<h2>Connexion à SCI Manager</h2>
<p>Bonjour,</p>
<p>Cliquez sur le lien ci-dessous pour vous connecter à votre cockpit SCI :</p>
<p><a href="{{ .ConfirmationURL }}">Se connecter</a></p>
<p>Ce lien est valide pendant 1 heure.</p>
<p>Si vous n'avez pas demandé cette connexion, ignorez cet email.</p>
<p>L'équipe SCI Manager</p>
```

---

### Solution 3: Debug et Tests (Vérification)

#### Test 1: Vérifier Configuration Supabase

```bash
# Dans le navigateur (Console DevTools)
console.log('Supabase URL:', import.meta.env.VITE_SUPABASE_URL);
console.log('Supabase Key:', import.meta.env.VITE_SUPABASE_ANON_KEY);
```

**Attendu**:
- URLs correctes (pas localhost si prod)
- Keys non vides

#### Test 2: Tester Envoi Magic Link

```typescript
// Dans la console navigateur sur /login
const { data, error } = await supabase.auth.signInWithOtp({
  email: 'test@example.com',
  options: {
    emailRedirectTo: `${window.location.origin}/auth/callback`
  }
});
console.log('Result:', { data, error });
```

**Erreurs possibles**:
- `Invalid email` → Format email incorrect
- `Email rate limit exceeded` → Trop d'envois (attendre 1h)
- `Email not configured` → SMTP non configuré dans Supabase

#### Test 3: Vérifier Logs Supabase

1. Supabase Dashboard → Logs → Auth Logs
2. Filtrer par type: `magic_link`
3. Vérifier:
   - Email envoyé avec succès
   - Erreurs SMTP
   - Rate limiting

---

### Solution 4: Alternative - Utiliser Resend Directement (Backend)

Si Supabase Email pose problème, utiliser l'endpoint backend existant:

#### Modifier Frontend (`frontend/src/routes/login/+page.svelte`)

```typescript
async function handleMagicLink() {
  errorMessage = '';
  isLoading = true;

  try {
    // Option 1: Via Supabase (actuel)
    const { error } = await supabase.auth.signInWithOtp({
      email: email,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`
      }
    });

    // Option 2: Via Backend (alternative)
    // const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/auth/magic-link/send`, {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ email })
    // });
    // const data = await response.json();

    if (error) {
      errorMessage = error.message;
      addToast({
        title: 'Erreur',
        description: error.message,
        variant: 'error'
      });
    } else {
      showCheckEmail = true;
      addToast({
        title: 'Email envoyé',
        description: `Vérifiez votre boîte mail à ${email}`,
        variant: 'success'
      });
    }
  } catch (err) {
    errorMessage = 'Erreur lors de l\'envoi du lien';
    addToast({
      title: 'Erreur',
      description: 'Une erreur est survenue. Veuillez réessayer.',
      variant: 'error'
    });
  }

  isLoading = false;
}
```

---

## 🎯 Checklist de Vérification

### Configuration Initiale
- [ ] Fichier `frontend/.env` créé avec variables Supabase
- [ ] Fichier `backend/.env` créé avec clés Resend
- [ ] Services redémarrés après ajout des variables

### Supabase Dashboard
- [ ] Redirect URLs configurées (localhost + prod)
- [ ] Site URL configurée
- [ ] SMTP Resend configuré (ou Email Service activé)
- [ ] Email template personnalisé

### Tests
- [ ] Envoi magic link réussit (check console)
- [ ] Email reçu dans boîte mail
- [ ] Clic sur lien → redirection vers `/auth/callback`
- [ ] Session créée → redirection vers `/dashboard`

### Monitoring
- [ ] Logs Supabase Auth vérifiés
- [ ] Rate limits non atteints
- [ ] Erreurs SMTP résolues

---

## 📚 Documentation Supabase

- [Magic Link Configuration](https://supabase.com/docs/guides/auth/auth-email)
- [SMTP Configuration](https://supabase.com/docs/guides/auth/auth-smtp)
- [Redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls)
- [Email Templates](https://supabase.com/docs/guides/auth/auth-email-templates)

---

## 🚨 Problèmes Courants

### "Email rate limit exceeded"
**Cause**: Supabase limite à 3 emails/heure en tier gratuit
**Solution**: Passer à tier payant ou attendre 1h

### "Invalid redirect URL"
**Cause**: URL callback non whitelistée
**Solution**: Ajouter URL dans Supabase Dashboard → Auth → Redirect URLs

### "Email not sent"
**Cause**: SMTP non configuré ou clés invalides
**Solution**: Vérifier config SMTP dans Supabase Dashboard

### "Session not found after callback"
**Cause**: Cookie policy ou redirect URL incorrect
**Solution**: Vérifier que domain callback = domain login

---

## 🎬 Prochaines Étapes

1. ✅ Créer fichiers `.env` avec vraies clés
2. ✅ Configurer Supabase Dashboard (Redirect URLs + SMTP)
3. ✅ Tester envoi magic link
4. ✅ Vérifier réception email
5. ✅ Tester callback et création session
6. ⚠️ Déployer en production avec variables d'environnement sécurisées
