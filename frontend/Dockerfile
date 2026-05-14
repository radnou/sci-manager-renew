# Node 22: packageManager/corepack pulls pnpm 11.x, which requires Node >=22.13 (uses node:sqlite).
FROM node:22-alpine AS build

WORKDIR /app

ARG VITE_API_URL
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY
ARG VITE_STRIPE_PUBLISHABLE_KEY
ARG PUBLIC_FEATURE_MULTI_SCI_DASHBOARD_V2
ARG VITE_SENTRY_DSN
ARG VITE_MATOMO_URL
ARG VITE_MATOMO_SITE_ID
ARG VITE_PLAUSIBLE_DOMAIN
ARG VITE_PLAUSIBLE_SRC
ARG VITE_PLAUSIBLE_API_HOST
ARG VITE_ANALYTICS_REQUIRE_CONSENT

ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_SUPABASE_URL=${VITE_SUPABASE_URL}
ENV VITE_SUPABASE_ANON_KEY=${VITE_SUPABASE_ANON_KEY}
ENV VITE_STRIPE_PUBLISHABLE_KEY=${VITE_STRIPE_PUBLISHABLE_KEY}
ENV PUBLIC_FEATURE_MULTI_SCI_DASHBOARD_V2=${PUBLIC_FEATURE_MULTI_SCI_DASHBOARD_V2}
ENV VITE_SENTRY_DSN=${VITE_SENTRY_DSN}
ENV VITE_MATOMO_URL=${VITE_MATOMO_URL}
ENV VITE_MATOMO_SITE_ID=${VITE_MATOMO_SITE_ID}
ENV VITE_PLAUSIBLE_DOMAIN=${VITE_PLAUSIBLE_DOMAIN}
ENV VITE_PLAUSIBLE_SRC=${VITE_PLAUSIBLE_SRC}
ENV VITE_PLAUSIBLE_API_HOST=${VITE_PLAUSIBLE_API_HOST}
ENV VITE_ANALYTICS_REQUIRE_CONSENT=${VITE_ANALYTICS_REQUIRE_CONSENT}

COPY package.json pnpm-lock.yaml ./
# pnpm 11 blocks native build scripts by default (ERR_PNPM_IGNORED_BUILDS for
# @sentry/cli, esbuild, ...). Approve them explicitly inside the container build.
RUN corepack enable \
    && pnpm config set dangerously-allow-all-builds true \
    && pnpm install --frozen-lockfile

COPY . .
RUN pnpm run build

# Prune to production dependencies only
RUN pnpm prune --prod

# ---- Production runtime ----
# Match the build stage on Node 22 (required by pnpm 11 / node:sqlite).
FROM node:22-alpine AS runtime

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=4173
ENV HOST=0.0.0.0

# Copy build output + production node_modules
COPY --from=build /app/build ./build
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./

# Run as non-root user (security: container escape mitigation)
RUN addgroup -S app && adduser -S app -G app
USER app

EXPOSE 4173

CMD ["node", "build"]
