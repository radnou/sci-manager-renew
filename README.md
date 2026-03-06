# 🚀 SCI-Manager - Déploiement Production

Guide complet pour déployer SCI-Manager sur un VPS Scaleway en production.

## 📋 Prérequis

- **VPS Scaleway** : Ubuntu 22.04 LTS (minimum 2GB RAM, 1 vCPU)
- **Domaine** : Configuré avec DNS pointant vers l'IP de votre VPS
- **Clés API** :
  - Stripe (clés de production)
  - Supabase (instance de production)
  - Resend (pour les emails)

## 🏗️ Architecture de Production

```
Internet → Nginx (SSL/TLS) → Frontend (SvelteKit)
                           → Backend (FastAPI)
                           → Database (PostgreSQL)
```

## 🚀 Déploiement Automatique

### 1. Préparation du VPS

```bash
# Connectez-vous à votre VPS
ssh root@your-vps-ip

# Mettez à jour le système
sudo apt update && sudo apt upgrade -y

# Installez Git
sudo apt install -y git
```

### 2. Clone du Repository

```bash
# Clonez le repository
git clone https://github.com/your-username/sci-manager-renew.git
cd sci-manager-renew

# Rendez le script de déploiement exécutable
chmod +x deploy.sh
```

### 3. Configuration de l'Environnement

```bash
# Copiez le template de production
cp .env.production .env

# Éditez le fichier .env avec vos vraies valeurs
nano .env
```

**Variables importantes à configurer :**
```env
DOMAIN=your-domain.com
DATABASE_PASSWORD=your_secure_password
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_prod_anon_key
STRIPE_SECRET_KEY=sk_live_your_key
# ... toutes les autres variables
```

### 4. Lancement du Déploiement

```bash
# Lancez le déploiement automatique
./deploy.sh
```

Le script va :
- ✅ Installer Docker et Docker Compose
- ✅ Configurer le firewall (UFW)
- ✅ Créer les répertoires nécessaires
- ✅ Construire et démarrer les services
- ✅ Installer Certbot pour SSL

## 🔒 Configuration SSL (Let's Encrypt)

Après le déploiement initial :

```bash
# 1. Vérifiez que votre domaine pointe vers le VPS
ping your-domain.com

# 2. Obtenez le certificat SSL
sudo certbot certonly --standalone -d your-domain.com

# 3. Copiez les certificats
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem docker/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem docker/ssl/

# 4. Redémarrez Nginx
docker compose restart nginx
```

## 🔧 Configuration DNS

Assurez-vous que votre domaine pointe vers l'IP de votre VPS :

```
Type: A
Name: @
Value: YOUR_VPS_IP
TTL: 300
```

## 📊 Monitoring et Maintenance

### Vérification des Services

```bash
# Status des conteneurs
docker compose ps

# Logs des services
docker compose logs backend
docker compose logs frontend
docker compose logs nginx

# Health check
curl https://your-domain.com/health
```

### Sauvegardes Automatiques

Le script de déploiement configure des sauvegardes automatiques :
- **Base de données** : Tous les jours à 2h du matin
- **SSL** : Renouvellement automatique tous les 3 mois

### Mise à Jour de l'Application

```bash
# Arrêtez les services
docker compose down

# Récupérez les dernières modifications
git pull origin main

# Redémarrez les services
docker compose up -d --build
```

## 🛠️ Dépannage

### Problème : Services ne démarrent pas

```bash
# Vérifiez les logs détaillés
docker compose logs

# Vérifiez les variables d'environnement
docker compose exec backend env | grep -E "(DATABASE|STRIPE|SUPABASE)"
```

### Problème : Erreur SSL

```bash
# Vérifiez les certificats
ls -la docker/ssl/

# Testez la configuration Nginx
docker compose exec nginx nginx -t
```

### Problème : Base de données inaccessible

```bash
# Vérifiez la santé de la DB
docker compose exec db pg_isready -U sci_manager -d sci_manager_prod

# Consultez les logs de la DB
docker compose logs db
```

## 🔐 Sécurité

### Firewall (UFW)
- ✅ SSH (22) : Autorisé
- ✅ HTTP (80) : Autorisé
- ✅ HTTPS (443) : Autorisé
- ❌ Tout le reste : Bloqué

