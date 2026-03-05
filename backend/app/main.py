import time
import uuid
from contextlib import asynccontextmanager
from typing import Callable, Awaitable

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
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1 import auth, biens, cerfa, files, gdpr, loyers, quitus, stripe
from app.core.config import settings
from app.core.exceptions import SCIManagerException
from app.core.logging_config import configure_logging
from app.core.rate_limit import limiter

# Configurer logging au démarrage
configure_logging(
    log_level=settings.log_level,
    log_format=settings.log_format
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager pour startup et shutdown"""
    # Startup
    logger.info("application_starting",
                app_name=settings.app_name,
                app_env=settings.app_env)
    yield

    # Shutdown
    logger.info("application_shutting_down")


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
    allowed_hosts=["localhost", "127.0.0.1", "*.scimanager.fr", "testserver"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api/v1")
app.include_router(biens.router, prefix="/api/v1")
app.include_router(loyers.router, prefix="/api/v1")
app.include_router(quitus.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")

app.include_router(cerfa.router, prefix="/api/v1")
app.include_router(stripe.router, prefix="/api/v1")
app.include_router(gdpr.router, prefix="/api/v1")
