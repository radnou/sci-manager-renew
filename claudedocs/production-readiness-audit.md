# Audit de Production Readiness - SCI-Manager

**Date**: 2026-03-04
**Scope**: Backend FastAPI + Frontend SvelteKit + Infrastructure Docker
**Focus**: Sécurité, Qualité, Performance, Observabilité

---

## 📊 Résumé Exécutif

### Score Global: 4/10 ⚠️

**Status**: ❌ **NON PRÊT POUR LA PRODUCTION**

### Risques Critiques Identifiés

| Catégorie | Severity | Impact Business |
|-----------|----------|-----------------|
| 🔴 Logging absent | CRITIQUE | Impossible de débugger les incidents en production |
| 🔴 Error handling incomplet | CRITIQUE | Expérience utilisateur dégradée, données perdues |
| 🔴 Graceful shutdown absent | CRITIQUE | Perte de requêtes pendant les déploiements |
| 🔴 Health checks basiques | CRITIQUE | Pas de détection de défaillances, downtime prolongé |
| 🔴 Secrets non sécurisés | CRITIQUE | Risque de fuite de credentials |
| 🟡 Retry logic absente | IMPORTANT | Échecs transients deviennent des erreurs permanentes |
| 🟡 Connection pooling non configuré | IMPORTANT | Performance dégradée sous charge |
| 🟡 Feature flags absents | IMPORTANT | Rollback difficile, déploiements risqués |

---

## 🔴 CRITIQUES - À Corriger Avant Déploiement

### 1. Logging et Observabilité

#### Status Actuel
- ❌ **Aucune configuration centralisée de logging**
- ❌ Structlog installé mais jamais configuré ni utilisé
- ❌ Un seul fichier utilise le logging (`stripe.py`, warnings uniquement)
- ❌ Pas de logs pour: requêtes API, authentification, erreurs, performances
- ❌ Pas de correlation IDs pour tracer les requêtes
- ❌ Volume Docker `/app/logs` configuré mais inutilisé

#### Impact
- Impossible de débugger les incidents en production
- Pas de visibilité sur l'utilisation réelle de l'API
- Impossible d'identifier les patterns d'erreurs
- Pas d'audit trail pour la sécurité

#### Actions Requises
```python
# 1. Configurer structlog dans app/core/logging_config.py
import structlog

def configure_logging(log_level: str = "INFO"):
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

# 2. Ajouter middleware de logging dans main.py
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(request_id=request_id)

    logger.info("request_started",
                method=request.method,
                path=request.url.path)

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    logger.info("request_completed",
                status_code=response.status_code,
                duration_ms=int(duration * 1000))

    return response

# 3. Utiliser dans tous les endpoints
logger = structlog.get_logger(__name__)

@router.post("/biens")
async def create_bien(bien: BienCreate, user_id: str = Depends(get_current_user)):
    logger.info("creating_bien", user_id=user_id, adresse=bien.adresse)
    try:
        result = await service.create(bien)
        logger.info("bien_created", bien_id=result.id)
        return result
    except Exception as e:
        logger.error("bien_creation_failed", error=str(e), exc_info=True)
        raise
```

---

### 2. Error Handling Global

#### Status Actuel
- ❌ **Pas de global exception handler**
- ❌ Services lèvent des `Exception` génériques au lieu d'exceptions custom
- ❌ Erreurs Supabase retournent 502 Bad Gateway (trop générique)
- ❌ Erreurs de validation Pydantic pas interceptées globalement
- ❌ Pas de distinction entre erreurs client (4xx) et serveur (5xx)
- ❌ Messages d'erreur exposent parfois des détails internes

