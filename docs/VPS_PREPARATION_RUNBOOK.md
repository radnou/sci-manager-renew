# Runbook VPS GererSCI (Preparation SSH)

Date de reference: 2026-03-05

## 1. Objectif

Ce document prepare un VPS de production pour GererSCI afin de permettre une intervention distante SSH sans ambiguite.

Perimetre:
- Frontend SvelteKit (service systemd)
- Backend FastAPI (service systemd)
- Reverse proxy Nginx
- TLS Let's Encrypt (Certbot)
- Hardening de base (UFW + utilisateur non-root)

## 2. Etat actuel du repository (verifie)

Points importants constates dans le repo:
- Pas de fichier `docker-compose.yml`.
- Pas de `backend/requirements.txt` versionne.
- `frontend/Dockerfile` existe, mais backend Dockerfile absent.
- Config backend attend un fichier `.env` dans le dossier `backend`.

Conclusion: pour un deploiement robuste immediat, utiliser une architecture native VPS (`systemd + nginx`) au lieu d'un compose incomplet.

## 3. Sizing VPS recommande

Recommande (France):
- 4 vCPU
- 8 Go RAM
- 75 Go SSD
- Ubuntu 24.04 LTS

Minimum acceptable:
- 2 vCPU
- 4 Go RAM
- 40 Go SSD

## 4. Informations a fournir avant intervention SSH

### 4.1 Acces serveur

- IP publique du VPS
- Port SSH
- Utilisateur SSH (ex: `ubuntu`)
- Methode d'auth (cle privee)
- Confirmation que l'IP d'administration est autorisee

### 4.2 DNS

- Domaine principal: `gerersci.fr`
- Sous-domaines:
  - `app.gerersci.fr`
  - `api.gerersci.fr`

Enregistrements A requis:
- `@` -> IP VPS
- `app` -> IP VPS
- `api` -> IP VPS

### 4.3 Secrets applicatifs

Backend (`/opt/gerersci/app/backend/.env`):
- `APP_ENV=production`
- `DEBUG=false`
- `FRONTEND_URL=https://app.gerersci.fr`
- `CORS_ORIGINS=["https://app.gerersci.fr","https://gerersci.fr"]`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET`
- `STRIPE_SECRET_KEY` (live)
- `STRIPE_WEBHOOK_SECRET`
- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL=noreply@gerersci.fr`

Frontend (`/opt/gerersci/app/frontend/.env`):
- `VITE_API_URL=https://api.gerersci.fr`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_STRIPE_PUBLISHABLE_KEY`

## 5. Preparation serveur (OS)

### 5.1 Mises a jour et paquets

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y nginx ufw fail2ban certbot python3-certbot-nginx git curl jq
sudo apt install -y python3.12 python3.12-venv python3-pip
```

Node.js LTS (22.x):

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node -v
npm -v
```

### 5.2 Utilisateur d'exploitation

```bash
sudo adduser --disabled-password --gecos "" gerersci
sudo usermod -aG sudo gerersci
sudo mkdir -p /opt/gerersci
sudo chown -R gerersci:gerersci /opt/gerersci
```

### 5.3 Firewall

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status verbose
```

## 6. Deployment applicatif

### 6.1 Checkout code

```bash
sudo -u gerersci -H bash -lc '
cd /opt/gerersci
git clone <REPO_URL> app
cd app
git checkout <BRANCH_OR_TAG>
'
```

### 6.2 Backend (venv + dependances)

Si `backend/requirements.txt` est absent, installer le socle minimal:

```bash
sudo -u gerersci -H bash -lc '
cd /opt/gerersci/app/backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
pip install \
  fastapi "uvicorn[standard]" pydantic pydantic-settings \
  "python-jose[cryptography]" supabase structlog stripe resend jinja2 \
  reportlab slowapi email-validator
'
```

Creer le fichier d'environnement backend:

```bash
sudo -u gerersci -H bash -lc 'nano /opt/gerersci/app/backend/.env'
```

### 6.3 Frontend (build production)

```bash
sudo -u gerersci -H bash -lc '
cd /opt/gerersci/app/frontend
npm ci
npm run build
'
```

