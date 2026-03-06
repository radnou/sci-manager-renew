# VPS Preparation Runbook - GererSCI (Production France)

Date de reference: 2026-03-05

## 1) Purpose and success criteria

Ce runbook prepare une execution distante SSH de niveau production pour GererSCI.

Succes =
- application disponible en HTTPS sur `app.gerersci.fr`,
- API disponible en HTTPS sur `api.gerersci.fr`,
- checks de sante backend au vert,
- securite de base activee (SSH durci, firewall, TLS, non-root runtime),
- procedure rollback testable en moins de 15 minutes.

## 2) Scope

In scope:
- preparation OS,
- durcissement acces serveur,
- deployment frontend + backend en `systemd`,
- Nginx reverse proxy,
- certificats Let's Encrypt,
- verification go-live,
- plan rollback et support post-go-live.

Out of scope:
- migration cloud multi-region,
- SOC 2 complet,
- DR actif-actif,
- bastion enterprise centralise.

## 3) Current repository constraints (verified)

Constats de structure:
- pas de `docker-compose.yml` versionne,
- pas de `backend/requirements.txt` versionne,
- backend lit les variables via `backend/.env`,
- frontend est exploitable via `npm run build` + `npm run preview`.

Decision d'architecture recommandee:
- deployment natif VPS (`systemd + nginx`) pour minimiser risque et delai.

## 4) Operating model (consulting governance)

## 4.1 RACI simplifie

| Activite | Accountable | Responsible | Consulted | Informed |
|---|---|---|---|---|
| Validation architecture cible | CTO/Founder | Tech Lead | Security advisor | Product |
| Preparation serveur | Tech Lead | Ops engineer | Security advisor | Founder |
| Configuration secrets | Founder | Tech Lead | Security advisor | Ops |
| Go/No-Go production | Founder | Tech Lead | Product, Security | Stakeholders |
| Suivi incident post-go-live | Tech Lead | Ops engineer | Founder | Product |

## 4.2 Gates de decision

Gate 1 - Pre-flight:
- DNS configure,
- secrets complets,
- acces SSH valide,
- fenetre de deploiement validee.

Gate 2 - Pre-go-live:
- services locaux en RUN,
- Nginx configuration valide,
- certificats TLS emis,
- health checks internes OK.

Gate 3 - Go-live:
- health checks externes OK,
- aucune erreur bloquante logs,
- rollback plan confirme.

## 5) Infrastructure target

## 5.1 Sizing VPS

Recommande:
- 4 vCPU,
- 8 Go RAM,
- 75 Go SSD,
- Ubuntu 24.04 LTS.

Minimum:
- 2 vCPU,
- 4 Go RAM,
- 40 Go SSD.

## 5.2 Naming and domains

Domaine principal: `gerersci.fr`

Sous-domaines:
- `app.gerersci.fr` -> frontend,
- `api.gerersci.fr` -> backend.

DNS A records:
- `@` -> IP VPS,
- `app` -> IP VPS,
- `api` -> IP VPS.

## 6) Required inputs before SSH execution

## 6.1 Server access

- IP publique VPS,
- port SSH,
- utilisateur SSH (`ubuntu`/`debian`/autre),
- methode auth (cle privee recommandee),
- confirmation allowlist IP administration.

## 6.2 Git and release target

- URL repository,
- branche/tag deploiement,
- hash commit cible (si release figee).

## 6.3 Application secrets

Backend file: `/opt/gerersci/app/backend/.env`

Minimum attendu:
- `APP_ENV=production`
- `DEBUG=false`
- `FRONTEND_URL=https://app.gerersci.fr`
- `CORS_ORIGINS=["https://app.gerersci.fr","https://gerersci.fr"]`
- `SUPABASE_URL=<value>`
- `SUPABASE_ANON_KEY=<value>`
- `SUPABASE_SERVICE_ROLE_KEY=<value>`
- `SUPABASE_JWT_SECRET=<value>`
- `STRIPE_SECRET_KEY=<sk_live_...>`
- `STRIPE_WEBHOOK_SECRET=<whsec_...>`
- `RESEND_API_KEY=<re_...>`
- `RESEND_FROM_EMAIL=noreply@gerersci.fr`

Frontend file: `/opt/gerersci/app/frontend/.env`

Minimum attendu:
- `VITE_API_URL=https://api.gerersci.fr`
- `VITE_SUPABASE_URL=<value>`
- `VITE_SUPABASE_ANON_KEY=<value>`
- `VITE_STRIPE_PUBLISHABLE_KEY=<pk_live_...>`
- `PUBLIC_FEATURE_MULTI_SCI_DASHBOARD_V2=true`

## 7) Security baseline (minimum viable hardening)

Controles obligatoires:
- acces SSH par cle uniquement (desactiver mot de passe),
- utilisateur runtime non-root,
- UFW: seulement `22`, `80`, `443`,
- Fail2ban actif,
- TLS actif et renouvellement automatique,
- journaux systeme et Nginx consultables,
- variables secretes hors git.

