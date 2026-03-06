# Deployment Checklist - GererSCI

## 1. Build Gate
- [ ] `bash scripts/quality-gate.sh` passe en local ou CI
- [ ] Backend coverage `>= 85%`
- [ ] Frontend high-value coverage `>= 85%`
- [ ] E2E critiques passent
- [ ] `bandit -r backend/app` ne remonte aucun blocant

## 2. Configuration & Secrets
- [ ] `APP_ENV=staging` ou `APP_ENV=production`
- [ ] `DEBUG=false`
- [ ] `LOG_FORMAT=json`
- [ ] `CORS_ORIGINS` ne contient aucun hôte local en production
- [ ] `ALLOWED_HOSTS` borne le domaine cible
- [ ] Tous les secrets proviennent d'une source dédiée et non d'un placeholder:
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `SUPABASE_JWT_SECRET`
  - `STRIPE_SECRET_KEY`
  - `STRIPE_WEBHOOK_SECRET`
  - `RESEND_API_KEY`
- [ ] Les templates `.env.development.example`, `.env.staging.example`, `.env.production.example` sont alignés avec la config effective

## 3. Stripe & Entitlements
- [ ] Les produits Stripe portent les metadata structurées:
  - `plan_key`
  - `billing_period`
  - `max_scis`
  - `max_biens`
  - `entitlements_version`
- [ ] Les prix live sont renseignés:
  - `STRIPE_STARTER_PRICE_ID`
  - `STRIPE_PRO_PRICE_ID`
  - `STRIPE_LIFETIME_PRICE_ID`
- [ ] `GET /api/v1/stripe/subscription` retourne l'offre attendue sur un compte de test
- [ ] Le checkout utilise `plan_key` côté frontend et le backend résout bien le `price_id`
- [ ] Les webhooks `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted` sont testés en environnement cible
- [ ] Les quotas sont cohérents avec la grille retenue:
  - `free`: 1 SCI / 1 bien
  - `starter`: 1 SCI / 5 biens
  - `pro`: 10 SCI / 20 biens
  - `lifetime`: illimité

## 4. Data & Migrations
- [ ] Toutes les migrations Supabase sont appliquées, y compris `004_subscription_entitlements.sql`
- [ ] Les colonnes `plan_key`, `max_scis`, `max_biens`, `features`, `is_active` existent sur `subscriptions`
- [ ] Les policies RLS sont actives sur les tables métiers
- [ ] Les sauvegardes de base et les exports de restauration sont validés

## 5. Runtime Hardening
- [ ] Les erreurs API retournent `error`, `code`, `request_id`
- [ ] Les logs structurés incluent `request_id`, `path`, `status_code`, `duration_ms`
- [ ] Les retries externes sont actifs sur les lectures idempotentes
- [ ] Les rate limits sont actifs sur auth, checkout, GDPR, fichiers et PDF
- [ ] Le graceful shutdown est testé avec `SIGTERM`
- [ ] Les feature flags sont explicitement décidés avant release:
  - `FEATURE_PLAN_ENTITLEMENTS_ENFORCEMENT`
  - `FEATURE_NEW_CHECKOUT_CATALOG`
  - `FEATURE_PDF_RENDER_DIRECT`
  - `FEATURE_MULTI_SCI_DASHBOARD_V2`

## 6. Health & Readiness
- [ ] `/health/live` retourne `200`
- [ ] `/health/ready` retourne `200` ou `503` selon l'état réel
- [ ] Le statut `degraded` est interprété par l'observabilité et n'est pas ignoré
- [ ] Les probes Docker/Kubernetes pointent vers `/health/live` et `/health/ready`

## 7. Smoke Tests Post-Deploy
- [ ] Envoi de magic link
- [ ] Consultation portefeuille SCI
- [ ] Création d'une SCI sur un compte Pro
- [ ] Blocage création SCI sur un compte Starter au-delà du quota
- [ ] Création d'un bien puis blocage au quota
- [ ] Génération et téléchargement PDF
- [ ] Checkout Stripe de bout en bout en mode test/live selon l'environnement

## 8. Rollback Readiness
- [ ] Version précédente identifiée
- [ ] Rollback documenté et testable sans migration destructrice
- [ ] Feature flags permettent de repasser en `warn` ou `observe` si l'enforcement doit être desserré

## Commandes utiles
```bash
bash scripts/quality-gate.sh

# Docker Compose rollback
docker compose down
git checkout <previous-commit>
docker compose up -d

# Avec tags
docker tag gerersci-backend:previous gerersci-backend:latest
docker compose up -d
```

## Checklist par Environnement

### Staging
- [ ] Utiliser les secrets de test (Stripe sk_test_)
- [ ] Activer DEBUG=false mais LOG_LEVEL=DEBUG
- [ ] Tester le déploiement complet
- [ ] Tester les migrations
- [ ] Tester les rollbacks

### Production
- [ ] ⚠️ CRITICAL: DEBUG=false, LOG_LEVEL=WARNING
- [ ] ⚠️ CRITICAL: Utiliser secrets live (Stripe sk_live_)
- [ ] ⚠️ CRITICAL: CORS production only
- [ ] Créer un backup avant déploiement
- [ ] Déployer pendant une fenêtre de maintenance annoncée
- [ ] Monitorer les logs pendant 1h après déploiement

## Validation Finale

### Tests Smoke (Production)
```bash
# Health checks
curl -f https://api.gerersci.fr/health/live
curl -f https://api.gerersci.fr/health/ready | jq

# Subscription check
curl -H "Authorization: Bearer <token>" https://api.gerersci.fr/api/v1/stripe/subscription | jq

# Login
curl -X POST https://api.gerersci.fr/api/v1/auth/magic-link/send \
  -H "Content-Type: application/json" \
  -d '{"email": "test@gerersci.fr"}'
```

### Monitoring Dashboard
- [ ] Ouvrir dashboard de monitoring
- [ ] Vérifier métriques système (CPU, RAM, Disk)
- [ ] Vérifier métriques applicatives (requests/s, latency, errors)
- [ ] Configurer alertes pour seuils critiques

## Documentation Post-Déploiement

- [ ] Mettre à jour CHANGELOG.md
- [ ] Documenter les changements de configuration
- [ ] Notifier l'équipe du déploiement réussi
- [ ] Archiver les logs du déploiement

## Contacts d'Urgence

- **DevOps**: [contact]
- **Backend Lead**: [contact]
- **Supabase Support**: support@supabase.com
- **Stripe Support**: support@stripe.com
