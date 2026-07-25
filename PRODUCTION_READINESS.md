# Production Readiness Checklist — GérerSCI

Audit date: 2026-03-27

## Error Handling

| Item | Status | Details |
|------|--------|---------|
| Global exception handler (GererSCIException) | ✅ Done | `main.py:267-296` — structured JSON with request_id |
| RequestValidationError handler (422) | ✅ Done | `main.py:293-322` |
| PydanticValidationError handler | ✅ Done | `main.py:325-347` |
| Catch-all Exception handler | ✅ Done | `main.py:350-386` — hides details in prod |
| RateLimitExceeded handler | ✅ Done | `main.py:394` |
| No bare `except: pass` without logging | ✅ Fixed | stripe.py, gdpr.py — warning logs added |
| Stripe-specific error handling | ✅ Done | `stripe.error.StripeError` caught everywhere |
| Supabase error wrapping → DatabaseError | ✅ Done | Consistent pattern across routes |
| Non-blocking operations degrade gracefully | ✅ Done | Notifications, email, metadata tracking |
| Frontend error pages (+error.svelte) | ✅ Fixed | Root + (app) group — 404/402/403/500/503 |
| Frontend API error classes | ✅ Done | `api/client.ts` — typed hierarchy |
| Frontend Sentry integration | ✅ Done | `hooks.server.ts` + `hooks.client.ts` |

## Logging & Observability

| Item | Status | Details |
|------|--------|---------|
| Structured JSON logging | ✅ Done | structlog + JSONRenderer in prod |
| Request correlation IDs | ✅ Done | `main.py:471-478` — UUID per request |
| Request duration tracking | ✅ Done | `main.py:494-510` — duration_ms logged |
| Sentry error tracking | ✅ Done | `main.py:18-25` — 0.2 sample rate prod |
| Zero print() statements | ✅ Done | All replaced with structlog |
| Log levels configurable | ✅ Done | `LOG_LEVEL` env var |
| Console renderer for dev | ✅ Done | `log_format=console` for dev |

## Environment Configuration

| Item | Status | Details |
|------|--------|---------|
| Multi-env support (dev/staging/prod) | ✅ Done | `Environment` enum in config.py |
| Pydantic BaseSettings validation | ✅ Done | Type-checked, required fields |
| Placeholder secret detection | ✅ Done | Blocks startup if placeholders in prod |
| CORS lockdown in production | ✅ Done | Rejects localhost origins in prod |
| Debug disabled in production | ✅ Done | Enforced via validator |
| .env not in git | ✅ Done | .gitignore + symlinked on VPS |
| Env file load order | ✅ Done | `../.env`, `.env`, `.env.local` |

## Health Checks & Readiness

| Item | Status | Details |
|------|--------|---------|
| Liveness probe (`/health/live`) | ✅ Done | Simple alive check |
| Readiness probe (`/health/ready`) | ✅ Done | DB + Storage + Stripe + Resend |
| Database connectivity check | ✅ Done | Supabase API + raw socket fallback |
| Stripe configuration validation | ✅ Done | Price IDs verified active |
| Feature flags endpoint (`/health/flags`) | ✅ Fixed | Runtime flag visibility |
| Docker healthcheck | ✅ Done | 30s interval, 5 retries |
| Degraded vs unhealthy distinction | ✅ Done | Critical vs non-critical services |

## Graceful Shutdown

| Item | Status | Details |
|------|--------|---------|
| SIGTERM/SIGINT handlers | ✅ Done | `main.py:175-196` |
| 503 during shutdown for new requests | ✅ Done | `main.py:480-485` |
| Health endpoints available during shutdown | ✅ Done | Excluded from 503 |
| Background cron task cancellation | ✅ Done | `main.py:209-216` |
| Grace period for in-flight requests | ✅ Done | 30s (configurable) |
| LRU cache cleanup | ✅ Done | Supabase clients cleared |
| Docker stop_grace_period | ✅ Done | 30s + SIGTERM |

## Rate Limiting & Request Validation

| Item | Status | Details |
|------|--------|---------|
| Global default rate limit | ✅ Done | 100/minute per IP |
| Auth endpoints rate limited | ✅ Done | 3-5/minute |
| Stripe endpoints rate limited | ✅ Done | 2/day-30/minute by type |
| GDPR endpoints rate limited | ✅ Done | 3-10/hour |
| CRUD write endpoints rate limited | ✅ Fixed | 30/minute POST/PATCH, 5/minute DELETE |
| File upload rate limited | ✅ Done | 10/minute |
| Pydantic schema validation on all inputs | ✅ Done | Typed models everywhere |
| Email validation (EmailStr) | ✅ Done | Auth + leads |
| Field constraints (min/max/pattern) | ✅ Done | Postal codes, addresses, amounts |

## Retry Logic & External Service Resilience

| Item | Status | Details |
|------|--------|---------|
| Centralized retry with backoff | ✅ Done | `external_services.py` — exponential + jitter |
| Retryable error detection | ✅ Done | timeout, connection reset, rate limit, etc. |
| Email sends with retry | ✅ Done | All Resend calls via `run_with_retry()` |
| Storage operations with retry | ✅ Done | All Supabase Storage calls |
| Configurable retry attempts/delay | ✅ Done | `external_retry_attempts`, `base_delay_ms` |
| Stripe global timeout | ✅ Fixed | HTTPXClient with 10s timeout |
| Supabase client timeout | ✅ Fixed | postgrest + storage timeout from config |
| Stripe max_network_retries | ✅ Fixed | Set to 2 at startup |