Creer le fichier d'environnement frontend:

```bash
sudo -u gerersci -H bash -lc 'nano /opt/gerersci/app/frontend/.env'
```

## 7. Services systemd

### 7.1 Backend service

Fichier `/etc/systemd/system/gerersci-backend.service`:

```ini
[Unit]
Description=GererSCI Backend (FastAPI)
After=network.target

[Service]
User=gerersci
Group=gerersci
WorkingDirectory=/opt/gerersci/app/backend
EnvironmentFile=/opt/gerersci/app/backend/.env
ExecStart=/opt/gerersci/app/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 7.2 Frontend service

Fichier `/etc/systemd/system/gerersci-frontend.service`:

```ini
[Unit]
Description=GererSCI Frontend (SvelteKit)
After=network.target

[Service]
User=gerersci
Group=gerersci
WorkingDirectory=/opt/gerersci/app/frontend
EnvironmentFile=/opt/gerersci/app/frontend/.env
ExecStart=/usr/bin/npm run preview -- --host 127.0.0.1 --port 4173
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 7.3 Activation

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gerersci-backend gerersci-frontend
sudo systemctl status gerersci-backend --no-pager
sudo systemctl status gerersci-frontend --no-pager
```

## 8. Nginx reverse proxy

Fichier `/etc/nginx/sites-available/gerersci.conf`:

```nginx
server {
    listen 80;
    server_name gerersci.fr app.gerersci.fr;

    location / {
        proxy_pass http://127.0.0.1:4173;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

server {
    listen 80;
    server_name api.gerersci.fr;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Activation:

```bash
sudo ln -sf /etc/nginx/sites-available/gerersci.conf /etc/nginx/sites-enabled/gerersci.conf
sudo nginx -t
sudo systemctl reload nginx
```

## 9. TLS (Let's Encrypt)

```bash
sudo certbot --nginx -d gerersci.fr -d app.gerersci.fr -d api.gerersci.fr
sudo certbot renew --dry-run
```

## 10. Verification complete

### 10.1 Local VPS

```bash
curl -f http://127.0.0.1:8000/health
curl -f http://127.0.0.1:8000/health/live
curl -f http://127.0.0.1:8000/health/ready
curl -I http://127.0.0.1:4173
```

### 10.2 Externe

```bash
curl -I https://app.gerersci.fr
curl -f https://api.gerersci.fr/health/live
curl -f https://api.gerersci.fr/health/ready
```

### 10.3 Logs

```bash
sudo journalctl -u gerersci-backend -n 200 --no-pager
sudo journalctl -u gerersci-frontend -n 200 --no-pager
sudo tail -n 200 /var/log/nginx/error.log
```

## 11. Procedure de mise a jour

```bash
sudo -u gerersci -H bash -lc '
cd /opt/gerersci/app
git fetch --all
git checkout <BRANCH_OR_TAG>
git pull
'

sudo -u gerersci -H bash -lc '
cd /opt/gerersci/app/frontend
npm ci
npm run build
'

sudo -u gerersci -H bash -lc '
cd /opt/gerersci/app/backend
source .venv/bin/activate
pip install --upgrade pip
'

sudo systemctl restart gerersci-backend gerersci-frontend
sudo systemctl status gerersci-backend gerersci-frontend --no-pager
```

## 12. Blocages frequents

- DNS non propage -> Certbot echoue.
- CORS production mal regle -> appels frontend bloques.
- Cle Stripe test en production -> readiness a 503.
- Service role Supabase invalide -> endpoints metier en erreur.
- Port 4173 ou 8000 deja occupe -> service systemd KO.

## 13. Dossier a transmettre avant execution SSH par Codex

Checklist minimale:
- [ ] IP serveur, port SSH, utilisateur
- [ ] Cle privee SSH (ou methode d'acces)
- [ ] Domaine et DNS A records configures
- [ ] Secrets backend complets
- [ ] Variables frontend completes
- [ ] Branch/tag Git cible

Une fois ces elements fournis, l'intervention SSH peut etre executee de bout en bout.
