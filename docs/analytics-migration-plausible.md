# Analytics migration — Matomo → Plausible

Status: proposed
Owner: platform / growth
Last updated: 2026-05-14

## 1. Current problem

GérerSCI is shipping two analytics setups today, both with issues:

1. **Matomo is the documented stack.** `frontend/src/lib/matomo.ts` reads
   `VITE_MATOMO_URL` and `VITE_MATOMO_SITE_ID`, and the production VPS runs
   `matomo` + `matomo-db` containers behind `analytics.gerersci.fr`. The
   public endpoints respond correctly:
   - `GET https://analytics.gerersci.fr/matomo.js` → `200`
   - `POST https://analytics.gerersci.fr/matomo.php` → `200`
2. **A hard-coded Umami-style script was also baked into `app.html`:**

   ```html
   <script defer src="https://analytics.gerersci.fr/script.js"
           data-website-id="0782cbe1-3b70-4c15-8a16-bf7b071fadf1"></script>
   ```

   That URL returns **404** in production (no Umami instance is deployed,
   only Matomo). Every visitor's browser fires a failing request on every
   page load. Worse, the `data-website-id` is hard-coded into the build, so
   it cannot be changed without a redeploy and leaks an identifier that
   should be configurable.

In addition to fixing the broken script, the team would like to evaluate
moving from Matomo to a lighter, cookieless solution to reduce hosting
load and simplify the consent UX.

## 2. What this PR changes

- Removes the hard-coded `script.js` tag from `frontend/src/app.html`.
- Introduces an analytics abstraction at `frontend/src/lib/analytics/`:
  - `index.ts` — public surface (`initAnalytics`, `trackEvent`,
    `trackPageView`, `grantAnalyticsConsent`, `revokeAnalyticsConsent`,
    `activeAnalyticsProviders`) plus the existing `EVENTS` map for
    backwards compatibility with all current call sites.
  - `providers/plausible.ts` — new Plausible provider, cookieless, env-driven.
  - `providers/matomo.ts` — refactored Matomo provider, kept as optional
    legacy fallback.
  - `types.ts`, `events.ts` — typed surface.
- Updates `CookieConsent.svelte` so its label reflects the configured
  providers (e.g. "Plausible (sans cookies)" or "Plausible et Matomo").
- Adds Docker build args and `.env.example` entries:
  - `VITE_PLAUSIBLE_DOMAIN`, `VITE_PLAUSIBLE_SRC`, `VITE_PLAUSIBLE_API_HOST`
  - `VITE_ANALYTICS_REQUIRE_CONSENT` (default `true`)
  - Existing `VITE_MATOMO_URL` / `VITE_MATOMO_SITE_ID` remain supported and
    default to empty so a build without analytics env stays silent.
- `trackEvent` and `EVENTS` keep the same import path
  (`import { trackEvent, EVENTS } from '$lib/analytics'`) — no call site
  changes required.

The PR does **not** deploy anything, modify the VPS, or touch the Matomo
container set.

## 3. Recommended rollout

A staged migration keeps existing dashboards intact while we validate the
new provider.

### Phase 1 — Land code (this PR)

- Merge the abstraction.
- Keep build env vars for Matomo on the VPS so behavior is unchanged.
- The 404 Umami request disappears immediately.

### Phase 2 — Deploy Plausible alongside Matomo (dual tracking, ~7 days)

- Sign up at [plausible.io](https://plausible.io) (or deploy self-hosted
  Plausible Community Edition on the VPS — see §6).
- Add the site domain in Plausible.
- Set production env vars on the VPS:
  - `VITE_PLAUSIBLE_DOMAIN=gerersci.fr`
  - `VITE_PLAUSIBLE_SRC=https://plausible.io/js/script.js`
    (or your self-hosted URL).
  - Keep `VITE_MATOMO_URL`, `VITE_MATOMO_SITE_ID` set.
- Rebuild + redeploy frontend.
- Both providers will fire in parallel. Compare key metrics for 7 days:
  - Daily uniques and pageviews
  - Top pages
  - Conversion funnel: `/pricing` → `register_start` → `register_success` → `checkout_confirm`
- Confirm the Plausible counters match Matomo within ~5%.

### Phase 3 — Switch primary analytics to Plausible

- Treat Plausible as the source of truth in dashboards and reports.
- Update Notion / runbooks to point to the Plausible dashboard URL.
- Update the privacy policy (`/confidentialite`) to mention Plausible.

### Phase 4 — Retire Matomo

After at least 30 days of clean Plausible data:

1. Export historical Matomo data:
   - Visits, pageviews, top pages, events — via Matomo `Export` UI or API.
2. Snapshot the Matomo MySQL volume:

   ```bash
   docker exec gerersci_matomo_db \
     mariadb-dump -u root -p"$MATOMO_DB_ROOT_PASSWORD" matomo \
     | gzip > matomo-final-$(date +%F).sql.gz
   ```

