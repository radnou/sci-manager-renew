import time
import uuid
from contextlib import asynccontextmanager
from typing import Callable, Awaitable

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1 import auth, biens, cerfa, files, loyers, quitus, stripe
from app.core.config import settings
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
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "*.scimanager.fr"])

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
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
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
