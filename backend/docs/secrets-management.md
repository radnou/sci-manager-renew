# Secrets Management - GererSCI

## ⚠️ Règles de Sécurité

### ❌ NE JAMAIS
- Commiter des secrets dans git (.env avec vraies valeurs)
- Hardcoder des secrets dans le code
- Partager des secrets par email/Slack
- Utiliser des secrets de dev en production
- Laisser des secrets en plaintext sur le serveur

### ✅ TOUJOURS
- Utiliser un vault (AWS Secrets Manager, HashiCorp Vault)
- Séparer les secrets par environnement (dev/staging/prod)
- Rotate les secrets régulièrement (tous les 90 jours)
- Limiter les permissions d'accès aux secrets
- Auditer l'accès aux secrets

## Environnements

### Development
**Fichier**: `.env.development`
**Commité**: ✅ Oui (valeurs de test locales uniquement)
**Secrets**: Fakes ou test mode (Stripe sk_test_, etc.)

### Staging
**Fichier**: `.env.staging` (créé depuis `.env.staging.example`)
**Commité**: ❌ Non (ignoré par .gitignore)
**Secrets**: Depuis AWS Secrets Manager staging
**Vault Path**: `gerersci/staging/*`

### Production
**Fichier**: `.env.production` (créé depuis `.env.production.example`)
**Commité**: ❌ Non (ignoré par .gitignore)
**Secrets**: Depuis AWS Secrets Manager production
**Vault Path**: `gerersci/production/*`

## Configuration par Environnement

### Development (Local)
```bash
APP_ENV=development
DEBUG=false
LOG_LEVEL=DEBUG
LOG_FORMAT=console

# Supabase (utiliser l'instance locale ou un projet de test)
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Stripe (mode test)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Resend (API key de test)
RESEND_API_KEY=re_...

# CORS
CORS_ORIGINS=["http://localhost:5173"]
FRONTEND_URL=http://localhost:5173
```

### Staging
```bash
APP_ENV=staging
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json

# Secrets loaded from AWS Secrets Manager
# See scripts/load_secrets.sh
```

### Production
```bash
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING
LOG_FORMAT=json

# Secrets loaded from AWS Secrets Manager
# See scripts/load_secrets.sh
```

## AWS Secrets Manager Setup

### 1. Créer les secrets

```bash
# Staging
aws secretsmanager create-secret \
    --name gerersci/staging/supabase-service-role-key \
    --secret-string "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
    --region eu-west-3

aws secretsmanager create-secret \
    --name gerersci/staging/stripe-secret-key \
    --secret-string "sk_test_..." \
    --region eu-west-3

# Production
aws secretsmanager create-secret \
    --name gerersci/staging/supabase-service-role-key \
    --secret-string "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
    --region eu-west-3

aws secretsmanager create-secret \
    --name gerersci/production/stripe-secret-key \
    --secret-string "sk_live_..." \
    --region eu-west-3
```

### 2. Récupération des secrets

Lors du déploiement, les secrets sont chargés automatiquement depuis AWS Secrets Manager et injectés comme variables d'environnement dans les conteneurs Docker.

## Rotation des Secrets

### Fréquence recommandée
- **Stripe**: Tous les 90 jours ou après changement de personnel
- **Supabase**: Tous les 90 jours
- **Resend**: Tous les 180 jours
- **JWT Secret**: Une fois par an (nécessite re-login des users)

### Procédure de rotation

1. Créer le nouveau secret dans AWS Secrets Manager
2. Tester avec l'ancien ET le nouveau secret en parallel
3. Déployer avec le nouveau secret
4. Invalider l'ancien secret après 24h

## Audit et Monitoring

### CloudWatch Logs
- Tous les accès aux secrets sont loggués
- Alertes configurées pour les accès suspects

### Checklist mensuelle
- [ ] Vérifier les logs d'accès aux secrets
- [ ] Vérifier qu'aucun secret n'est exposé dans les logs applicatifs
- [ ] Vérifier la rotation schedule
- [ ] Vérifier les permissions IAM

## Troubleshooting

### Erreur: Secret not found
```bash
# Vérifier que le secret existe
aws secretsmanager list-secrets --region eu-west-3 | grep gerersci

# Vérifier les permissions IAM
aws secretsmanager describe-secret --secret-id gerersci/production/stripe-secret-key
```

### Erreur: Access Denied
```bash
# Vérifier la policy IAM attachée au role EC2/ECS
aws iam get-role-policy --role-name gerersci-backend --policy-name SecretsManagerAccess
```
