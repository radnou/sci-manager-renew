#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE=".env"
CHECK_ONLY="false"
BUILD_IMAGES="true"

usage() {
	cat <<'EOF'
Usage:
  bash scripts/start-real-stack.sh [--check] [--no-build] [--env-file PATH]

Options:
  --check           Validate env + compose config only, without starting containers.
  --no-build        Skip docker image rebuild before startup.
  --env-file PATH   Load a specific env file instead of .env.
  --help            Show this help.

What it does:
  1. Loads and validates the env file required for real email + Stripe testing.
  2. Validates the Docker Compose configuration.
  3. Starts the full stack (db, backend, frontend, nginx).
  4. Waits for backend/frontend health endpoints.
  5. Prints the exact URLs and manual smoke checks for email and Stripe.
EOF
}

while [[ $# -gt 0 ]]; do
	case "$1" in
		--check)
			CHECK_ONLY="true"
			shift
			;;
		--no-build)
			BUILD_IMAGES="false"
			shift
			;;
		--env-file)
			ENV_FILE="${2:-}"
			if [[ -z "$ENV_FILE" ]]; then
				echo "[start-real-stack] Missing value after --env-file" >&2
				exit 1
			fi
			shift 2
			;;
		--help|-h)
			usage
			exit 0
			;;
		*)
			echo "[start-real-stack] Unknown argument: $1" >&2
			usage >&2
			exit 1
			;;
	esac
done

if [[ ! -f "$ENV_FILE" ]]; then
	echo "[start-real-stack] Env file not found: $ENV_FILE" >&2
	echo "[start-real-stack] Copy .env.example or .env.production.example and fill the real values first." >&2
	exit 1
fi

set -a
source "$ENV_FILE"
set +a

