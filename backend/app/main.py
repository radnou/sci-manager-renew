import asyncio
import hmac
import json
import os
import signal
import threading
import time
import uuid
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from typing import Awaitable, Callable

import sentry_sdk
import structlog
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

if os.environ.get("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.environ["SENTRY_DSN"],
        integrations=[FastApiIntegration(), StarletteIntegration()],
        traces_sample_rate=0.2 if os.environ.get("APP_ENV") == "production" else 1.0,
        environment=os.environ.get("APP_ENV", "development"),
        send_default_pii=False,
    )
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1 import (
    admin,
    assemblees_generales,
    associes,
    auth,
    biens,
    biens_flat,
    bilans,
    calendrier_fiscal,
    cerfa,
    charges,
    comptabilite,
    credits,
    dashboard,
    declarations,    demo,
    echeances,
    export,
    files,
    finances,
    fiscalite,
    gdpr,
    health,
    import_csv,
    leads,
    locataires,
    loyers,
    mouvements_parts,
    notification_preferences,
    notifications,
    onboarding,
    quitus,
    sci_lifecycle,
    scis,
    stripe,
)
from app.core.config import Environment, settings
from app.core.exceptions import GererSCIException
from app.core.logging_config import configure_logging
from app.core.rate_limit import limiter
from app.core.supabase_client import get_supabase_service_client
from app.services.irl_service import check_irl_revisions
from app.services.nurture_service import process_nurture_emails
from app.services.signup_nurture_service import check_and_send_signup_nurture_emails
from app.services.bilan_mensuel_service import auto_generate_bilans
from app.services.notification_cron import (
    check_bail_renewal,
    check_depot_garantie_restitution,
    check_expiring_bails,
    check_expiring_pno,
    check_fiscal_deadlines,
    check_late_payments,
    check_monthly_loyer_generation,
    check_pending_quittances,
    check_recurring_charges,
    check_regularisation_charges_reminder,
)

# Configurer logging au démarrage
configure_logging(
    log_level=settings.log_level,
    log_format=settings.log_format
)

logger = structlog.get_logger(__name__)

# Shutdown event pour coordonner le shutdown gracieux
shutdown_event = asyncio.Event()

# Background task handle for notification cron
_cron_task: asyncio.Task | None = None


async def _notification_cron_loop():
    """Run notification checks every 24 hours in the background."""
    while True:
        try:
            client = get_supabase_service_client()
            # Task 1: Auto-generate loyer records on the 1st of each month
            await check_monthly_loyer_generation(client)
            # Task 2: Graduated late payment reminders (J+5, J+15, J+30)
            await check_late_payments(client)
            await check_expiring_bails(client)
            await check_expiring_pno(client)
            await check_pending_quittances(client)
            await check_fiscal_deadlines(client)
            # Task 3: IRL revision notifications
            await check_irl_revisions(client)
            # Task 4: Tacit bail renewals and conge deadlines
            await check_bail_renewal(client)
            # Task 5: Auto-generate recurring charges (quarterly)
            await check_recurring_charges(client)
            # Task 9: Regularisation charges reminder (January)
            await check_regularisation_charges_reminder(client)
            # Task 10: Depot garantie restitution alerts (1 or 2 month deadline)
            await check_depot_garantie_restitution(client)
            # Task 6: Lead nurture email sequence
            nurture_sent = await process_nurture_emails()
            if nurture_sent:
                logger.info("nurture_emails_sent", count=nurture_sent)
            # Task 7: Signup nurture email sequence (day 1, 3, 7)
            signup_nurture_sent = await check_and_send_signup_nurture_emails()
            if signup_nurture_sent:
                logger.info("signup_nurture_emails_sent", count=signup_nurture_sent)
            # Task 8: Generate monthly bilans on the 2nd of each month
            bilans_count = await auto_generate_bilans(client)
            if bilans_count:
                logger.info("bilans_mensuels_generated", count=bilans_count)
            logger.info("notification_cron_cycle_complete")
            await asyncio.sleep(86_400)  # 24h
        except asyncio.CancelledError:
            logger.info("notification_cron_cancelled")
            break
        except Exception:
            logger.exception("notification_cron_error")
            await asyncio.sleep(3600)  # retry in 1h on error


