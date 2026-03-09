# Deployment Checklist - GererSCI

## Pré-Déploiement

### Code Quality
- [ ] Tous les tests passent (`pytest --cov=app`)
- [ ] Coverage ≥ 80% sur les modules critiques
- [ ] Aucune alerte de sécurité (`bandit -r app`)
- [ ] Linting passé (`ruff check app`)
- [ ] Type checking passé (`mypy app`)

### Configuration
- [ ] Variables d'environnement validées (voir `app/core/config.py`)
- [ ] APP_ENV défini correctement (staging ou production)
- [ ] DEBUG=false en production
- [ ] LOG_LEVEL=WARNING en production
- [ ] LOG_FORMAT=json en production
- [ ] CORS_ORIGINS ne contient pas localhost en production
- [ ] Secrets récupérés depuis AWS Secrets Manager

### Base de Données
- [ ] Migrations Supabase appliquées
- [ ] RLS policies activées sur toutes les tables
- [ ] Backups automatiques configurés
- [ ] Indexes créés pour les requêtes fréquentes

### Services Externes
- [ ] Stripe en mode live (sk_live_)
- [ ] Webhooks Stripe configurés et testés
- [ ] Resend configuré avec domaine vérifié
- [ ] Supabase Storage buckets créés
- [ ] Supabase Auth configuré

## Déploiement

### Infrastructure
- [ ] Docker images buildées et taguées
- [ ] Images pushées vers registry (AWS ECR)
- [ ] Secrets chargés dans environnement
- [ ] Reverse proxy (nginx) configuré
- [ ] SSL/TLS certificates valides
- [ ] Firewall rules configurées

### Application
- [ ] Backend déployé sur serveur
- [ ] Frontend déployé (Vercel ou serveur)
- [ ] Health checks fonctionnels (`/health/live`, `/health/ready`)
- [ ] Docker health checks configurés
- [ ] Graceful shutdown testé (SIGTERM)

### Monitoring
- [ ] Logs centralisés (CloudWatch ou similaire)
- [ ] Métriques système configurées
- [ ] Alertes configurées (erreurs 5xx, latence, downtime)
- [ ] Status page configuré

## Post-Déploiement

### Validation Technique
- [ ] `/health/live` retourne 200
- [ ] `/health/ready` retourne 200
- [ ] Tous les endpoints API testés manuellement
- [ ] Tests E2E en staging passés
- [ ] Performance tests (load testing) passés
- [ ] Aucune erreur dans les logs

### Validation Fonctionnelle
- [ ] Magic link login fonctionne
- [ ] Création de bien fonctionne
- [ ] Création de loyer fonctionne
- [ ] Génération de quittance fonctionne
- [ ] Export CERFA 2044 fonctionne
- [ ] Stripe checkout fonctionne
- [ ] Webhooks Stripe fonctionnent

### Sécurité
- [ ] Headers de sécurité présents (HSTS, CSP, X-Frame-Options)
- [ ] Rate limiting actif
- [ ] CORS configuré correctement
- [ ] Aucun secret exposé dans les logs
- [ ] Scan de vulnérabilités passé

## Rollback Plan

### Si Problème Détecté
1. **Immédiat**: Arrêter le traffic vers la nouvelle version
2. **5 minutes**: Rollback vers version précédente
3. **10 minutes**: Vérifier que le rollback fonctionne
4. **Post-mortem**: Analyser la cause et documenter

### Commandes Rollback
```bash
# Docker Compose
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
curl https://api.gerersci.fr/health/live
curl https://api.gerersci.fr/health/ready

# Login
curl -X POST https://api.gerersci.fr/api/v1/auth/magic-link/send \
  -H "Content-Type: application/json" \
  -d '{"email": "test@gerersci.fr"}'

# Metrics
curl https://api.gerersci.fr/health/ready | jq '.checks'
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