### Headers de Sécurité
- ✅ X-Frame-Options
- ✅ X-Content-Type-Options
- ✅ Content-Security-Policy
- ✅ HTTPS forcé

### Rate Limiting
- API : 10 requêtes/seconde
- Général : 100 requêtes/seconde

## 📈 Performance

### Optimisations Appliquées
- ✅ Compression Gzip
- ✅ Cache des assets statiques (1 an)
- ✅ HTTP/2 activé
- ✅ Connection pooling

### Monitoring Recommandé
- **Uptime** : UptimeRobot ou Pingdom
- **Logs** : Loki + Promtail + Grafana
- **Métriques** : Prometheus + Node Exporter

## 💰 Coûts Scaleway

| Service | Configuration | Prix/mois |
|---------|---------------|-----------|
| VPS | GP1-XS (2GB RAM) | ~5€ |
| Domain | .com/.fr | ~10€/an |
| SSL | Let's Encrypt | Gratuit |
| **Total** | | **~5€/mois** |

## 🎯 Checklist Post-Déploiement

- [ ] Application accessible sur HTTPS
- [ ] Paiements Stripe fonctionnels
- [ ] Emails Resend opérationnels
- [ ] Authentification Supabase OK
- [ ] Base de données accessible
- [ ] SSL valide (A+ sur SSL Labs)
- [ ] Sauvegardes automatiques actives
- [ ] Monitoring configuré

## 📞 Support

En cas de problème :
1. Consultez les logs : `docker compose logs`
2. Vérifiez la configuration : `cat .env`
3. Testez les endpoints : `curl https://your-domain.com/health`

---

**🎉 Félicitations ! Votre SCI-Manager est maintenant en production !**
- offre Standard (jusqu'à 5 biens),
- offre Pro (multi-biens illimités),
- option onboarding / accompagnement premium.

## 6) Indicateurs de pilotage recommandés

- **North Star**: nombre de SCI actives avec au moins 1 loyer enregistré sur 30 jours.
- Activation: délai moyen entre création de compte et premier bien ajouté.
- Valeur: ratio biens actifs / loyers saisis.
- Rétention: cohortes mensuelles SCI actives.
- Monétisation: conversion freemium -> payant, ARPA, churn logo.

## 7) Stack technique

- Backend: FastAPI, Python 3.12
- Frontend: SvelteKit, TypeScript, Tailwind CSS
- Base de données: Supabase (PostgreSQL)
- Paiements: Stripe
- Outils: Docker, Playwright, Vitest, Storybook

## 8) Démarrage rapide local

```bash
# 1. Démarrer les dépendances locales
cd /workspaces/sci-manager-renew
docker-compose up -d

# 2. Configurer les variables d'environnement
cp .env.example .env

# 3. Lancer l'API
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# 4. Lancer le frontend
cd ../frontend
npm install
npm run dev -- --port 5173
```

- API: `http://localhost:8001`
- Frontend: `http://localhost:5173`

## 9) Qualité et tests

### Vérifications principales

```bash
cd frontend
npm run check
npm run build
npm run test:high-value -- --coverage
```

`test:high-value` applique une couverture sur les modules métier critiques avec les seuils suivants:
- lignes >= 85%
- fonctions >= 85%
- statements >= 85%
- branches >= 70%

### Gate global backend + frontend

```bash
bash scripts/quality-gate.sh
```

Ce script enchaîne:
- backend: `pytest --cov=backend/app --cov-fail-under=85`
- frontend: `npm --prefix frontend run test:high-value -- --coverage`

## 10) Documentation

- Vision & positionnement: [`docs/BUSINESS_FUNCTIONAL_OVERVIEW.md`](docs/BUSINESS_FUNCTIONAL_OVERVIEW.md)
- Parcours fonctionnels et exigences MVP: [`docs/FUNCTIONAL_REQUIREMENTS.md`](docs/FUNCTIONAL_REQUIREMENTS.md)
- Go-to-market & métriques: [`docs/GTM_AND_METRICS.md`](docs/GTM_AND_METRICS.md)
- Architecture technique: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- Audit de maturité: [`AUDIT_BIG4_2026-03-04.md`](AUDIT_BIG4_2026-03-04.md)

## 11) Skills et sub-agents projet

Le dossier [`skills/`](skills/) contient des skills internes pour standardiser les travaux orientés business/produit (documentation, backlog fonctionnel, stratégie go-to-market).
