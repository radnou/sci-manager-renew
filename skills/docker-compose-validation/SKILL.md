---
name: docker-compose-validation
description: Vérifier en lecture seule l'état de la stack Docker GererSCI (validité de la configuration Compose, services, santé, ports, volumes, réseau, logs, cohérence avec les .env.example). À utiliser depuis local-environment, ou pour diagnostiquer un conteneur unhealthy.
---

# Validation Docker Compose GererSCI

## Portée

Cette skill est en **lecture seule**. Elle diagnostique la configuration et l'état des services Docker, elle ne les modifie pas. Le reverse proxy de production est Caddy, géré en service systemd et versionné dans le dépôt `vps-infra`, hors de ce dépôt. `docker/nginx.conf` est du code mort : ne pas s'y référer. Ne jamais modifier un fichier Compose.

Les trois fichiers Compose du dépôt sont :

- `docker-compose.yml` -- stack principale. Services actifs : `backend` (port `127.0.0.1:18000:8000`, healthcheck `/health/live`, mémoire 512 M) et `frontend` (port `127.0.0.1:14173:4173`, dépend de `backend condition: service_healthy`, mémoire 256 M). Services inactifs : `matomo-db`, `matomo`, `uptime-kuma` en `profiles: ["disabled"]`. Volumes nommés : `backend_logs`, `matomo_db_data`, `matomo_data`, `uptime_kuma_data`. Réseaux : `internal`, `matomo`.
- `docker-compose.dev.yml` -- service `caddy_dev` uniquement (ports `127.0.0.1:8080:80` et `127.0.0.1:8443:443`). Redéfinit le réseau `internal` avec `name: gerersci_internal_dev`, ce qui renomme le réseau partagé lors d'une fusion des deux fichiers.
- `docker-compose.monitoring.yml` -- services `loki` (`grafana/loki:3.4.2`) et `grafana` (`grafana/grafana:11.6.0`, port `127.0.0.1:13000:3000`). Réseau `monitoring`, séparé de `internal`. `GRAFANA_ADMIN_PASSWORD` est obligatoire : la stack refuse de démarrer sans.

La stack Supabase n'est **pas** dans le Compose : elle tourne via `supabase start`, et ses conteneurs suivent la convention `supabase_*_sci-manager-renew`.

## Contrôles

| # | Contrôle | Commande | Attendu |
|---|---|---|---|
| 1 | Configuration Compose valide | `docker compose config -q` | Exit code 0, aucune sortie |
| 2 | Liste des services définis | `docker compose config --services` | `backend`, `frontend` (et les services disabled) |
| 3 | Services démarrés | `docker compose ps --format json \| jq -r '.[] \| "\(.Service)\t\(.State)\t\(.Health)"'` | `backend running healthy`, `frontend running healthy` |
| 4 | Détail santé d'un service | `docker inspect --format '{{json .State.Health}}' gerersci_backend \| jq .` | `Status: "healthy"`, `FailingStreak: 0` |
| 5 | Ports publiés | `docker compose ps --format json \| jq -r '.[] \| "\(.Service)\t\(.Publishers)"'` | Backend `127.0.0.1:18000`, Frontend `127.0.0.1:14173` |
| 6 | Dépendances | Inspecter `depends_on` dans `docker-compose.yml` | `frontend` dépend de `backend` avec `condition: service_healthy` |
| 7 | Erreurs de démarrage backend | `docker compose logs --tail=200 backend` | Aucune exception ni `Error` inattendue |
| 8 | Erreurs de démarrage frontend | `docker compose logs --tail=200 frontend` | Aucune erreur de build ou de serving |
| 9 | Logs Supabase | `docker logs --tail=100 supabase_db_sci-manager-renew` | Aucune erreur PostgreSQL 17 |
| 10 | Réseau entre services | `docker network inspect gerersci_internal \| jq '.[0].Containers'` | `gerersci_backend` et `gerersci_frontend` présents |
| 11 | Volumes persistants | `docker volume ls --filter name=gerersci` | `gerersci_backend_logs` présent |
| 12 | Migrations Supabase | `supabase migration list` | Toutes les migrations appliquées, aucune en attente |
| 13 | Cohérence `.env.example` | Comparer les noms de variables `${...}` du Compose aux noms dans `.env.example` | Aucune variable orpheline non documentée |

