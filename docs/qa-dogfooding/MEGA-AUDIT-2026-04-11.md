# QA Dogfooding — Mega Audit Report
**Date**: 2026-04-11
**Agents**: 10 parallel (10 completed)
**Total findings**: 150+

---

## CRITICAL / P0 — Fix Immediately

| # | Agent | File:Line | Issue | Impact |
|---|-------|-----------|-------|--------|
| **SEC-01** | Security | `core/rate_limit.py` + `docker-compose.yml` | **Rate limiting completely ineffective in production** — all requests arrive from nginx container IP, not real client IP. `--proxy-headers` missing from uvicorn. All rate limits (magic link, demo seed, activate) are unenforced. | Brute-force, spam, DDoS |
| **API-01** | Backend | `gdpr.py:399` | **Account deletion uses user JWT for `auth.admin.delete_user`** — data is cascade-deleted but auth account survives. Zombie auth accounts. | GDPR non-compliance |
| **API-02** | Backend | `auth.py:94-100` | **`upsert + ignore_duplicates` breaks first activation** — returns empty on both insert AND ignore. New user can't activate post-payment. | Blocked users |
| **API-03** | Backend | `stripe.py:41` | **Linear O(n) scan of ALL users** to find email in Stripe activation path. At scale = timeout = activation failure. | Payment activation broken |
| **BIZ-01** | Business | `quitus_service.py` | **Race condition in quittance number generation** — concurrent PDF requests can generate duplicate legal document numbers. | Legal compliance |
| **BIZ-02** | Business | `quitus_service.py` | **No `statut=paye` check on quittance generation** — can generate receipts for unpaid rent. | Financial fraud risk |
| **BIZ-03** | Business | `demo_service.py` | **Demo cleanup deletes real user data** — `frais_agence`, `credits_immobiliers`, `AG`, `mouvements_parts` cleaned by FK/SCI ID, not `is_demo` flag. If user created real data during demo, it's lost. | Data loss |
| **PERF-01** | Perf | `dashboard_service.py:90` | **Dashboard fetches ALL loyers (all-time) then filters in Python** — for alert display. Grows linearly with account age. | Slow dashboard |
| **STRIPE-01** | Stripe | `pricing/+page.svelte` + `+page.svelte` | **Fondateur buy button sends `'lifetime'` instead of `'fondateur'`** — `resolve_price_id_for_plan` has no LIFETIME case → returns None → "Price ID unavailable" error for ALL authenticated Fondateur buyers. | **100% Fondateur revenue blocked** |
| **STRIPE-02** | Stripe | `subscription_service.py` | **`guarantee_expires_at` always NULL** — 30-day money-back guarantee not tracked in DB. Refund endpoint falls back to `created_at + 30d` but no DB constraint enforces it. | Legal compliance gap |
| **STRIPE-03** | Stripe | `stripe.py` webhook | **`subscription.updated` defaults missing status to `"active"`** — malformed webhook silently grants paid access. | Security: free access |
| **STRIPE-04** | Stripe | `entitlements.py` | **Placeholder price IDs resolve to real plans** — `price_cabinet_placeholder` → Cabinet plan with full `multi_user` + `api_access`. | Security: plan escalation |

---

## HIGH / P1 — Fix This Sprint

### Security & Data Integrity

| # | Agent | File:Line | Issue |
|---|-------|-----------|-------|
| SEC-02 | Security | `bilans.py:64,88,115` | IDOR — bilan reads use service-role client (bypasses RLS) |
| SEC-03 | Security | `gdpr.py:225` | JWT decoded without signature verification in fallback |
| SEC-04 | Security | `scis_biens.py:1070` | No cross-SCI ownership check on `attach_locataire_to_bail` |
| API-04 | Backend | `gdpr.py:115,355` | `locataires.id_bien` column doesn't exist — GDPR export/delete silently fails for tenants |
| API-05 | Backend | `scis_biens.py:813` | `bail_locataires` deleted before bail authorization check — partial deletion on failure |
| API-06 | Backend | `scis_biens.py:685-695` | Race condition: concurrent bail creation (two `en_cours` bails) |
| API-07 | Backend | `scis_biens.py:1076` | Raw `body: dict` input, no Pydantic schema validation |

### Business Logic