## 8) Execution plan (step-by-step)

## 8.1 OS bootstrap

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y nginx ufw fail2ban certbot python3-certbot-nginx git curl jq
sudo apt install -y python3.12 python3.12-venv python3-pip
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node -v
npm -v
```

## 8.2 Runtime user and folders

```bash
sudo adduser --disabled-password --gecos "" gerersci
sudo usermod -aG sudo gerersci
sudo mkdir -p /opt/gerersci
sudo chown -R gerersci:gerersci /opt/gerersci
```

## 8.3 Firewall and SSH policy

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status verbose
```

SSH hardening (a adapter selon politique):

```bash
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak
sudo sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl reload ssh
```

## 8.4 Code checkout

```bash
sudo -u gerersci -H bash -lc '
cd /opt/gerersci
git clone <REPO_URL> app
cd app
git checkout <BRANCH_OR_TAG>
'
```

## 8.5 Backend setup

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

Create backend env:

```bash
sudo -u gerersci -H bash -lc 'nano /opt/gerersci/app/backend/.env'
```

## 8.6 Frontend setup

```bash
sudo -u gerersci -H bash -lc '
cd /opt/gerersci/app/frontend
npm ci
npm run build
'
```

Create frontend env:

```bash
sudo -u gerersci -H bash -lc 'nano /opt/gerersci/app/frontend/.env'
```

## 8.7 systemd services

Backend service `/etc/systemd/system/gerersci-backend.service`:

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

Frontend service `/etc/systemd/system/gerersci-frontend.service`:

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

Enable/start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gerersci-backend gerersci-frontend
sudo systemctl status gerersci-backend --no-pager
sudo systemctl status gerersci-frontend --no-pager
```

## 8.8 Nginx reverse proxy

File `/etc/nginx/sites-available/gerersci.conf`:

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

Enable and reload:

```bash
sudo ln -sf /etc/nginx/sites-available/gerersci.conf /etc/nginx/sites-enabled/gerersci.conf
sudo nginx -t
sudo systemctl reload nginx
```

## 8.9 TLS certificates

```bash
sudo certbot --nginx -d gerersci.fr -d app.gerersci.fr -d api.gerersci.fr
sudo certbot renew --dry-run
```

## 9) Validation plan

## 9.1 Internal checks

```bash
curl -f http://127.0.0.1:8000/health
curl -f http://127.0.0.1:8000/health/live
curl -f http://127.0.0.1:8000/health/ready
curl -I http://127.0.0.1:4173
```

## 9.2 External checks

```bash
curl -I https://app.gerersci.fr
curl -f https://api.gerersci.fr/health/live
curl -f https://api.gerersci.fr/health/ready
```

## 9.3 Logs and diagnostics

```bash
sudo journalctl -u gerersci-backend -n 200 --no-pager
sudo journalctl -u gerersci-frontend -n 200 --no-pager
sudo tail -n 200 /var/log/nginx/error.log
```

Go/No-Go criteria:
- 100% checks above green,
- zero error critique repetee dans logs,
- readiness backend `200` stable.

## 10) Rollback plan (15-minute target)

Scenario rollback standard:

```bash
sudo -u gerersci -H bash -lc '
cd /opt/gerersci/app
git checkout <PREVIOUS_STABLE_TAG_OR_COMMIT>
'

sudo -u gerersci -H bash -lc '
cd /opt/gerersci/app/frontend
npm ci
npm run build
'

sudo systemctl restart gerersci-backend gerersci-frontend
sudo systemctl status gerersci-backend gerersci-frontend --no-pager
```

Validation rollback:
- health endpoints OK,
- page app chargee,
- erreurs critiques absentes logs.

## 11) Update procedure (standard release)

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
```

## 12) Common failure modes and mitigations

| Failure mode | Detection | Mitigation |
|---|---|---|
| DNS non propage | certbot echoue | verifier A records, TTL, propagation |
| CORS mal regle | erreurs navigateur | corriger `CORS_ORIGINS` backend |
| Stripe test key en prod | `/health/ready` KO | injecter `sk_live` + restart |
| Port occupe | service failed | `ss -ltnp` puis ajustement service |
| Secret invalide Supabase | erreurs API metier | corriger `.env` et redemarrer |

## 13) Deliverables package before remote SSH

Checklist minimale:
- [ ] IP serveur, port SSH, user,
- [ ] acces cle privee valide,
- [ ] DNS pointe vers VPS,
- [ ] secrets backend/frontend complets,
- [ ] branche ou tag release,
- [ ] fenetre de deploiement validee,
- [ ] contact de decision Go/No-Go disponible.

Quand ce package est complet, l'intervention SSH peut etre executee de bout en bout avec un risque controle.