if [[ -z "${SUPABASE_INTERNAL_URL:-}" ]]; then
	SUPABASE_INTERNAL_URL="${SUPABASE_URL}"
	if [[ "${SUPABASE_INTERNAL_URL}" =~ ^http://(127\.0\.0\.1|localhost)(:.*)?$ ]]; then
		SUPABASE_INTERNAL_URL="${SUPABASE_INTERNAL_URL/127.0.0.1/host.docker.internal}"
		SUPABASE_INTERNAL_URL="${SUPABASE_INTERNAL_URL/localhost/host.docker.internal}"
	fi
	export SUPABASE_INTERNAL_URL
fi

required_vars=(
	"APP_ENV"
	"DATABASE_PASSWORD"
	"SUPABASE_URL"
	"SUPABASE_ANON_KEY"
	"SUPABASE_SERVICE_ROLE_KEY"
	"SUPABASE_JWT_SECRET"
	"STRIPE_SECRET_KEY"
	"STRIPE_PUBLISHABLE_KEY"
	"STRIPE_WEBHOOK_SECRET"
	"STRIPE_STARTER_PRICE_ID"
	"STRIPE_PRO_PRICE_ID"
	"STRIPE_LIFETIME_PRICE_ID"
	"RESEND_API_KEY"
	"RESEND_FROM_EMAIL"
	"FRONTEND_URL"
	"VITE_API_URL"
)

placeholder_pattern='(placeholder|your_|example|demo|changeme)'

require_var() {
	local key="$1"
	local value="${!key:-}"
	if [[ -z "$value" ]]; then
		echo "[start-real-stack] Missing required variable: $key" >&2
		exit 1
	fi
	if [[ "$value" =~ $placeholder_pattern ]]; then
		echo "[start-real-stack] Variable still looks like a placeholder: $key=$value" >&2
		exit 1
	fi
}

for key in "${required_vars[@]}"; do
	require_var "$key"
done

if [[ ! "${STRIPE_SECRET_KEY}" =~ ^sk_(test|live)_ ]]; then
	echo "[start-real-stack] STRIPE_SECRET_KEY must start with sk_test_ or sk_live_" >&2
	exit 1
fi

if [[ ! "${STRIPE_PUBLISHABLE_KEY}" =~ ^pk_(test|live)_ ]]; then
	echo "[start-real-stack] STRIPE_PUBLISHABLE_KEY must start with pk_test_ or pk_live_" >&2
	exit 1
fi

if [[ ! "${STRIPE_WEBHOOK_SECRET}" =~ ^whsec_ ]]; then
	echo "[start-real-stack] STRIPE_WEBHOOK_SECRET must start with whsec_" >&2
	exit 1
fi

if [[ ! "${RESEND_API_KEY}" =~ ^re_ ]]; then
	echo "[start-real-stack] RESEND_API_KEY must start with re_" >&2
	exit 1
fi

if [[ ! "${RESEND_FROM_EMAIL}" =~ ^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$ ]]; then
	echo "[start-real-stack] RESEND_FROM_EMAIL must be a valid sender email address" >&2
	exit 1
fi

if [[ ! "${SUPABASE_URL}" =~ ^https?:// ]]; then
	echo "[start-real-stack] SUPABASE_URL must be a valid http(s) URL" >&2
	exit 1
fi

if [[ ! "${FRONTEND_URL}" =~ ^https?:// ]]; then
	echo "[start-real-stack] FRONTEND_URL must be a valid http(s) URL" >&2
	exit 1
fi

if [[ ! "${VITE_API_URL}" =~ ^https?:// ]]; then
	echo "[start-real-stack] VITE_API_URL must be a valid http(s) URL" >&2
	exit 1
fi

echo "[start-real-stack] Validating docker compose configuration"
docker compose --env-file "$ENV_FILE" config >/tmp/sci-manager-compose-check.out

echo "[start-real-stack] Environment looks consistent"
echo "  APP_ENV=${APP_ENV}"
echo "  FRONTEND_URL=${FRONTEND_URL}"
echo "  VITE_API_URL=${VITE_API_URL}"
echo "  SUPABASE_URL=${SUPABASE_URL}"
echo "  SUPABASE_INTERNAL_URL=${SUPABASE_INTERNAL_URL}"
echo "  STRIPE mode=$( [[ "${STRIPE_SECRET_KEY}" == sk_live_* ]] && echo live || echo test )"
echo "  RESEND_FROM_EMAIL=${RESEND_FROM_EMAIL}"
echo "  MULTI_SCI_V2=${PUBLIC_FEATURE_MULTI_SCI_DASHBOARD_V2:-true}"

if [[ "$CHECK_ONLY" == "true" ]]; then
	echo "[start-real-stack] Check-only mode complete"
	exit 0
fi

echo "[start-real-stack] Starting Docker services"
if [[ "$BUILD_IMAGES" == "true" ]]; then
	docker compose --env-file "$ENV_FILE" up -d --build
else
	docker compose --env-file "$ENV_FILE" up -d
fi

wait_for_http() {
	local url="$1"
	local label="$2"
	local attempts=60
	local sleep_seconds=2
	local status=""

	for ((i = 1; i <= attempts; i++)); do
		status="$(curl -s -o /dev/null -w '%{http_code}' "$url" || true)"
		if [[ "$status" == "200" ]]; then
			echo "[start-real-stack] ${label} ready (${url})"
			return 0
		fi
		sleep "$sleep_seconds"
	done

	echo "[start-real-stack] ${label} did not become ready: ${url} (last status=${status:-n/a})" >&2
	return 1
}

wait_for_http "http://127.0.0.1:8000/health/live" "backend liveness"
wait_for_http "http://127.0.0.1:8000/health/ready" "backend readiness"
wait_for_http "http://127.0.0.1:4173/" "frontend"

cat <<EOF

[start-real-stack] Stack started successfully.

Local endpoints:
  Frontend : http://127.0.0.1:4173
  Backend  : http://127.0.0.1:8000
  Nginx    : http://127.0.0.1

Configured callback URLs:
  FRONTEND_URL=${FRONTEND_URL}
  VITE_API_URL=${VITE_API_URL}

Manual real smoke checks:
  1. Open http://127.0.0.1:4173/login and send a magic link to a real email inbox.
  2. Open http://127.0.0.1:4173/pricing and trigger a real Stripe checkout.
  3. If Stripe is in test mode, use card 4242 4242 4242 4242, any future date, any CVC.
  4. Watch logs with:
     docker compose logs -f backend frontend nginx
  5. Stop everything with:
     docker compose down
EOF