Pour le contrôle 13 : comparer les **noms** uniquement, jamais les valeurs. Variables utilisées dans `docker-compose.yml` et absentes de tous les `.env*.example` : `STRIPE_CABINET_PRICE_ID`, `STRIPE_CABINET_ANNUAL_PRICE_ID`, `ADMIN_SECRET_KEY`, `MAINTENANCE_MODE`, `BETA_PASSWORD`, `VITE_PLAUSIBLE_DOMAIN`, `VITE_PLAUSIBLE_SRC`, `VITE_PLAUSIBLE_API_HOST`, `VITE_ANALYTICS_REQUIRE_CONSENT`.

## Contrôle du défaut healthcheck / maintenance

**Défaut identifié :** `docker-compose.yml:65` sonde `/health/live`. `backend/app/main.py:580` (`maintenance_middleware`) n'exempte que `/api/v1/health` et `/api/v1/health/ready`, chemins qui n'existent pas : le router health est monté sans préfixe (`main.py:830`, `backend/app/api/v1/health.py:18`), les vrais chemins sont `/health`, `/health/live`, `/health/ready`, `/health/flags`. En mode maintenance, `/health/live` renvoie 503 et le conteneur `backend` passe `unhealthy` pendant toute la durée de la maintenance.

**Scénario de contrôle -- CONSTATER, NE PAS CORRIGER :**

1. Activer la maintenance : `./scripts/maintenance-on.sh`
2. Vérifier l'état : `docker compose ps` -- le service `backend` doit afficher `unhealthy`
3. Désactiver la maintenance : `./scripts/maintenance-off.sh`

Ce comportement est documenté et connu. Ne pas corriger dans le cadre de cette skill.

## Incohérences connues

| Emplacement | Incohérence |
|---|---|
| `docker-compose.yml:190` | IP `54.38.109.182` codée en dur pour `api.radnoumane.com` dans `extra_hosts` |
| `.github/workflows/deploy.yml:89` | Référence `docker-compose.caddy.yml`, fichier inexistant dans le dépôt |
| `docker-compose.yml` | Variables `STRIPE_CABINET_PRICE_ID`, `STRIPE_CABINET_ANNUAL_PRICE_ID`, `ADMIN_SECRET_KEY`, `MAINTENANCE_MODE`, `BETA_PASSWORD`, `VITE_PLAUSIBLE_DOMAIN`, `VITE_PLAUSIBLE_SRC`, `VITE_PLAUSIBLE_API_HOST`, `VITE_ANALYTICS_REQUIRE_CONSENT` absentes de tous les `.env*.example` |
| `docker-compose.dev.yml` | Redéfinit le réseau `internal` avec `name: gerersci_internal_dev`, risque de conflit si fusionné avec `docker-compose.yml` |

## Format de sortie

Toujours produire ce tableau en tête de rapport :

```
| Service  | État    | Santé   | Ports | Constat |
|----------|---------|---------|-------|---------|
| backend  | running | healthy | 18000 | ...     |
| frontend | running | healthy | 14173 | ...     |
```

Puis trois listes :

**Constats** : faits observés sans jugement (volumes présents, migrations appliquées, logs propres).

**Anomalies** : écarts par rapport à l'attendu (service unhealthy, port non publié, variable absente du `.env.example`).

**Actions suggérées (à exécuter par l'utilisateur)** : commandes concrètes avec contexte, sans les exécuter. Jamais de commande destructive sans confirmation explicite.

## Garde-fous

Avant toute commande destructive : afficher la commande exacte, la cible, l'impact, le risque et les données concernées, puis attendre l'accord explicite.

| Commande | Impact | Règle |
|---|---|---|
| `docker compose down -v` | Détruit les volumes, dont les données Supabase | Confirmation obligatoire |
| `docker volume rm` | Perte de données définitive | Confirmation obligatoire |
| `docker system prune` | Supprime des ressources partagées avec d'autres projets | Confirmation obligatoire |
| `docker compose build --no-cache` | Reconstruction complète, plusieurs minutes | Confirmation obligatoire |
| `docker compose down` | Arrête des services potentiellement utilisés par un autre processus | Confirmation obligatoire |
| `docker compose restart` | Interruption de service | Confirmation obligatoire |

Ne jamais afficher de valeur de variable d'environnement. Pour `docker compose config`, la sortie peut contenir des secrets résolus : n'utiliser que `docker compose config -q` (validation) et `docker compose config --services` (liste), jamais `docker compose config` complet.
