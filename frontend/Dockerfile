FROM node:20-alpine AS build

WORKDIR /app

ARG VITE_API_URL
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY
ARG VITE_STRIPE_PUBLISHABLE_KEY
ARG PUBLIC_FEATURE_MULTI_SCI_DASHBOARD_V2
ARG VITE_SENTRY_DSN
ARG VITE_MATOMO_URL
ARG VITE_MATOMO_SITE_ID

ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_SUPABASE_URL=${VITE_SUPABASE_URL}
ENV VITE_SUPABASE_ANON_KEY=${VITE_SUPABASE_ANON_KEY}
ENV VITE_STRIPE_PUBLISHABLE_KEY=${VITE_STRIPE_PUBLISHABLE_KEY}
ENV PUBLIC_FEATURE_MULTI_SCI_DASHBOARD_V2=${PUBLIC_FEATURE_MULTI_SCI_DASHBOARD_V2}
ENV VITE_SENTRY_DSN=${VITE_SENTRY_DSN}
ENV VITE_MATOMO_URL=${VITE_MATOMO_URL}
ENV VITE_MATOMO_SITE_ID=${VITE_MATOMO_SITE_ID}

COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

COPY . .
RUN pnpm run build

# Prune to production dependencies only
RUN pnpm prune --prod

# ---- Production runtime ----
FROM node:20-alpine AS runtime

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=4173
ENV HOST=0.0.0.0

# Copy build output + production node_modules
COPY --from=build /app/build ./build
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./

EXPOSE 4173

CMD ["node", "build"]