#### Impact
- Expérience utilisateur dégradée (messages d'erreur peu clairs)
- Difficile de débugger les erreurs côté client
- Risque de fuite d'informations sensibles dans les stacktraces

#### Actions Requises
```python
# 1. Créer app/core/exceptions.py
class SCIManagerException(Exception):
    """Base exception pour SCI-Manager"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class DatabaseError(SCIManagerException):
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status_code=503)

class ResourceNotFoundError(SCIManagerException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(f"{resource} {resource_id} not found", status_code=404)

class ValidationError(SCIManagerException):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class ExternalServiceError(SCIManagerException):
    """Stripe, Resend, Supabase Storage"""
    def __init__(self, service: str, message: str):
        super().__init__(f"{service} error: {message}", status_code=503)

# 2. Ajouter global exception handler dans main.py
@app.exception_handler(SCIManagerException)
async def sci_manager_exception_handler(request: Request, exc: SCIManagerException):
    logger.error("sci_manager_exception",
                 error=exc.message,
                 status_code=exc.status_code,
                 path=request.url.path)

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "request_id": request.state.request_id}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception",
                 error=str(exc),
                 exc_info=True,
                 path=request.url.path)

    # Ne pas exposer les détails en production
    message = "Internal server error" if settings.app_env == "production" else str(exc)

    return JSONResponse(
        status_code=500,
        content={"error": message, "request_id": request.state.request_id}
    )

# 3. Utiliser dans les services
class StorageService:
    async def upload_file(self, file_path: str, file_content: bytes):
        try:
            result = self.client.storage.from_(self.bucket_name).upload(...)
            return result
        except Exception as e:
            logger.error("storage_upload_failed", path=file_path, error=str(e))
            raise ExternalServiceError("Supabase Storage", f"Upload failed: {str(e)}")
```

---

### 3. Health Checks et Readiness Probes

#### Status Actuel
- ❌ **Health check trop simpliste**: retourne toujours `{"status": "ok"}`
- ❌ Pas de vérification de connectivité DB
- ❌ Pas de vérification des services externes (Supabase, Stripe, Resend)
- ❌ Pas de readiness probe séparé
- ❌ Pas de liveness probe
- ❌ Pas de métriques de santé (CPU, mémoire, connexions actives)

#### Impact
- Kubernetes/orchestrateur ne peut pas détecter les défaillances
- Traffic routé vers des instances défaillantes
- Downtime prolongé car pas de détection automatique

#### Actions Requises
```python
# app/api/v1/health.py
from fastapi import APIRouter, status
from app.core.supabase_client import get_supabase_service_client
import stripe
import resend

router = APIRouter(tags=["health"])

@router.get("/health/live")
async def liveness():
    """Liveness probe - L'app est-elle vivante?"""
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness():
    """Readiness probe - L'app peut-elle accepter du traffic?"""
    checks = {
        "database": await _check_database(),
        "supabase_storage": await _check_supabase_storage(),
        "stripe": await _check_stripe(),
        "resend": await _check_resend()
    }

    all_healthy = all(check["healthy"] for check in checks.values())
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

async def _check_database() -> dict:
    try:
        client = get_supabase_service_client()
        # Simple query pour vérifier la connectivité
        result = client.table("sci").select("id").limit(1).execute()
        return {"healthy": True, "latency_ms": result.latency_ms}
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return {"healthy": False, "error": str(e)}

async def _check_supabase_storage() -> dict:
    try:
        client = get_supabase_service_client()
        client.storage.list_buckets()
        return {"healthy": True}
    except Exception as e:
        return {"healthy": False, "error": str(e)}

async def _check_stripe() -> dict:
    try:
        stripe.api_key = settings.stripe_secret_key
        # Balance.retrieve est une opération légère
        stripe.Balance.retrieve()
        return {"healthy": True}
    except Exception as e:
        return {"healthy": False, "error": str(e)}

async def _check_resend() -> dict:
    try:
        resend.api_key = settings.resend_api_key
        # Verify API key sans envoyer d'email
        resend.api_keys.list()
        return {"healthy": True}
    except Exception as e:
        return {"healthy": False, "error": str(e)}

# Configurer dans docker-compose.yml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 40s
```

---

### 4. Graceful Shutdown

#### Status Actuel
- ❌ **Aucun signal handler configuré**
- ❌ Uvicorn lancé sans options de graceful shutdown
- ❌ Pas de cleanup des ressources (connexions DB, workers, fichiers temporaires)
- ❌ Dockerfile CMD basique sans gestion des signaux
- ❌ Requêtes en cours perdues lors des redémarrages/déploiements

#### Impact
- Perte de requêtes pendant les déploiements
- Corruption potentielle de données (transactions interrompues)
- Expérience utilisateur dégradée (erreurs 502 pendant les déploiements)

#### Actions Requises
```python
# 1. Ajouter dans app/main.py
import signal
import asyncio
from contextlib import asynccontextmanager

shutdown_event = asyncio.Event()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager avec graceful shutdown"""
    # Startup
    logger.info("application_starting")

    # Setup signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: shutdown_event.set())

    yield

    # Shutdown
    logger.info("application_shutting_down")
    shutdown_event.set()

    # Cleanup resources
    await cleanup_resources()

    logger.info("application_shutdown_complete")

async def cleanup_resources():
    """Cleanup avant shutdown"""
    logger.info("cleaning_up_resources")

    # Fermer les connexions Supabase
    # Note: Supabase client n'a pas de méthode close explicite,
    # mais on peut cleanup les caches
    get_supabase_anon_client.cache_clear()
    get_supabase_service_client.cache_clear()

    # Attendre les requêtes en cours
    await asyncio.sleep(5)  # Grace period

    logger.info("cleanup_complete")

app = FastAPI(
    title="SCI-Manager API",
    version="1.0.0",
    lifespan=lifespan
)

# 2. Modifier Dockerfile
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--timeout-keep-alive", "75", \
     "--timeout-graceful-shutdown", "30"]

# 3. Ajouter dans docker-compose.yml
services:
  backend:
    stop_grace_period: 30s
    stop_signal: SIGTERM
```

---

### 5. Configuration Environnement et Secrets

#### Status Actuel
- ❌ **Secrets hardcodés dans `config.py`** (placeholders, mais dangereux pattern)
- ❌ Pas de séparation dev/staging/prod
- ❌ Variable `APP_ENV` définie mais jamais utilisée
- ❌ Pas de validation des secrets au démarrage
- ❌ CORS origins accepte `["*"]` en parsing (risque sécurité)
- ❌ Pas de rotation des secrets
- ❌ `.env` committé dans git (risque selon `.gitignore`)

#### Impact
- Risque de fuite de credentials en production
- Configuration dev utilisée en prod par erreur
- Impossible de faire du feature flagging par environnement
- Secrets expirés non détectés

#### Actions Requises
```python
# 1. Créer app/core/config.py robuste
from enum import Enum
from typing import Literal

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    # Environment
    app_env: Environment = Environment.DEVELOPMENT
    app_name: str = "SCI-Manager"
    debug: bool = False

    # Security
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str

    stripe_secret_key: str
    stripe_webhook_secret: str

    resend_api_key: str
    resend_from_email: str

    # CORS
    cors_origins: list[str]
    frontend_url: str

    # Database
    database_url: str
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "text"] = "json"

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_default: str = "100/minute"

    # Feature flags
    feature_cerfa_generation: bool = True
    feature_stripe_payments: bool = True
    feature_email_notifications: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid"  # Interdire les variables inconnues
    )

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Valider les settings pour la production"""
        if self.app_env == Environment.PRODUCTION:
            # Vérifier que les placeholders ne sont pas utilisés
            if "placeholder" in self.stripe_secret_key.lower():
                raise ValueError("Production secrets must be real values")

            if "localhost" in self.cors_origins[0]:
                raise ValueError("Production CORS must not include localhost")

            if self.debug:
                raise ValueError("Debug mode must be disabled in production")

        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.app_env == Environment.DEVELOPMENT

# 2. Créer des fichiers .env séparés
# .env.development
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# .env.staging
APP_ENV=staging
DEBUG=false
LOG_LEVEL=INFO
FEATURE_CERFA_GENERATION=false  # Test progressif

# .env.production
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING
# Tous les secrets depuis vault/secrets manager

# 3. Utiliser dans le code
if settings.is_production:
    # Configuration stricte pour prod
    app.debug = False

if settings.feature_stripe_payments:
    app.include_router(stripe.router)
```

---

## 🟡 IMPORTANTS - À Implémenter Rapidement

### 6. Retry Logic et Resilience

#### Status Actuel
- ❌ **Aucun mécanisme de retry** pour les appels externes
- ❌ Échecs Stripe, Resend, Supabase Storage = échec immédiat
- ❌ Pas de circuit breaker pour les services externes
- ❌ Pas de timeouts configurés
- ❌ Pas de fallback strategies

#### Actions Requises
```python
# 1. Installer tenacity
# pip install tenacity

# 2. Créer app/core/resilience.py
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import structlog

logger = structlog.get_logger(__name__)

# Retry decorator pour appels externes
retry_external_service = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)

# 3. Utiliser dans les services
class EmailService:
    @retry_external_service
    async def send_magic_link(self, email: str, magic_link: str) -> dict:
        logger.info("sending_magic_link", email=email)
        try:
            result = resend.Emails.send({...})
            logger.info("magic_link_sent", email=email)
            return result
        except Exception as e:
            logger.error("magic_link_send_failed", email=email, error=str(e))
            raise ExternalServiceError("Resend", str(e))

class StorageService:
    @retry_external_service
    async def upload_file(self, file_path: str, file_content: bytes):
        try:
            result = self.client.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": content_type}
            )
            return result
        except Exception as e:
            raise ExternalServiceError("Supabase Storage", str(e))

# 4. Ajouter timeouts
import httpx

async def call_external_api_with_timeout():
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=data)
        return response
```

---

### 7. Database Connection Pooling

#### Status Actuel
- ❌ **Supabase client créé sans configuration de pool**
- ❌ Utilisation de `@lru_cache` qui crée un seul client global
- ❌ Pas de limite de connexions concurrentes
- ❌ Pas de timeout configuré
- ❌ Pas de health check des connexions

#### Actions Requises
```python
# Note: Supabase Python SDK n'expose pas directement le pooling PostgreSQL
# car il utilise l'API REST de Supabase, pas une connexion directe PostgreSQL

# OPTION 1: Si vous utilisez l'API REST Supabase (actuel)
# → Le pooling est géré côté Supabase, mais vous devez limiter les clients

class SupabaseClientPool:
    def __init__(self, max_clients: int = 10):
        self.max_clients = max_clients
        self.semaphore = asyncio.Semaphore(max_clients)

    async def execute_with_limit(self, operation):
        async with self.semaphore:
            return await operation()

pool = SupabaseClientPool(max_clients=20)

@router.get("/biens")
async def get_biens(user_id: str = Depends(get_current_user)):
    async def operation():
        client = get_supabase_anon_client()
        return client.table("biens").select("*").eq("owner_id", user_id).execute()

    result = await pool.execute_with_limit(operation)
    return result

# OPTION 2: Si vous migrez vers connexion PostgreSQL directe
# → Utiliser asyncpg avec pooling natif

from asyncpg import create_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.db_pool = await create_pool(
        settings.database_url,
        min_size=10,
        max_size=20,
        max_queries=50000,
        max_inactive_connection_lifetime=300,
        timeout=30,
        command_timeout=60
    )

    yield

    # Shutdown
    await app.state.db_pool.close()

@router.get("/biens")
async def get_biens(request: Request, user_id: str = Depends(get_current_user)):
    async with request.app.state.db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM biens WHERE owner_id = $1", user_id)
        return [dict(row) for row in rows]
```

---

### 8. Rate Limiting Avancé

#### Status Actuel
- ✅ SlowAPI configuré (bien!)
- ⚠️ Limite uniquement par IP (pas suffisant)
- ❌ Pas de limite par user authentifié
- ❌ Pas de limite différenciée par plan (Starter vs Pro)
- ❌ Endpoint Stripe webhook à 10/min par IP (devrait être par signature)
- ❌ Pas de rate limiting sur les actions coûteuses (génération PDF)

#### Actions Requises
```python
# 1. Créer app/core/rate_limit.py amélioré
from slowapi import Limiter
from slowapi.util import get_remote_address

def get_rate_limit_key(request: Request) -> str:
    """Rate limit par user si authentifié, sinon par IP"""
    # Essayer de récupérer le user_id du token
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"])
            user_id = payload.get("sub")
            if user_id:
                # Récupérer le plan de l'utilisateur
                plan = get_user_plan(user_id)  # À implémenter
                return f"user:{user_id}:plan:{plan}"
        except:
            pass

    # Fallback: rate limit par IP
    return f"ip:{get_remote_address(request)}"

limiter = Limiter(key_func=get_rate_limit_key)

# 2. Limites différenciées par plan
RATE_LIMITS = {
    "free": "50/hour",
    "starter": "100/hour",
    "pro": "500/hour",
    "lifetime": "1000/hour"
}

@router.get("/biens")
@limiter.limit(lambda: get_user_rate_limit())
async def get_biens(user_id: str = Depends(get_current_user)):
    ...

def get_user_rate_limit() -> str:
    plan = get_user_plan_from_context()  # À implémenter
    return RATE_LIMITS.get(plan, "50/hour")

# 3. Limites spéciales pour actions coûteuses
@router.post("/quitus/generate")
@limiter.limit("10/hour")  # Génération PDF coûteuse
async def generate_quitus(...):
    ...

# 4. Webhook Stripe: rate limit par customer_id, pas par IP
@router.post("/stripe/webhook")
@limiter.limit("100/hour", key_func=lambda req: req.headers.get("stripe-signature", "unknown"))
async def stripe_webhook(request: Request):
    ...
```

---

### 9. Request Validation

#### Status Actuel
- ✅ Pydantic utilisé pour la validation (bien!)
- ⚠️ Validation basique sur les champs requis
- ❌ Pas de validation métier (ex: loyer_mensuel > 0)
- ❌ Pas de validation des IDs UUID
- ❌ Pas de sanitization des inputs (risque XSS si rendering HTML)
- ❌ Pas de validation de taille de fichiers uploadés

#### Actions Requises
```python
# 1. Améliorer les schemas avec validateurs custom
from pydantic import field_validator, model_validator
from uuid import UUID

class BienCreate(BaseModel):
    adresse: str
    ville: str
    code_postal: str
    type_bien: Literal["appartement", "maison", "local", "parking"]
    surface: float
    prix_acquisition: float
    loyer_mensuel: float

    @field_validator("surface")
    @classmethod
    def validate_surface(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Surface must be positive")
        if v > 10000:  # 10,000 m² max (commercial)
            raise ValueError("Surface too large")
        return v

    @field_validator("prix_acquisition", "loyer_mensuel")
    @classmethod
    def validate_positive_amount(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Amount must be positive")
        return v

    @field_validator("code_postal")
    @classmethod
    def validate_code_postal(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 5:
            raise ValueError("Code postal must be 5 digits")
        return v

    @field_validator("adresse", "ville")
    @classmethod
    def sanitize_string(cls, v: str) -> str:
        # Supprimer les caractères dangereux
        return v.strip().replace("<", "").replace(">", "")

# 2. Validation des UUID dans les path parameters
from fastapi import Path

@router.get("/biens/{bien_id}")
async def get_bien(
    bien_id: str = Path(..., regex=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'),
    user_id: str = Depends(get_current_user)
):
    ...

# 3. Validation de taille de fichier
from fastapi import UploadFile, File

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)
):
    # Vérifier la taille
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise ValidationError(f"File too large. Max size: {MAX_FILE_SIZE} bytes")

    # Vérifier le type MIME
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png"]:
        raise ValidationError("Invalid file type")

    return await storage_service.upload_file(file.filename, contents)
```

---

### 10. Feature Flags

#### Status Actuel
- ❌ **Aucun système de feature flags**
- ❌ Impossible de désactiver des fonctionnalités sans redéploiement
- ❌ Rollout progressif impossible
- ❌ Pas de A/B testing possible

#### Actions Requises
```python
# 1. Simple feature flag system dans config
class Settings(BaseSettings):
    # Feature flags
    feature_cerfa_generation: bool = True
    feature_stripe_payments: bool = True
    feature_email_notifications: bool = True
    feature_pdf_generation: bool = True
    feature_new_dashboard: bool = False  # Rollout progressif

    # Advanced: percentage rollout
    feature_new_dashboard_rollout_pct: int = 0  # 0-100

# 2. Utiliser dans le code
@router.post("/cerfa/generate")
async def generate_cerfa(user_id: str = Depends(get_current_user)):
    if not settings.feature_cerfa_generation:
        raise HTTPException(
            status_code=503,
            detail="CERFA generation temporarily disabled"
        )
    ...

# 3. Rollout progressif basé sur user_id
def is_feature_enabled_for_user(feature: str, user_id: str, rollout_pct: int) -> bool:
    """Enable feature for X% of users (deterministic based on user_id)"""
    if rollout_pct >= 100:
        return True
    if rollout_pct <= 0:
        return False

    # Hash user_id pour avoir un nombre stable entre 0-99
    hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16) % 100
    return hash_value < rollout_pct

@router.get("/dashboard")
async def get_dashboard(user_id: str = Depends(get_current_user)):
    use_new_dashboard = is_feature_enabled_for_user(
        "new_dashboard",
        user_id,
        settings.feature_new_dashboard_rollout_pct
    )

    if use_new_dashboard:
        return await get_new_dashboard(user_id)
    else:
        return await get_old_dashboard(user_id)

# 4. AVANCÉ: Intégration avec LaunchDarkly / Unleash
# pip install launchdarkly-server-sdk

from ldclient import LDClient, Config, Context

ld_client = LDClient(config=Config(sdk_key=settings.launchdarkly_sdk_key))

def is_feature_enabled(feature_key: str, user_id: str) -> bool:
    context = Context.builder(user_id).build()
    return ld_client.variation(feature_key, context, default=False)
```

---

## 🟢 RECOMMANDATIONS - Améliorations Progressives

### 11. Monitoring et Métriques

```python
# Intégrer Prometheus pour les métriques
from prometheus_client import Counter, Histogram, Gauge

# Métriques business
requests_total = Counter("requests_total", "Total requests", ["method", "endpoint", "status"])
request_duration = Histogram("request_duration_seconds", "Request duration", ["method", "endpoint"])
active_users = Gauge("active_users", "Number of active users")
biens_total = Gauge("biens_total", "Total number of biens")

# Middleware métriques
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response

# Endpoint métriques
@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest())
```

---

### 12. Security Headers et CORS

#### Status Actuel
- ✅ Security headers configurés (bien!)
- ✅ CORS middleware configuré
- ⚠️ TrustedHostMiddleware avec wildcard `*.scimanager.fr`
- ❌ Pas de CSP (Content Security Policy)
- ❌ Pas de CSRF protection

#### Actions
```python
# 1. Améliorer security headers
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    # CSP
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://js.stripe.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' https://api.stripe.com;"
    )

    return response

# 2. CSRF protection pour formulaires
from fastapi_csrf_protect import CsrfProtect

@app.post("/api/v1/biens")
async def create_bien(
    bien: BienCreate,
    csrf_protect: CsrfProtect = Depends(),
    user_id: str = Depends(get_current_user)
):
    await csrf_protect.validate_csrf(request)
    ...
```

---

### 13. Docker Production Best Practices

#### Status Actuel
- ❌ Image Python 3.12-slim (bon choix de base mais amélioration possible)
- ❌ Pas de multi-stage build
- ❌ Run en tant que root
- ❌ Pas de health check dans Dockerfile
- ❌ CMD basique sans workers

#### Actions
```dockerfile
# Multi-stage build optimisé
FROM python:3.12-slim AS builder

WORKDIR /app

# Installer les dépendances build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage final
FROM python:3.12-slim

WORKDIR /app

# Créer un user non-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copier les dépendances depuis builder
COPY --from=builder /root/.local /home/appuser/.local

# Copier le code
COPY --chown=appuser:appuser app ./app

# Configurer PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/live')"

# Switcher vers user non-root
USER appuser

EXPOSE 8000

# Production-ready command
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--timeout-keep-alive", "75", \
     "--timeout-graceful-shutdown", "30", \
     "--log-config", "/app/logging_config.json"]
```

---

## 📋 CHECKLIST DE PRODUCTION READINESS

### 🔴 Bloquants (À faire AVANT déploiement)

- [ ] **Logging structuré configuré et testé**
  - [ ] Structlog configuré avec JSON output
  - [ ] Middleware de logging des requêtes
  - [ ] Logs dans tous les endpoints critiques
  - [ ] Correlation IDs sur toutes les requêtes
  - [ ] Rotation des logs configurée

- [ ] **Error handling global implémenté**
  - [ ] Exception handlers globaux configurés
  - [ ] Exceptions custom créées et utilisées
  - [ ] Messages d'erreur ne divulguent pas d'infos sensibles
  - [ ] Erreurs logguées avec contexte complet
  - [ ] Validation des erreurs en staging

- [ ] **Health checks robustes**
  - [ ] `/health/live` (liveness probe)
  - [ ] `/health/ready` avec vérifications DB, Stripe, Resend
  - [ ] Health checks configurés dans docker-compose
  - [ ] Timeouts configurés (max 5s)
  - [ ] Tests des health checks en conditions dégradées

- [ ] **Graceful shutdown configuré**
  - [ ] Signal handlers (SIGTERM, SIGINT)
  - [ ] Lifecycle manager avec cleanup
  - [ ] Grace period de 30s minimum
  - [ ] Tests de rolling deployment sans erreurs
  - [ ] Vérification que les requêtes en cours se terminent

- [ ] **Secrets sécurisés**
  - [ ] Tous les placeholders remplacés par vrais secrets
  - [ ] Secrets stockés dans un vault (AWS Secrets Manager, etc.)
  - [ ] `.env` ajouté au `.gitignore`
  - [ ] Vérification qu'aucun secret n'est committé
  - [ ] Rotation des secrets documentée

- [ ] **Environnements séparés**
  - [ ] `.env.development` créé
  - [ ] `.env.staging` créé
  - [ ] `.env.production` créé
  - [ ] Validation des settings en fonction de l'environnement
  - [ ] Tests que dev ne peut pas utiliser prod secrets

### 🟡 Importants (À faire dans les 2 semaines)

- [ ] **Retry logic implémentée**
  - [ ] Tenacity configuré pour Stripe
  - [ ] Tenacity configuré pour Resend
  - [ ] Tenacity configuré pour Supabase Storage
  - [ ] Tests des retries en conditions d'échec
  - [ ] Alerting sur échecs après retries

- [ ] **Connection pooling configuré**
  - [ ] Limite de clients Supabase concurrents
  - [ ] OU migration vers asyncpg avec pooling natif
  - [ ] Tests de charge pour valider le pooling
  - [ ] Monitoring du nombre de connexions actives

- [ ] **Rate limiting avancé**
  - [ ] Rate limit par user authentifié
  - [ ] Limites différenciées par plan (Free/Starter/Pro)
  - [ ] Limites spéciales pour actions coûteuses (PDF)
  - [ ] Tests des rate limits
  - [ ] Documentation des limites pour les users

- [ ] **Validation des requêtes renforcée**
  - [ ] Validateurs custom sur tous les schemas
  - [ ] Validation des UUID dans path params
  - [ ] Sanitization des inputs
  - [ ] Validation de taille de fichiers
  - [ ] Tests de fuzzing pour trouver les edge cases

- [ ] **Feature flags système**
  - [ ] Feature flags dans Settings
  - [ ] Utilisation dans les endpoints critiques
  - [ ] Tests avec features ON/OFF
  - [ ] Documentation des flags disponibles

### 🟢 Recommandés (Améliorations progressives)

- [ ] **Monitoring et métriques**
  - [ ] Prometheus metrics exposées
  - [ ] Dashboard Grafana configuré
  - [ ] Alerting configuré (PagerDuty, Opsgenie)
  - [ ] SLOs définis (99.9% uptime, p95 < 500ms)

- [ ] **Security hardening**
  - [ ] CSP headers configurés
  - [ ] CSRF protection
  - [ ] Scan de sécurité automatisé (bandit, safety)
  - [ ] Pentest externe

- [ ] **Docker optimisé**
  - [ ] Multi-stage build
  - [ ] User non-root
  - [ ] Image scanner (Trivy, Snyk)
  - [ ] Size optimization

- [ ] **Documentation**
  - [ ] Runbook pour incidents communs
  - [ ] Architecture Decision Records (ADRs)
  - [ ] API documentation (Swagger/OpenAPI)
  - [ ] Postmortems pour incidents passés

---

## 🎯 PLAN D'ACTION PRIORITAIRE

### Semaine 1: Bloquants Critiques

**Jour 1-2**: Logging et Error Handling
- Configurer structlog
- Implémenter exception handlers globaux
- Ajouter logging dans tous les endpoints
- Tests en dev/staging

**Jour 3**: Health Checks
- Implémenter `/health/live` et `/health/ready`
- Ajouter vérifications de services externes
- Configurer dans docker-compose
- Tests de failover

**Jour 4**: Graceful Shutdown
- Implémenter signal handlers
- Configurer lifecycle manager
- Tests de rolling deployment
- Validation en staging

**Jour 5**: Secrets et Configuration
- Créer configs séparées dev/staging/prod
- Migrer secrets vers vault
- Valider que dev ne peut pas toucher prod
- Documentation

### Semaine 2: Importants

**Jour 1-2**: Retry Logic
- Implémenter tenacity pour Stripe/Resend/Storage
- Tests d'échecs et retries
- Alerting sur échecs persistants

**Jour 3**: Connection Pooling
- Configurer pooling Supabase OU migrer vers asyncpg
- Tests de charge
- Monitoring connexions

**Jour 4**: Rate Limiting Avancé
- Rate limit par user + plan
- Limites spéciales pour PDF
- Tests

**Jour 5**: Validation Avancée
- Validateurs custom
- UUID validation
- Sanitization

### Semaine 3: Monitoring et Optimisations

- Prometheus metrics
- Dashboard Grafana
- Docker multi-stage
- Feature flags système

---

## 📊 MÉTRIQUES DE SUCCÈS

### KPIs Production Readiness

| Métrique | Cible | Actuel | Gap |
|----------|-------|--------|-----|
| **Structured Logging Coverage** | 100% endpoints | 1% (1/50 fichiers) | ❌ 99% |
| **Error Handling Coverage** | 100% services | 20% (exceptions génériques) | ❌ 80% |
| **Health Check Depth** | 4+ services | 0 services | ❌ 4 |
| **Graceful Shutdown** | Oui | Non | ❌ |
| **Secrets Security** | Vault | Hardcodé | ❌ |
| **Retry Logic Coverage** | 100% external calls | 0% | ❌ 100% |
| **Rate Limit Strategy** | User + Plan | IP seulement | ⚠️ |
| **Feature Flags** | Système en place | Aucun | ❌ |
| **Docker Security Score** | A (90+) | C (50) | ⚠️ |

### SLOs Production

| SLO | Cible | Mesure Actuelle |
|-----|-------|-----------------|
| Uptime | 99.9% | ❓ Non mesuré |
| API Latency p95 | < 500ms | ❓ Non mesuré |
| Error Rate | < 0.1% | ❓ Non mesuré |
| Time to Recovery | < 5 min | ❓ Non mesuré |

---

## 🚨 RISQUES SI DÉPLOIEMENT EN L'ÉTAT

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Incident impossible à débugger** | 🔴 Élevée | 🔴 Critique | Implémenter logging immédiatement |
| **Perte de données pendant déploiement** | 🟡 Moyenne | 🔴 Critique | Graceful shutdown requis |
| **Service dégradé non détecté** | 🔴 Élevée | 🔴 Critique | Health checks avancés requis |
| **Fuite de secrets** | 🟡 Moyenne | 🔴 Critique | Migrer vers vault |
| **Échecs transients permanents** | 🔴 Élevée | 🟡 Important | Retry logic requis |
| **Saturation connexions DB** | 🟡 Moyenne | 🟡 Important | Connection pooling |
| **Rollback difficile** | 🟡 Moyenne | 🟡 Important | Feature flags |

---

## 📝 CONCLUSION

**Verdict**: ❌ **L'application n'est PAS prête pour la production**

### Résumé des Gaps Critiques

L'application présente **7 gaps critiques** qui rendent un déploiement production risqué:

1. **Observabilité inexistante** → Impossible de débugger les incidents
2. **Error handling incomplet** → Expérience utilisateur dégradée
3. **Health checks basiques** → Défaillances non détectées
4. **Graceful shutdown absent** → Perte de requêtes pendant déploiements
5. **Secrets non sécurisés** → Risque de fuite
6. **Retry logic absente** → Échecs transients deviennent permanents
7. **Connection pooling manquant** → Performance dégradée sous charge

### Estimation de Travail

- **Bloquants critiques** (🔴): 5 jours-développeur
- **Importants** (🟡): 5 jours-développeur
- **Total pour production readiness**: **2 semaines** avec 1 développeur

### Recommandation

**Ne PAS déployer en production** avant d'avoir implémenté au minimum:
1. Logging structuré
2. Error handling global
3. Health checks avancés
4. Graceful shutdown
5. Secrets sécurisés dans un vault

Une fois ces 5 points critiques adressés, un déploiement en **staging** peut être envisagé pour validation finale avant production.

---

**Généré le**: 2026-03-04
**Auteur**: Claude Code Production Readiness Audit
**Prochaine révision**: Après implémentation des bloquants critiques