| # | Agent | File:Line | Issue |
|---|-------|-----------|-------|
| BIZ-04 | Business | `regularisation_service.py:45` | Provisions calculated for 12 months regardless of bail start date |
| BIZ-05 | Business | `regularisation_service.py:51-58` | Charges from prior bail period included in new tenant's regularisation |
| BIZ-06 | Business | `credit_service.py` | No error when `mensualite < interest` — loan never amortizes silently |
| BIZ-07 | Business | `notification_cron.py:103-110` | Auto-generated loyers missing `id_locataire` — affects quittance PDF |
| BIZ-08 | Business | `bilan_mensuel_service.py` | Wrong scope data cached on `scope_id` miss + upsert broken for NULL `scope_id` |
| BIZ-09 | Business | `dashboard_service.py` | `taux_recouvrement` is all-time, `cashflow` is 12-month — inconsistent time windows |

### Frontend

| # | Agent | File:Line | Issue |
|---|-------|-----------|-------|
| FE-01 | State | `LoyerTable.svelte:17-36` | Full Svelte 4 syntax (`export let`, `$:`) — not migrated |
| FE-02 | State | `GettingStartedPanel.svelte:24-50` | Same — 11 `export let` props |
| FE-03 | State | `biens/[bienId]/+page.svelte:55-59` | **Stale bien data on navigation** — `bien` not nulled before fetch, old data renders |
| FE-04 | State | `(app)/+layout.ts:32-43` | API error → redirect loop (/welcome → /pricing endlessly) |
| FE-05 | UX | `CrudModal.svelte:50-129` | **No focus trap** — affects all 8 CRUD modals |
| FE-06 | UX | `CrudModal.svelte` | **No autofocus on first input** — user must click to start typing |
| FE-07 | UX | 6 modals | **Silent validation failures** — no error feedback on invalid submit |
| FE-08 | UX | `settings/+page.svelte:65-97` | `passwordLoading` not reset on error → button stays disabled forever |
| FE-09 | UX | `register/+page.svelte:3` | **Svelte 4 store import** (`$app/stores` instead of `$app/state`) |
| FE-10 | State | `lib/stores/sci-context.ts` | **Stores not reset on logout** — stale SCI data persists |

### Performance

| # | Agent | File:Line | Issue |
|---|-------|-----------|-------|
| PERF-02 | Perf | `dashboard_service.py:176` | All-time loyers fetched for 12-month KPI |
| PERF-03 | Perf | `notification_cron.py:255-270` | N+1 locataire queries per bail in cron |
| PERF-04 | Perf | `notification_cron.py:34-111` | 3 DB queries per bail on loyer generation day (N×3) |
| PERF-05 | Perf | `stripe.py:82,499,669,681` | Sync Stripe calls blocking async event loop |
| PERF-06 | Perf | All `.svelte` files | **Zero `loading="lazy"` on any images** |
| DB-01 | Perf | migrations | Missing `loyers(id_sci, statut)` index |
| DB-02 | Perf | migrations | Missing `biens(id_sci, id)` composite index |
| DB-03 | Perf | migrations | Incomplete `bilans_mensuels` cache index |

### SEO & Legal

| # | Agent | File:Line | Issue |
|---|-------|-----------|-------|
| LEGAL-01 | SEO | `mentions-legales/+page.svelte` | **SIRET "en cours d'immatriculation"** — required by L111-2 Code du Commerce |
| LEGAL-02 | SEO | `+page.svelte:983` | **"Carte bancaire requise" contradicts register page** "Aucune carte bancaire requise" |
| LEGAL-03 | SEO | `pricing/+page.svelte` | **"Places restantes sur 25" is hardcoded** — false scarcity (L121-1 Code conso) |
| LEGAL-04 | SEO | `app.html:27` | **Umami loads before cookie consent** — potential RGPD violation |
| SEO-01 | SEO | 3 lead magnets | Missing `og:image` — broken social sharing |
| SEC-05 | Security | `gdpr.py:48-176` | **GDPR export missing 8 tables** (credits, assurances, frais, AG, mouvements, subscriptions, regularisations, evenements) |

### Dark Mode & Responsive