def _json_safe(value):
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]

    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager avec graceful shutdown.

    Startup:
    - Configure signal handlers pour SIGTERM et SIGINT
    - Initialise les ressources

    Shutdown:
    - Attend la fin des requêtes en cours (grace period)
    - Nettoie les ressources
    """
    # ==================== STARTUP ====================
    logger.info("application_starting",
                app_name=settings.app_name,
                app_env=settings.app_env,
                version="1.0.0")
    shutdown_event.clear()

    # Configure Stripe global timeout
    import stripe
    stripe.max_network_retries = 2
    stripe.default_http_client = stripe.HTTPXClient(
        timeout=settings.stripe_request_timeout_seconds,
    )

    # Configurer les signal handlers pour graceful shutdown
    loop = asyncio.get_event_loop()

    def handle_shutdown_signal(sig):
        """Handler appelé lors de SIGTERM ou SIGINT"""
        signal_name = signal.Signals(sig).name
        logger.info("shutdown_signal_received", signal=signal_name)
        shutdown_event.set()

    # Enregistrer les handlers uniquement sur le thread principal.
    if threading.current_thread() is threading.main_thread():
        configured_signals: list[str] = []
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, lambda s=sig: handle_shutdown_signal(s))
                configured_signals.append(signal.Signals(sig).name)
            except (NotImplementedError, RuntimeError, ValueError):
                logger.warning("signal_handler_unavailable", signal=signal.Signals(sig).name)
        if configured_signals:
            logger.info("signal_handlers_configured", signals=configured_signals)
    else:
        logger.info("signal_handlers_skipped", reason="not_main_thread")
    logger.info("application_started")

    # Start the notification cron background task
    global _cron_task  # noqa: PLW0603
    import sys
    if "pytest" not in sys.modules:
        _cron_task = asyncio.create_task(_notification_cron_loop())
        logger.info("notification_cron_started")
    else:
        logger.info("notification_cron_skipped_in_tests")

    yield

    # ==================== SHUTDOWN ====================
    logger.info("application_shutting_down")

    # Cancel the notification cron background task
    if _cron_task is not None and not _cron_task.done():
        _cron_task.cancel()
        try:
            await _cron_task
        except asyncio.CancelledError:
            pass
        logger.info("notification_cron_stopped")

    # Marquer le shutdown event
    shutdown_event.set()

    # Grace period: attendre que les requêtes en cours se terminent
    grace_period_seconds = 30
    logger.info("waiting_for_requests_to_complete", grace_period_seconds=grace_period_seconds)

    # Attendre un peu pour que les requêtes se terminent
    await asyncio.sleep(min(grace_period_seconds, 5))

    # Cleanup des ressources
    await cleanup_resources()

    logger.info("application_shutdown_complete")


async def cleanup_resources():
    """
    Nettoie les ressources avant shutdown.

    - Clear les caches (@lru_cache)
    - Ferme les connexions si nécessaire
    - Flush les logs
    """
    logger.info("cleaning_up_resources")

    # Clear les caches Supabase clients
    from app.core.supabase_client import get_supabase_anon_client, get_supabase_service_client
    get_supabase_anon_client.cache_clear()
    get_supabase_service_client.cache_clear()

    logger.info("caches_cleared")
    logger.info("cleanup_complete")


app = FastAPI(title="GererSCI API", version="1.0.0", lifespan=lifespan)


# ============================================================
# EXCEPTION HANDLERS GLOBAUX
# ============================================================

@app.exception_handler(GererSCIException)
async def gerersci_exception_handler(
    request: Request,
    exc: GererSCIException
) -> JSONResponse:
    """
    Handler pour toutes les exceptions métier GererSCI.
    Retourne un JSON avec le message d'erreur et le request_id.
    """
    # Récupérer le request_id du contexte
    request_id = getattr(request.state, "request_id", "unknown")

    # Logger l'erreur avec contexte
    logger.error(
        "gerersci_exception",
        error_type=exc.__class__.__name__,
        error_message=exc.message,
        status_code=exc.status_code,
        path=request.url.path,
        method=request.method
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "code": exc.code,
            "details": exc.details,
            "request_id": request_id
        }
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handler pour les erreurs de validation FastAPI/Pydantic.
    Retourne les détails de validation de manière structurée.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    # Extraire les erreurs de validation
    errors = _json_safe(exc.errors())

    logger.warning(
        "request_validation_error",
        validation_errors=errors,
        path=request.url.path,
        method=request.method
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "code": "validation_error",
            "details": errors,
            "request_id": request_id
        }
    )


@app.exception_handler(PydanticValidationError)
async def pydantic_validation_exception_handler(
    request: Request,
    exc: PydanticValidationError
) -> JSONResponse:
    """Handler pour les ValidationError de Pydantic"""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.warning(
        "pydantic_validation_error",
        validation_errors=_json_safe(exc.errors()),
        path=request.url.path
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "code": "validation_error",
            "details": _json_safe(exc.errors()),
            "request_id": request_id
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handler pour toutes les exceptions non gérées.
    En production: cache les détails pour éviter la fuite d'infos.
    En dev: affiche l'exception complète pour debugging.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    # Logger l'erreur avec stacktrace complète
    logger.error(
        "unhandled_exception",
        error_type=exc.__class__.__name__,
        error_message=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True  # Inclut la stacktrace dans les logs
    )

    # En production: cacher les détails
    # En dev: montrer l'exception pour debugging
    if settings.app_env == Environment.PRODUCTION:
        error_message = "Internal server error"
    else:
        error_message = f"{exc.__class__.__name__}: {str(exc)}"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": error_message,
            "code": "internal_error",
            "request_id": request_id
        }
    )


# ============================================================
# MIDDLEWARES ET CONFIGURATION
# ============================================================

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)


def _resolved_cors_origins() -> list[str]:
    origins: list[str] = []
    for origin in settings.cors_origins:
        normalized = origin.strip().rstrip("/")
        if normalized:
            origins.append(normalized)

    parsed_frontend = urlparse(settings.frontend_url.strip())
    if parsed_frontend.scheme and parsed_frontend.netloc:
        scheme = parsed_frontend.scheme
        netloc = parsed_frontend.netloc
        origins.append(f"{scheme}://{netloc}")

        # Also allow bare domain and www variant when frontend is on a subdomain
        # e.g. app.gerersci.fr → also allow gerersci.fr and www.gerersci.fr
        host = netloc.split(":")[0]  # strip port if present
        parts = host.split(".")
        if len(parts) >= 3:
            base_domain = ".".join(parts[-2:])
            port_suffix = f":{netloc.split(':')[1]}" if ":" in netloc else ""
            origins.append(f"{scheme}://{base_domain}{port_suffix}")
            origins.append(f"{scheme}://www.{base_domain}{port_suffix}")

    # Keep order stable while removing duplicates.
    return list(dict.fromkeys(origins))


local_dev_origin_regex = None
if settings.app_env != Environment.PRODUCTION:
    # Allow localhost/127.0.0.1 with any port for local frontend variants (Vite, Nginx, Storybook, etc.).
    local_dev_origin_regex = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=_resolved_cors_origins(),
    allow_origin_regex=local_dev_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Accept"],
)


# ============================================================
# WRITE-PROTECTION MIDDLEWARE (P0 security fix)
# Blocks mutating requests from users without an active subscription.
# ============================================================

# Paths exempt from write-protection (prefix match with trailing slash to
# prevent /api/v1/stripe matching a hypothetical /api/v1/stripe_admin).
_WRITE_EXEMPT_PREFIXES: tuple[str, ...] = (
    "/api/v1/auth/",
    "/api/v1/stripe/",
    "/api/v1/demo/",
    "/api/v1/health/",
    "/api/v1/leads/",
    "/api/v1/onboarding/",
    "/api/v1/gdpr/",
    "/api/v1/admin/",
    "/api/v1/notifications/",           # marking as read = UI state, not business data
    "/api/v1/user/notification-preferences",  # demo UX: let users set prefs
    "/api/v1/quitus/public-generate",   # public lead magnet, no auth
    "/health",
)

_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@app.middleware("http")
async def write_protection_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Block demo/inactive users from mutating data via direct API calls."""
    if request.method not in _MUTATING_METHODS:
        return await call_next(request)

    path = request.url.path
    if any(path.startswith(prefix) for prefix in _WRITE_EXEMPT_PREFIXES):
        return await call_next(request)

    # Extract user_id from Bearer token (supports HS256 + ES256/RS256 via JWKS)
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        # No auth header -- let the endpoint's own auth dependency handle 401
        return await call_next(request)

    token = auth_header[7:]
    try:
        from app.core.security import _decode_bearer_token
        payload = await _decode_bearer_token(token)
        user_id = payload.get("sub")
    except Exception:
        # Bad token -- let endpoint auth handle it
        return await call_next(request)

    if user_id:
        from app.core.paywall import check_write_access
        if not check_write_access(user_id):
            return JSONResponse(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                content={
                    "code": "subscription_required",
                    "error": "Un abonnement actif est requis pour cette action.",
                    "redirect": "/pricing",
                },
            )

    return await call_next(request)