3. Unset `VITE_MATOMO_URL` / `VITE_MATOMO_SITE_ID` in the deploy env.
4. Rebuild + redeploy frontend.
5. Stop the Matomo containers in `docker-compose.yml`, then remove their
   service blocks + volumes after the dump has been archived to S3 (or
   equivalent cold storage).
6. Remove the DNS A record for `analytics.gerersci.fr`.

## 4. Consent / RGPD model

Plausible is cookieless, does not collect personal data, and does not need
visitor consent under GDPR/RGPD per the [Plausible legal documentation](https://plausible.io/data-policy).
Matomo, in its default cookie-based mode, does require consent.

The abstraction supports both models:

- **Default (`VITE_ANALYTICS_REQUIRE_CONSENT=true`)** — keep the existing
  consent banner. Plausible loads anyway (it is safe pre-consent), Matomo
  honors `requireCookieConsent` and only stores cookies after the user
  accepts.
- **Cookieless mode (`VITE_ANALYTICS_REQUIRE_CONSENT=false`)** — flip only
  after Matomo is retired. The consent banner can then be removed or made
  optional.

The `CookieConsent.svelte` wording now reflects the configured providers
automatically (e.g. "Plausible (sans cookies)" when Matomo is unset).

## 5. Alternatives considered

| Tool          | Strengths                                                              | Weaknesses                                                                 | Best for                                                |
| ------------- | ---------------------------------------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------- |
| **Plausible** | Cookieless, <1KB script, EU-hosted, simple dashboard, fair pricing.    | No session replay, no funnels in entry tier, lighter custom event surface. | **Recommended.** Public marketing pages + simple goals. |
| **Umami**     | Free OSS, very simple, similar privacy stance.                         | Smaller community, weaker event/goal UI, the broken script we just removed was Umami-shaped — risk of misconfig. | Pure self-host, minimal needs.                          |
| **PostHog**   | Funnels, retention, session replay, feature flags, A/B tests.          | Heavier script, requires more careful consent UX, more expensive at scale. | Product analytics on the in-app (`/app`) surface only.  |
| **Matomo**    | Full-featured, complete control when self-hosted, granular reports.    | MySQL + Apache footprint, cookie-based by default, heavier ops burden.     | Compliance-heavy reporting (current setup).             |

**Recommended split, mid-term:**

- **Plausible** on public/marketing pages (`/`, `/pricing`,
  `/simulateur-*`, `/calendrier-fiscal`) — fast, cookieless, no banner
  needed when used alone.
- **PostHog (optional, later)** on authenticated routes (`(app)/`) for
  funnels and retention if the team needs deeper product insight. Loaded
  only after login + explicit consent.

## 6. Self-hosting Plausible (optional)

If we prefer keeping analytics on `analytics.gerersci.fr`:

```yaml
# Append to docker-compose.yml (replaces Matomo services after retirement)
services:
  plausible-db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: ${PLAUSIBLE_DB_PASSWORD}
    volumes:
      - plausible_db:/var/lib/postgresql/data

  plausible-events-db:
    image: clickhouse/clickhouse-server:24-alpine
    volumes:
      - plausible_events_db:/var/lib/clickhouse

  plausible:
    image: plausible/analytics:latest
    depends_on: [plausible-db, plausible-events-db]
    environment:
      BASE_URL: https://analytics.gerersci.fr
      SECRET_KEY_BASE: ${PLAUSIBLE_SECRET_KEY_BASE}
      DATABASE_URL: postgres://postgres:${PLAUSIBLE_DB_PASSWORD}@plausible-db:5432/plausible_db
      CLICKHOUSE_DATABASE_URL: http://plausible-events-db:8123/plausible_events_db
```

Then set in the frontend env:

```bash
VITE_PLAUSIBLE_DOMAIN=gerersci.fr
VITE_PLAUSIBLE_SRC=https://analytics.gerersci.fr/js/script.js
VITE_PLAUSIBLE_API_HOST=https://analytics.gerersci.fr
```

The Plausible script will POST events to
`${VITE_PLAUSIBLE_API_HOST}/api/event` instead of `plausible.io`.

## 7. Verification checklist

After Phase 2 deploy:

- [ ] `view-source:https://gerersci.fr/` no longer references `script.js`.
- [ ] Network tab shows a `200` from `plausible.io/js/script.js` (or the
      self-hosted equivalent), and `POST /api/event` returns `202`.
- [ ] Browser shows no `404` for `analytics.gerersci.fr/script.js`.
- [ ] After clicking "Tout accepter" on the cookie banner, Matomo's
      `_pk_*` cookies appear. Without consent, only Plausible fires.
- [ ] `EVENTS.PRICING_PLAN_SELECT` fires on Plausible "Goals" when a plan
      is clicked.
- [ ] Plausible counter is within 5% of Matomo counter over 24h.

## 8. Rollback

If Plausible misbehaves, unset `VITE_PLAUSIBLE_DOMAIN` and rebuild. The
abstraction falls back to Matomo-only, and the consent banner copy
adapts automatically.
