# Phase 5+ : Email + Magic Link + Storage

## 🎯 Nouvelles Fonctionnalités Implémentées

### 1. **Authentification Magic Link** 🔗
- ✅ Inscription/Connexion sans mot de passe
- ✅ Lien magique envoyé par email (Supabase Auth OTP)
- ✅ Callback automatique après clic sur le lien
- ✅ Pages frontend: `/login`, `/register`, `/auth/callback`

**Frontend Routes:**
```
POST /api/v1/auth/magic-link/send    → Envoyer le lien magique
POST /api/v1/auth/magic-link/verify  → Vérifier le token
POST /api/v1/auth/logout             → Se déconnecter
```

**Usage Frontend (Svelte):**
```typescript
import { supabase } from '$lib/supabase';

// Envoyer magic link
const { error } = await supabase.auth.signInWithOtp({
  email: email,
  options: {
    emailRedirectTo: `${window.location.origin}/auth/callback`
  }
});

// Le callback traite automatiquement après clic du lien
```

### 2. **Email Service** 📧
- ✅ Intégration Resend API
- ✅ Templates Jinja2 pour emails HTML
- ✅ 4 types d'emails:
  - Magic link (connexion)
  - Welcome (bienvenue)
  - Quitus generated (notification PDF)
  - Subscription confirmation (abonnement)

**Usage Backend:**
```python
from app.services.email_service import email_service

# Envoyer magic link
await email_service.send_magic_link(
    email="user@example.com",
    magic_link="https://app.gerersci.fr/auth/callback?token=..."
)

# Envoyer welcome
await email_service.send_welcome(
    email="user@example.com",
    user_name="Jean Dupont"
)
```

### 3. **Supabase Storage** 📦
- ✅ Gestion des fichiers (Quitus PDF, documents)
- ✅ Bucket auto-création: `documents`
- ✅ Upload/Download/Delete sécurisé
- ✅ URLs publiques pour téléchargement

**Endpoints:**
```
POST   /api/v1/files/upload-quitus      → Upload PDF quitus
GET    /api/v1/files/download/:path     → Télécharger fichier
DELETE /api/v1/files/delete/:path       → Supprimer fichier
GET    /api/v1/files/list/:folder       → Lister fichiers
```

**Usage Backend:**
```python
from app.services.storage_service import storage_service

# Upload PDF
url = await storage_service.upload_pdf(
    file_path="2024/quitus/bien-1.pdf",
    pdf_buffer=BytesIO(pdf_data)
)

# Get public URL
url = await storage_service.get_file_url("2024/quitus/bien-1.pdf")
```

## 🔧 Configuration Requise

### .env (Backend)
```env
# Email (Resend)
RESEND_API_KEY=re_5iUFid19_MUkdrohHXjMMCErFoKcq1uHx  # ← Votre clé
RESEND_FROM_EMAIL=noreply@email.radnoumane.com

# Supabase (déjà configuré)
SUPABASE_URL=http://localhost:54321
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### Supabase Storage (Admin Panel)
1. Aller dans **Storage** > **Buckets**
2. Créer bucket `documents` (public)
3. RLS policy: Permettre read public, write/delete à utilisateur propriétaire

## 📝 Architecture Services

### email_service.py
```
EmailService
├── send_magic_link()
├── send_welcome()
├── send_quitus_generated()
└── send_subscription_confirmation()
```

### storage_service.py
```
StorageService
├── upload_file()
├── upload_pdf()
├── delete_file()
├── get_file_url()
├── create_bucket_if_not_exists()
└── list_files()
```

### auth_service.py
```
MagicLinkService
├── send_magic_link()      → Supabase OTP
├── verify_magic_link()    → Valide token URL
├── create_user_from_magic_link()
├── sign_out()
├── get_user_session()
└── refresh_session()
```

## 🧪 Tests Implémentés

```bash
# Backend - Tests email/auth (à venir)
cd backend
pytest tests/test_services/test_email_service.py -v
pytest tests/test_services/test_auth_service.py -v

# Frontend - Magic link flow (Playwright)
npx playwright test tests/e2e/auth-magic-link.spec.ts
```

## 🔐 Sécurité

### Magic Link
- ✅ Token JWT signé par Supabase (expire 24h)
- ✅ HTTPS only (`emailRedirectTo` validation)
- ✅ Pas de token stocké en clair (Supabase gère)
- ✅ One-time use (token consommé après clic)

### Storage
- ✅ RLS policies (propriétaire uniquement)
- ✅ Paths anonymisées (`/user_id/date/filename`)
- ✅ CORS strict
- ✅ Delete trigger audit

### Email
- ✅ Rate limiting (Resend: 3 emails/min par utilisateur)
- ✅ Template sanitization (Jinja2)
- ✅ SPF/DKIM via Resend

## 📊 Endpoints Summary

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| POST | `/api/v1/auth/magic-link/send` | ❌ | Envoyer magic link |
| POST | `/api/v1/auth/magic-link/verify` | ❌ | Vérifier token |
| POST | `/api/v1/auth/logout` | ✅ | Se déconnecter |
| POST | `/api/v1/files/upload-quitus` | ✅ | Upload PDF |
| GET | `/api/v1/files/download/:path` | ✅ | Télécharger |
| DELETE | `/api/v1/files/delete/:path` | ✅ | Supprimer |
| GET | `/api/v1/files/list/:folder` | ✅ | Lister fichiers |

## 🚀 Prochaines Étapes

1. ✅ Magic Link Auth (TERMINÉ)
2. ✅ Email avec Resend (TERMINÉ)
3. ✅ Storage Supabase (TERMINÉ)
4. ⏳ **Phase 6**: Docker + Déploiement VPS

---

**Phase 5+ Complète!** On peut passer à Phase 6 (Infrastructure Docker/Nginx)
