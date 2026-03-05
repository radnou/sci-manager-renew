# Guide de Configuration Supabase pour Magic Link

**Date**: 2026-03-05
**Objectif**: Configurer Supabase Auth + Resend pour activer l'authentification par magic link

---

## 📋 Prérequis

- [ ] Compte Supabase créé: [app.supabase.com](https://app.supabase.com)
- [ ] Projet Supabase créé (si nouveau) ou existant
- [ ] Compte Resend créé: [resend.com](https://resend.com)
- [ ] API Key Resend générée
- [ ] Domaine vérifié dans Resend (ex: scimanager.fr)

---

## 🔑 Étape 1: Récupérer les Clés Supabase

### 1.1 Se connecter à Supabase Dashboard

1. Aller sur [app.supabase.com](https://app.supabase.com)
2. Sélectionner votre projet **SCI Manager**
3. Aller dans **Settings** → **API**

### 1.2 Copier les clés

Vous verrez 4 informations importantes:

| Variable | Valeur Supabase | Utilisation |
|----------|----------------|-------------|
| `VITE_SUPABASE_URL` | Project URL | Frontend + Backend |
| `VITE_SUPABASE_ANON_KEY` | anon public | Frontend |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role | Backend uniquement |
| `SUPABASE_JWT_SECRET` | JWT Secret | Backend (vérification tokens) |

**Format Project URL**: `https://abcdefghijklmnop.supabase.co`

### 1.3 Remplir les fichiers .env

#### Frontend (`frontend/.env`):
```bash
VITE_SUPABASE_URL=https://abcdefghijklmnop.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Backend (`backend/.env`):
```bash
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=your-jwt-secret-from-api-settings
```

---

## 📧 Étape 2: Configurer SMTP avec Resend

### 2.1 Récupérer l'API Key Resend

1. Aller sur [resend.com/api-keys](https://resend.com/api-keys)
2. Cliquer sur **Create API Key**
3. Nom: `SCI Manager - Supabase Auth`
4. Permission: **Full Access** (ou **Sending Access** minimum)
5. Copier la clé (commence par `re_`)

⚠️ **Important**: La clé n'est affichée qu'une seule fois! Sauvegarder immédiatement.

### 2.2 Vérifier le domaine dans Resend

1. Aller sur [resend.com/domains](https://resend.com/domains)
2. Ajouter votre domaine: `scimanager.fr`
3. Configurer les DNS records (SPF, DKIM, DMARC)
4. Attendre la vérification (peut prendre 1-24h)

**Email expéditeur**: `noreply@scimanager.fr`

### 2.3 Configurer SMTP dans Supabase

1. Supabase Dashboard → **Project Settings** → **Auth**
2. Scroller jusqu'à **SMTP Settings**
3. Activer **Enable Custom SMTP**
4. Remplir les champs:

```
Sender name: SCI Manager
Sender email: noreply@scimanager.fr

Host: smtp.resend.com
Port: 587 (ou 465 pour SSL)
Username: resend
Password: re_your_resend_api_key_here

Minimum interval: 60 (secondes entre emails)
```

5. Cliquer sur **Save**

### 2.4 Tester l'envoi (optionnel)

Dans Supabase Dashboard → **Authentication** → **Users**:
1. Cliquer sur **Send magic link**
2. Entrer votre email de test
3. Vérifier la réception de l'email

---

## 🔗 Étape 3: Configurer les Redirect URLs

### 3.1 Ajouter les URLs autorisées

1. Supabase Dashboard → **Authentication** → **URL Configuration**
2. Dans **Redirect URLs**, ajouter:

**Développement**:
```
http://localhost:5173/auth/callback
http://127.0.0.1:5173/auth/callback
```

**Production** (quand déployé):
```
https://scimanager.fr/auth/callback
https://www.scimanager.fr/auth/callback
```

3. Dans **Site URL**, définir:
   - Dev: `http://localhost:5173`
   - Prod: `https://scimanager.fr`

4. Cliquer sur **Save**

### 3.2 Vérifier les wildcard (optionnel)

Si vous avez plusieurs environnements (staging, preview), vous pouvez utiliser:
```
https://*.vercel.app/auth/callback
```

⚠️ **Attention**: Les wildcards sont moins sécurisés, à utiliser uniquement en dev/staging.

---

## 📝 Étape 4: Personnaliser le Template Email

### 4.1 Accéder aux templates

1. Supabase Dashboard → **Authentication** → **Email Templates**
2. Sélectionner **Magic Link**

### 4.2 Modifier le template

Remplacer le template par défaut par:

```html
<h2>Connexion à SCI Manager</h2>

<p>Bonjour,</p>

<p>Vous avez demandé un lien de connexion sécurisé pour accéder à votre cockpit SCI.</p>

<p>
  <a href="{{ .ConfirmationURL }}"
     style="display: inline-block; padding: 12px 24px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 6px; font-weight: 600;">
    Se connecter à SCI Manager
  </a>
</p>

<p style="color: #64748b; font-size: 14px;">
  Ce lien est valide pendant 1 heure.<br>
  Si vous n'avez pas demandé cette connexion, ignorez cet email.
</p>

<hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;">

<p style="color: #94a3b8; font-size: 12px;">
  L'équipe SCI Manager<br>
  <a href="https://scimanager.fr" style="color: #2563eb;">scimanager.fr</a>
</p>
```

### 4.3 Variables disponibles

| Variable | Description |
|----------|-------------|
| `{{ .ConfirmationURL }}` | URL du magic link (obligatoire) |
| `{{ .Token }}` | Token seul (non recommandé) |
| `{{ .SiteURL }}` | URL de votre site |

### 4.4 Sauvegarder

Cliquer sur **Save** en bas du template.

---

## ✅ Étape 5: Tester le Flux Complet

### 5.1 Redémarrer les services

```bash
# Terminal 1 - Frontend
cd frontend
pnpm run dev

# Terminal 2 - Backend
cd backend
uvicorn app.main:app --reload
```

### 5.2 Tester depuis la page de login

1. Ouvrir [http://localhost:5173/login](http://localhost:5173/login)
2. Entrer votre email de test
3. Cliquer sur **Recevoir le lien de connexion**
4. Vérifier:
   - ✅ Message de succès affiché
   - ✅ Email reçu dans votre boîte mail
   - ✅ Lien cliquable dans l'email

### 5.3 Cliquer sur le magic link

Le lien devrait:
1. Ouvrir `/auth/callback`
2. Afficher "Vérification de votre lien de connexion..."
3. Créer la session automatiquement
4. Rediriger vers `/dashboard`

### 5.4 Vérifier la session

Dans la console du navigateur (F12):
```javascript
const { data: session } = await supabase.auth.getSession();
console.log('Session:', session);
// Devrait afficher: session.user avec votre email
```

---

## 🐛 Troubleshooting

### Problème 1: "Email not sent"

**Cause**: SMTP non configuré ou clé Resend invalide

**Solution**:
1. Vérifier que SMTP est activé dans Supabase
2. Vérifier la clé Resend (copier-coller sans espaces)
3. Vérifier que le domaine est vérifié dans Resend
4. Consulter les logs: Supabase Dashboard → Logs → Auth Logs

### Problème 2: "Email rate limit exceeded"

**Cause**: Supabase limite à 3 emails/heure en tier gratuit avec leur SMTP

**Solution**:
1. Configurer SMTP custom avec Resend (pas de limite)
2. OU passer au tier payant Supabase
3. OU attendre 1h entre les tests

### Problème 3: "Invalid redirect URL"

**Cause**: URL callback non whitelistée

**Solution**:
1. Vérifier que `http://localhost:5173/auth/callback` est dans Redirect URLs
2. Vérifier l'URL exacte (pas de trailing slash)
3. Vérifier le protocole (http vs https)

### Problème 4: "Session not found after callback"

**Cause**: Cookie policy ou redirect URL incorrect

**Solution**:
1. Vérifier que le domaine callback = domaine login
2. Désactiver les bloqueurs de cookies (privacy extensions)
3. Vérifier les DevTools → Application → Cookies
4. Vérifier que `sb-access-token` est présent

### Problème 5: Email arrive dans spam

**Cause**: SPF/DKIM non configurés correctement

**Solution**:
1. Resend Dashboard → Domains → Vérifier DNS records
2. Configurer SPF, DKIM, DMARC correctement
3. Utiliser un domaine vérifié (pas @gmail.com)
4. Ajouter `noreply@` dans sender email

---

## 📊 Logs et Monitoring

### Logs Supabase

1. **Auth Logs**: Supabase Dashboard → Logs → Auth
   - Filtrer par `magic_link` pour voir les envois
   - Vérifier les erreurs SMTP
   - Voir les taux de succès

2. **Database Logs**: Si problèmes de session
   - Vérifier la table `auth.users`
   - Vérifier les refresh tokens

### Logs Resend

1. Resend Dashboard → [Emails](https://resend.com/emails)
2. Voir tous les emails envoyés
3. Statuts: Sent, Delivered, Bounced, Complained

### Logs Application

Backend logs (uvicorn):
```bash
cd backend
uvicorn app.main:app --reload --log-level debug
```

Frontend logs (console navigateur):
```javascript
// Activer debug Supabase
localStorage.setItem('supabase.auth.debug', 'true');
```

---

## 🔐 Sécurité - Checklist

Avant de passer en production:

- [ ] HTTPS activé (pas HTTP)
- [ ] Redirect URLs limitées aux domaines de prod
- [ ] Service Role Key jamais exposée au frontend
- [ ] JWT Secret gardé confidentiel
- [ ] CORS configuré avec origines spécifiques (pas `*`)
- [ ] Rate limiting activé (Supabase auto, mais vérifier)
- [ ] Logs monitorés régulièrement
- [ ] RGPD: politique de confidentialité + mentions légales
- [ ] SPF/DKIM/DMARC configurés pour domaine email

---

## 📚 Ressources

- [Documentation Supabase Auth](https://supabase.com/docs/guides/auth)
- [Magic Link Guide](https://supabase.com/docs/guides/auth/auth-email)
- [SMTP Configuration](https://supabase.com/docs/guides/auth/auth-smtp)
- [Resend Documentation](https://resend.com/docs/introduction)
- [Email Best Practices](https://resend.com/docs/knowledge-base/deliverability)

---

## ✅ Checklist Finale

Avant de considérer la configuration terminée:

### Configuration
- [ ] Fichier `frontend/.env` créé avec clés Supabase
- [ ] Fichier `backend/.env` créé avec toutes les variables
- [ ] SMTP Resend configuré dans Supabase Dashboard
- [ ] Domaine vérifié dans Resend
- [ ] Redirect URLs ajoutées dans Supabase
- [ ] Template email personnalisé
- [ ] Services redémarrés

### Tests
- [ ] Email magic link reçu
- [ ] Clic sur lien → redirection `/auth/callback`
- [ ] Session créée automatiquement
- [ ] Redirection vers `/dashboard`
- [ ] Session persiste après refresh page
- [ ] Logs Supabase sans erreurs
- [ ] Logs Resend montrent "Delivered"

### Production
- [ ] Variables d'environnement prod configurées
- [ ] Redirect URLs prod ajoutées
- [ ] HTTPS activé
- [ ] Monitoring configuré
- [ ] Politique RGPD en place

---

**Statut**: Configuration complète ✅
**Prochaine étape**: Tester en production avec vrais utilisateurs
