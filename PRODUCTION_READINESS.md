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
| JWT verification | ✅ Done | JWKS rotation with cache |
| RLS on all tables | ✅ Done | Supabase policies |
| CORS properly configured | ✅ Done | Explicit origins, no wildcard in prod |
| Security headers (CSP, HSTS, etc.) | ✅ Done | `main.py:525-570` |
| TrustedHostMiddleware | ✅ Done | `main.py:397-400` |
| Admin secret-key auth | ✅ Done | URL-based, outside (app) group |
| No secrets in error responses | ✅ Done | Generic "Internal server error" in prod |
| Webhook signature verification | ✅ Done | Stripe webhook validates signature |

## Infrastructure

| Item | Status | Details |
|------|--------|---------|
| Docker Compose with healthchecks | ✅ Done | Backend + frontend + reverse proxy |
| Deploy guard (no localhost in prod) | ✅ Done | `.env` validation at startup |
| DB backup cron (daily 3am) | ✅ Done | VPS cron |
| Docker cleanup cron (weekly) | ✅ Done | Sunday 4am |
| CI/CD quality gate → auto-deploy | ✅ Done | SSH to VPS |

## Remaining Items (Non-Blocking)

| Item | Priority | Notes |
|------|----------|-------|
| Resend SDK timeout | Low | SDK doesn't expose timeout param; retry wrapper catches timeouts |
| 3 pre-existing test failures | Medium | Stripe test expects `price_test` but env has real IDs — fix test fixtures |
| Dynamic feature flag service | Low | Current env-based flags are sufficient; consider LaunchDarkly if A/B needed |
| Per-user rate limiting | Low | Currently IP-based; add user-based limits if abuse detected |
| `datetime.utcnow()` deprecation | Low | `finances_service.py:71` — migrate to `datetime.now(UTC)` |
