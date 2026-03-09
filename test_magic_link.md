# Test du Magic Link - Guide Rapide

## 🚀 Étapes de Test

### 1. Vérifier la Configuration

```bash
# Vérifier que les fichiers .env existent
ls -la frontend/.env
ls -la backend/.env

# Vérifier que les variables sont chargées (frontend)
cd frontend
pnpm run dev
# Ouvrir http://localhost:5173 et vérifier la console:
# console.log(import.meta.env.VITE_SUPABASE_URL)
# Doit afficher votre URL Supabase, pas "undefined"
```

### 2. Tester l'Envoi du Magic Link

**Page**: [http://localhost:5173/login](http://localhost:5173/login)

1. Entrer votre email de test
2. Cliquer sur **Recevoir le lien de connexion**
3. **Attendu**:
   - ✅ Message de succès: "Email envoyé"
   - ✅ Texte: "Vérifiez votre boîte mail à [email]"
   - ✅ Email reçu dans les 30 secondes

**Si erreur**:
- Ouvrir DevTools (F12) → Console
- Copier le message d'erreur
- Vérifier les logs backend

### 3. Tester le Callback

1. Cliquer sur le lien dans l'email
2. **Attendu**:
   - ✅ Page `/auth/callback` s'ouvre
   - ✅ Spinner avec "Vérification de votre lien de connexion..."
   - ✅ Message de succès: "Connexion réussie"
   - ✅ Redirection automatique vers `/dashboard` (après 1-2 secondes)

**Si erreur "Lien invalide ou expiré"**:
- Vérifier que Redirect URLs sont configurées dans Supabase
- Vérifier que l'URL du lien = URL dans Redirect URLs
- Tester avec un nouveau lien (l'ancien peut expirer après 1h)

### 4. Vérifier la Session

Dans la console du navigateur (F12 → Console):

```javascript
// Test 1: Vérifier la session
const { data: session, error } = await supabase.auth.getSession();
console.log('Session:', session);
console.log('User:', session?.session?.user);
// Devrait afficher votre email

// Test 2: Vérifier le user
const { data: { user } } = await supabase.auth.getUser();
console.log('Current user:', user);
// Devrait afficher votre profil utilisateur

// Test 3: Vérifier le token
const { data: { session: currentSession } } = await supabase.auth.getSession();
console.log('Access token:', currentSession?.access_token);
// Devrait afficher un JWT token (commence par "eyJ...")
```

### 5. Test de Déconnexion

```javascript
// Dans la console navigateur
const { error } = await supabase.auth.signOut();
console.log('Signout error:', error);
// Devrait afficher null (pas d'erreur)

// Vérifier que la session est supprimée
const { data: session } = await supabase.auth.getSession();
console.log('Session after signout:', session);
// Devrait afficher null
```

---

## 🐛 Commandes de Debug

### Logs Backend

```bash
cd backend
uvicorn app.main:app --reload --log-level debug
# Surveiller les logs pour:
# - "sending_magic_link"
# - "magic_link_sent"
# - Erreurs Supabase
```

### Logs Supabase (Dashboard)

1. Supabase Dashboard → **Logs** → **Auth**
2. Filtrer par:
   - Type: `magic_link`
   - Timestamp: dernières minutes
3. Chercher:
   - ✅ Status: `success`
   - ❌ Erreurs SMTP

### Test SMTP Direct (Resend)

```bash
# Installer curl si nécessaire
curl -X POST 'https://api.resend.com/emails' \
  -H 'Authorization: Bearer re_your_api_key' \
  -H 'Content-Type: application/json' \
  -d '{
    "from": "noreply@email.radnoumane.com",
    "to": "test@example.com",
    "subject": "Test SMTP",
    "html": "<p>Test email from Resend</p>"
  }'

# Attendu: {"id":"..."}
# Si erreur: vérifier API key et domaine vérifié
```

---

## ✅ Checklist de Validation

Cocher après validation:

### Configuration
- [ ] `frontend/.env` existe avec clés Supabase
- [ ] `backend/.env` existe avec clés Resend
- [ ] Variables chargées (vérifier console navigateur)
- [ ] Services frontend + backend démarrés

### Supabase Dashboard
- [ ] SMTP configuré avec Resend
- [ ] Redirect URLs ajoutées (localhost:5173/auth/callback)
- [ ] Template email personnalisé
- [ ] Domaine email vérifié dans Resend

### Tests Fonctionnels
- [ ] Email magic link reçu
- [ ] Lien cliquable
- [ ] Callback réussit
- [ ] Redirection vers /dashboard
- [ ] Session créée
- [ ] Session persiste après refresh
- [ ] Déconnexion fonctionne

---

## 📝 Problèmes Courants et Solutions

| Symptôme | Cause Probable | Solution |
|----------|----------------|----------|
| "Email not sent" | SMTP non configuré | Vérifier Supabase Dashboard → Auth → SMTP |
| "Invalid redirect URL" | URL non whitelistée | Ajouter dans Supabase → Auth → URL Configuration |
| Variables `undefined` | .env non chargé | Vérifier fichier existe + redémarrer serveur |
| Email en spam | SPF/DKIM manquants | Configurer DNS dans Resend Dashboard |
| "Session not found" | Cookie bloqué | Désactiver bloqueurs de cookies |
| "Rate limit exceeded" | Trop d'envois | Attendre 1h ou utiliser SMTP custom |

---

## 📊 Métriques de Succès

Après validation complète, vous devriez avoir:

- ⚡ **Délai envoi email**: < 5 secondes
- ✅ **Taux de délivrabilité**: 100% (avec Resend)
- 🔐 **Session valide**: 1 heure (configurable)
- 🔄 **Refresh automatique**: Oui (Supabase le gère)

---

## 🎯 Prochaines Étapes

Une fois les tests validés:

1. **Documentation utilisateur**:
   - Ajouter FAQ sur "Comment se connecter"
   - Expliquer le magic link aux utilisateurs

2. **Monitoring production**:
   - Configurer alertes Resend pour bounces
   - Surveiller taux d'ouverture emails

3. **Optimisations**:
   - Personnaliser template email avec logo
   - Ajouter tracking emails (optionnel)
   - Configurer email de bienvenue après première connexion

---

**Dernière mise à jour**: 2026-03-05
**Statut**: Guide de test complet ✅