## Database & Connection Management

| Item | Status | Details |
|------|--------|---------|
| Client caching (lru_cache) | ✅ Done | anon + service clients cached |
| Per-request user client (RLS) | ✅ Done | JWT injected per request |
| Postgrest timeout | ✅ Fixed | `supabase_request_timeout_seconds` applied |
| Storage timeout | ✅ Fixed | `storage_client_timeout` applied |
| Cache cleared on shutdown | ✅ Done | `cleanup_resources()` |

## Feature Flags

| Item | Status | Details |
|------|--------|---------|
| Boolean feature flags in config | ✅ Done | 6 flags in config.py |
| Enforcement modes (observe/warn/enforce) | ✅ Done | `feature_plan_entitlements_enforcement` |
| FeatureDisabledError exception | ✅ Done | Returns 403 with flag name |
| Runtime flag visibility endpoint | ✅ Fixed | `/health/flags` |
| Frontend feature flags | ✅ Done | `features.ts` with boolean parser |
| Maintenance mode | ✅ Done | Middleware blocks all non-health requests |
| Beta access bypass | ✅ Done | Cookie/header based |

## Security

| Item | Status | Details |
|------|--------|---------|
> ⚠️ **Ce tableau était partiellement faux.** Corrigé après l'audit externe du
> 2026-07-25, qui a reproduit un contournement complet du paiement en production.
> Référence : `AUDIT_EXTERNE_2026-07-25.md` · Suivi : `BACKLOG.md`.

| Item | Status | Details |
|------|--------|---------|
| JWT verification | ✅ Done | JWKS rotation with cache — vérifié, solide |
| RLS on all tables | ⚠️ Partiel | RLS active et **tient pour l'accès anonyme** (vérifié en prod). Mais policies d'écriture trop permissives sur `subscriptions` (C1) et `associes` (C3) → migration `043` corrige, **à déployer** |
| Supabase non exposé publiquement | ❌ **NON** | `api.gerersci.fr/rest/v1/` et `/auth/v1/` répondent 200 en prod (C2). RLS est donc la seule frontière réelle. À fermer dans `vps-infra` |
| Signup public désactivé | ❌ **NON** | `disable_signup:false` + `mailer_autoconfirm:true` → compte confirmé instantanément (HIGH-1) |
| CORS properly configured | ✅ Done | Origine étrangère rejetée — vérifié en prod |
| Security headers (CSP, HSTS, etc.) | ✅ Done | Posés par **Caddy**, vérifiés en prod (CSP, HSTS preload, X-Frame-Options) |
| API docs privées en prod | ❌ **NON** | `/docs`, `/redoc`, `/openapi.json` publics — 147 endpoints exposés (HIGH-2) |
| TrustedHostMiddleware | ✅ Done | — |
| Admin secret-key auth | ⚠️ Partiel | `hmac.compare_digest`, fail-closed — mais pas de rate-limit dédié ni MFA (MED-22) |
| No secrets in error responses | ⚠️ Partiel | OK sur le handler global, mais 7 `detail=str(e)` exposent l'exception Python (HIGH-13) |
| Webhook signature verification | ✅ Done | Signature + idempotence `UNIQUE(event_id)` |
| Pas de manipulation de prix au checkout | ✅ Done | `price_id` résolu serveur depuis un `plan_key` enum |

## Infrastructure

| Item | Status | Details |
|------|--------|---------|
| Docker Compose with healthchecks | ⚠️ Partiel | OK backend/frontend ; matomo, matomo-db, uptime-kuma sans limite mémoire ni rotation de logs |
| Deploy guard (no localhost in prod) | ✅ Done | `.env` validation at startup |
| DB backup cron (daily 3am) | ❌ **NON — CRITIQUE** | **Aucune sauvegarde n'existe.** `scripts/backup-remote.sh:18` cible un service `db` absent du compose → no-op silencieux ; aucun cron ne l'installe (`deploy.sh` n'installe que le cleanup Docker). Perte de données irrécupérable en cas de sinistre (CRITICAL-8) |
| Restauration testée | ❌ **NON** | Jamais testée. Aggravé par l'ordre de migrations cassé (HIGH-11) qui rend la reconstruction du schéma incertaine |
| Docker cleanup cron (weekly) | ⚠️ Risque | `docker volume prune -f` peut détruire les volumes nommés (Docker < 23) |
| CI/CD quality gate → auto-deploy | ⚠️ Partiel | Le gate de readiness est **inopérant** (`curl -sf` avale le 503 → le grep ne matche jamais) et le rollback est fictif (HIGH-11). Les migrations DB ne sont jouées par aucun chemin de déploiement (HIGH-12) |
| Cron notifications idempotent | ❌ **NON** | Lancé dans chaque worker uvicorn sans verrou → emails en double, rejoués à chaque déploiement (CRITICAL-9) |

## Remaining Items (Non-Blocking)

| Item | Priority | Notes |
|------|----------|-------|
| Resend SDK timeout | Low | SDK doesn't expose timeout param; retry wrapper catches timeouts |
| 3 pre-existing test failures | Medium | Stripe test expects `price_test` but env has real IDs — fix test fixtures |
| Dynamic feature flag service | Low | Current env-based flags are sufficient; consider LaunchDarkly if A/B needed |
| Per-user rate limiting | Low | Currently IP-based; add user-based limits if abuse detected |
| `datetime.utcnow()` deprecation | Low | `finances_service.py:71` — migrate to `datetime.now(UTC)` |