| # | Agent | File:Line | Issue |
|---|-------|-----------|-------|
| DARK-01 | Visual | `LoyerTable.svelte:79,92` | `text-slate-900` without `dark:` variant — invisible text |
| DARK-02 | Visual | `BienTable.svelte:81,90,93` | Same — table cells invisible in dark mode |
| DARK-03 | Visual | `FicheBienHeader.svelte:54-55` | DPE badges: runtime class strings can't use `dark:` |
| RESP-01 | Visual | `+page.svelte:579-610` | Landing table `overflow-hidden` clips content on mobile |
| RESP-02 | Visual | `SCIGrid.svelte:114` | `grid-cols-3` without responsive fallback |
| RESP-03 | Visual | `onboarding/+page.svelte:811` | `grid-cols-3` KPI preview — overflows on 375px |
| RESP-04 | Visual | `finances/+page.svelte:151` | Action buttons overflow without `flex-wrap` |

---

## MEDIUM / P2 — Backlog

### Test Coverage Gaps (most dangerous)

| Rank | Untested Path | Risk |
|------|---------------|------|
| 1 | `POST /stripe/refund` — zero tests | Money-losing |
| 2 | `POST /stripe/cancel-subscription` — zero tests | Billing mismatch |
| 3 | `demo_service.cleanup_demo_data()` — zero tests | Conversion blocker |
| 4 | `regularisation_service` — zero tests | Wrong financial calculations |
| 5 | `resume_fiscal_service` + PDF — zero tests | Tax compliance exposure |
| 6 | `credit_service` — zero tests | Wrong amortisation shown |
| 7 | `bilan_mensuel_service` (619 lines) — zero tests | Wrong P&L balances |
| 8 | 6 untested routers: bilans, calendrier_fiscal, comptabilite, credits, demo, notification_preferences | Mixed |
| 9 | 17/34 services untested (50%) | Mixed |
| 10 | 14/30 frontend routes without E2E | Mixed |

### Additional P2 Items

- 4 form modals allow `montant=0` (BailModal, LoyerModal, ChargeModal, FraisModal)
- `layerchart` + `d3-scale` not code-split (bundled for all pages)
- `stripe` Node SDK in browser dependencies
- 1 Storage RPC per document for URL signing (N+1)
- No HTTP cache headers on dashboard endpoint
- FAQ accordion leaks content to screen readers when collapsed
- Several `$effect` blocks without AbortController cleanup
- Double `getCurrentSession()` call (root + app layout)

---

## Stats Summary

| Metric | Count |
|--------|-------|
| Total unique findings | **~150** |
| CRITICAL / P0 | **8** |
| HIGH / P1 | **~45** |
| MEDIUM / P2 | **~60** |
| LOW / P3 | **~37** |
| Agents deployed | **10** |
| Agents completed | **9** (Stripe/Payment pending) |
| Files scanned | **200+** |

---

## Recommended Fix Order

### Week 1 — Ship Blockers
1. SEC-01: Add `--proxy-headers` to uvicorn (2 lines)
2. API-01: Swap to service client for `auth.admin.delete_user` (1 line)
3. API-02: Fix `upsert + ignore_duplicates` activation logic
4. LEGAL-01: Update SIRET in legal pages
5. LEGAL-02: Fix contradictory CTA copy
6. BIZ-02: Add `statut=paye` check on quittance generation

### Week 2 — Data Integrity
7. API-03: Replace `list_users()` with direct email lookup
8. BIZ-03: Fix demo cleanup to use `is_demo` flag properly
9. API-04: Fix locataires GDPR export/delete (join table)
10. API-06: Add bail creation lock (prevent dual `en_cours`)
11. PERF-01: Add DB-level filter on dashboard loyers query

### Week 3 — UX & Frontend
12. FE-01/02: Migrate LoyerTable + GettingStartedPanel to Svelte 5
13. FE-05/06: Add focus trap + autofocus to CrudModal
14. FE-07: Add inline error messages to silent-fail modals
15. FE-03: Null `bien` before fetch on navigation
16. DARK-01/02: Add `dark:` text variants to table cells

### Week 4 — Performance & Tests
17. DB-01/02/03: Add missing indexes
18. PERF-03/04: Batch cron queries (eliminate N+1)
19. PERF-05: Convert sync Stripe calls to async
20. Write tests for: stripe/refund, demo_service, regularisation, credit_service