@app.middleware("http")
async def maintenance_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Block all requests in maintenance mode, except health + webhooks."""
    if settings.maintenance_mode:
        path = request.url.path
        # Always allow health checks and Stripe webhooks.
        # The webhook route is /api/v1/stripe/webhook (singular); accept both
        # spellings for defence-in-depth in case the route is ever renamed.
        if (
            path in ("/api/v1/health", "/api/v1/health/ready")
            or path == "/api/v1/stripe/webhook"
            or path.startswith("/api/v1/stripe/webhook/")
            or path.startswith("/api/v1/stripe/webhooks")
        ):
            return await call_next(request)
        # Allow beta access with password
        if settings.beta_password:
            beta_cookie = request.cookies.get("beta_access")
            beta_header = request.headers.get("X-Beta-Password")
            if (beta_cookie and hmac.compare_digest(beta_cookie, settings.beta_password)) or (beta_header and hmac.compare_digest(beta_header, settings.beta_password)):
                return await call_next(request)
        return JSONResponse(
            status_code=503,
            content={
                "code": "maintenance",
                "error": "GérerSCI est en cours de mise à jour. Revenez bientôt.",
                "maintenance": True,
            },
        )
    return await call_next(request)


@app.middleware("http")
async def logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """
    Middleware de logging pour toutes les requêtes.
    Ajoute un correlation ID et logge les détails de chaque requête.
    """
    # Générer un request_id unique
    request_id = str(uuid.uuid4())

    # Ajouter le request_id au contexte structlog
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    # Stocker request_id dans request.state pour l'utiliser ailleurs
    request.state.request_id = request_id

    if shutdown_event.is_set() and not request.url.path.startswith("/health"):
        logger.warning("request_rejected_during_shutdown", path=request.url.path, method=request.method)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": "Service shutting down", "code": "service_unavailable", "request_id": request_id},
        )

    # Logger le début de la requête
    logger.info("request_started",
                method=request.method,
                path=request.url.path,
                client_host=request.client.host if request.client else None)

    # Mesurer le temps de traitement
    start_time = time.time()

    try:
        response = await call_next(request)
    except Exception:
        duration = time.time() - start_time
        logger.error(
            "request_failed",
            method=request.method,
            path=request.url.path,
            duration_ms=int(duration * 1000),
            exc_info=True,
        )
        raise

    # Calculer la durée
    duration = time.time() - start_time

    # Logger la fin de la requête
    logger.info("request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=int(duration * 1000))

    # Ajouter le request_id dans les headers de réponse pour debugging
    response.headers["X-Request-ID"] = request_id

    return response


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # Security Headers de base
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

    # Content Security Policy (CSP)
    # connect-src must include every origin the browser is allowed to fetch from
    # (API, Supabase REST + Realtime WSS, Stripe, analytics, error reporting).
    # Browser blocks fetch BEFORE sending the request when an origin is missing,
    # surfacing as "Failed to fetch" with no backend log entry.
    matomo_url = os.environ.get("VITE_MATOMO_URL", "https://analytics.gerersci.fr")
    api_public_url = os.environ.get("VITE_API_URL", "https://api.gerersci.fr").strip().rstrip("/")
    supabase_public_url = (
        os.environ.get("SUPABASE_PUBLIC_URL")
        or os.environ.get("VITE_SUPABASE_URL")
        or settings.supabase_url
    ).strip().rstrip("/")
    sentry_dsn = os.environ.get("SENTRY_DSN") or os.environ.get("VITE_SENTRY_DSN", "")
    sentry_origin = ""
    if sentry_dsn:
        try:
            parsed = urlparse(sentry_dsn)
            if parsed.scheme and parsed.netloc:
                # Strip credentials from the DSN; we only need scheme://host
                host = parsed.hostname or ""
                if host:
                    sentry_origin = f"https://{host}"
        except Exception:
            sentry_origin = ""

    connect_sources = ["'self'"]
    if api_public_url:
        connect_sources.append(api_public_url)
    if supabase_public_url:
        connect_sources.append(supabase_public_url)
        # Supabase Realtime uses WebSocket — derive wss:// equivalent.
        if supabase_public_url.startswith("https://"):
            connect_sources.append("wss://" + supabase_public_url[len("https://"):])
        elif supabase_public_url.startswith("http://"):
            connect_sources.append("ws://" + supabase_public_url[len("http://"):])
    connect_sources.extend([
        "https://api.stripe.com",
        "https://*.stripe.com",
        matomo_url,
    ])
    if sentry_origin:
        connect_sources.append(sentry_origin)

    if settings.app_env != Environment.PRODUCTION:
        connect_sources.extend([
            "http://localhost:8001",
            "http://127.0.0.1:8001",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "ws://localhost:5173",
            "ws://127.0.0.1:5173",
        ])

    # Deduplicate while preserving order
    connect_src = " ".join(dict.fromkeys(s for s in connect_sources if s))

    csp_policy = (
        "default-src 'self'; "
        f"script-src 'self' https://js.stripe.com {matomo_url}; "
        "style-src 'self' 'unsafe-inline'; "  # Tailwind nécessite unsafe-inline
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        f"connect-src {connect_src}; "
        "frame-src https://js.stripe.com https://hooks.stripe.com; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "upgrade-insecure-requests"
    )
    response.headers["Content-Security-Policy"] = csp_policy

    # Permissions Policy (Feature Policy)
    response.headers["Permissions-Policy"] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(self), "
        "usb=(), "
        "accelerometer=(), "
        "gyroscope=(), "
        "magnetometer=()"
    )

    # Referrer Policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # X-Permitted-Cross-Domain-Policies
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

    return response


# Include health router (pas de prefix pour /health/live et /health/ready)
app.include_router(health.router)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(scis.router, prefix="/api/v1")
app.include_router(associes.router, prefix="/api/v1")
app.include_router(biens.router, prefix="/api/v1")
app.include_router(charges.router, prefix="/api/v1")
app.include_router(fiscalite.router, prefix="/api/v1")
app.include_router(locataires.router, prefix="/api/v1")
app.include_router(loyers.router, prefix="/api/v1")
app.include_router(quitus.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")

app.include_router(cerfa.router, prefix="/api/v1")
app.include_router(stripe.router, prefix="/api/v1")
app.include_router(gdpr.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(notification_preferences.router, prefix="/api/v1")
app.include_router(onboarding.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(finances.router, prefix="/api/v1")
app.include_router(biens_flat.router, prefix="/api/v1")
app.include_router(mouvements_parts.router, prefix="/api/v1")
app.include_router(sci_lifecycle.router, prefix="/api/v1")
app.include_router(assemblees_generales.router, prefix="/api/v1")
app.include_router(calendrier_fiscal.router, prefix="/api/v1")
app.include_router(comptabilite.router, prefix="/api/v1")
app.include_router(echeances.router, prefix="/api/v1")
app.include_router(import_csv.router, prefix="/api/v1")
app.include_router(import_csv.templates_router, prefix="/api/v1")
app.include_router(leads.router, prefix="/api/v1")
app.include_router(bilans.router, prefix="/api/v1")
app.include_router(credits.router, prefix="/api/v1")
app.include_router(demo.router, prefix="/api/v1")
app.include_router(declarations.router, prefix="/api/v1")
app.include_router(admin.router)
