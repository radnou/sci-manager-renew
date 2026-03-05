import asyncio
import signal
import threading
import time
import uuid
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from typing import Awaitable, Callable

import structlog
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1 import auth, biens, cerfa, files, gdpr, health, loyers, quitus, stripe
from app.core.config import Environment, settings
from app.core.exceptions import SCIManagerException
from app.core.logging_config import configure_logging
from app.core.rate_limit import limiter

# Configurer logging au démarrage
configure_logging(
    log_level=settings.log_level,
    log_format=settings.log_format
)

logger = structlog.get_logger(__name__)

# Shutdown event pour coordonner le shutdown gracieux
shutdown_event = asyncio.Event()


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

    yield

    # ==================== SHUTDOWN ====================
    logger.info("application_shutting_down")

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


app = FastAPI(title="SCI-Manager API", version="1.0.0", lifespan=lifespan)


# ============================================================
# EXCEPTION HANDLERS GLOBAUX
# ============================================================

@app.exception_handler(SCIManagerException)
async def sci_manager_exception_handler(
    request: Request,
    exc: SCIManagerException
) -> JSONResponse:
    """
    Handler pour toutes les exceptions métier SCI-Manager.
    Retourne un JSON avec le message d'erreur et le request_id.
    """
    # Récupérer le request_id du contexte
    request_id = getattr(request.state, "request_id", "unknown")

    # Logger l'erreur avec contexte
    logger.error(
        "sci_manager_exception",
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
    errors = exc.errors()

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
        validation_errors=exc.errors(),
        path=request.url.path
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors(),
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
    if settings.app_env == "production":
        error_message = "Internal server error"
    else:
        error_message = f"{exc.__class__.__name__}: {str(exc)}"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": error_message,
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
        origins.append(f"{parsed_frontend.scheme}://{parsed_frontend.netloc}")

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
    allow_methods=["*"],
    allow_headers=["*"],
)


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

    # Logger le début de la requête
    logger.info("request_started",
                method=request.method,
                path=request.url.path,
                client_host=request.client.host if request.client else None)

    # Mesurer le temps de traitement
    start_time = time.time()

    # Traiter la requête
    response = await call_next(request)

    # Calculer la durée
    duration = time.time() - start_time

    # Logger la fin de la requête
    logger.info("request_completed",
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
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' https://js.stripe.com; "
        "style-src 'self' 'unsafe-inline'; "  # Tailwind nécessite unsafe-inline
        f"img-src 'self' data: https:; "
        "font-src 'self' data:; "
        f"connect-src 'self' {settings.supabase_url} https://api.stripe.com; "
        "frame-src https://js.stripe.com; "
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
app.include_router(biens.router, prefix="/api/v1")
app.include_router(loyers.router, prefix="/api/v1")
app.include_router(quitus.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")

app.include_router(cerfa.router, prefix="/api/v1")
app.include_router(stripe.router, prefix="/api/v1")
app.include_router(gdpr.router, prefix="/api/v1")
