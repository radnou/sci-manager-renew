# backend/app/api/v1/health.py
import asyncio
import time
from datetime import datetime, timezone

import resend
import stripe
import structlog
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.supabase_client import get_supabase_service_client

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def liveness():
    """
    Liveness probe - L'application est-elle vivante?

    Retourne toujours 200 tant que le process tourne.
    Utilisé par Kubernetes/Docker pour redémarrer l'app si elle freeze.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness():
    """
    Readiness probe - L'application peut-elle accepter du traffic?

    Vérifie la connectivité avec tous les services externes:
    - Database (Supabase PostgreSQL)
    - Supabase Storage
    - Stripe API
    - Resend API

    Returns:
        200: Tous les services sont accessibles (ready)
        503: Au moins un service est inaccessible (not ready)
    """
    logger.info("running_readiness_check")

    # Exécuter tous les checks en parallèle
    checks_results = await asyncio.gather(
        _check_database(),
        _check_supabase_storage(),
        _check_stripe(),
        _check_resend(),
        return_exceptions=True
    )

    # Structurer les résultats
    checks = {
        "database": checks_results[0] if not isinstance(checks_results[0], Exception) else {"healthy": False, "error": str(checks_results[0])},
        "supabase_storage": checks_results[1] if not isinstance(checks_results[1], Exception) else {"healthy": False, "error": str(checks_results[1])},
        "stripe": checks_results[2] if not isinstance(checks_results[2], Exception) else {"healthy": False, "error": str(checks_results[2])},
        "resend": checks_results[3] if not isinstance(checks_results[3], Exception) else {"healthy": False, "error": str(checks_results[3])},
    }

    # Déterminer si tous sont healthy
    all_healthy = all(check.get("healthy", False) for check in checks.values())

    # Status code
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    # Logger le résultat
    if all_healthy:
        logger.info("readiness_check_passed")
    else:
        unhealthy_services = [name for name, check in checks.items() if not check.get("healthy")]
        logger.warning("readiness_check_failed", unhealthy_services=unhealthy_services)

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


async def _check_database() -> dict:
    """
    Vérifie la connectivité avec la base de données Supabase.

    Returns:
        dict: {"healthy": bool, "latency_ms"?: int, "error"?: str}
    """
    try:
        start = time.time()

        client = get_supabase_service_client()

        # Requête simple pour vérifier la connectivité
        # On limite à 1 résultat pour être rapide
        _result = client.table("sci").select("id").limit(1).execute()

        latency_ms = int((time.time() - start) * 1000)

        logger.debug("database_check_passed", latency_ms=latency_ms)
        return {"healthy": True, "latency_ms": latency_ms}

    except Exception as e:
        logger.error("database_check_failed", error=str(e))
        return {"healthy": False, "error": str(e)}


async def _check_supabase_storage() -> dict:
    """
    Vérifie la connectivité avec Supabase Storage.

    Returns:
        dict: {"healthy": bool, "error"?: str}
    """
    try:
        client = get_supabase_service_client()

        # Lister les buckets (opération légère)
        buckets = client.storage.list_buckets()

        logger.debug("storage_check_passed", buckets_count=len(buckets))
        return {"healthy": True}

    except Exception as e:
        logger.error("storage_check_failed", error=str(e))
        return {"healthy": False, "error": str(e)}


async def _check_stripe() -> dict:
    """
    Vérifie la connectivité avec l'API Stripe.

    Returns:
        dict: {"healthy": bool, "error"?: str}
    """
    try:
        stripe.api_key = settings.stripe_secret_key

        # Balance.retrieve est une opération légère et rapide
        stripe.Balance.retrieve()

        logger.debug("stripe_check_passed")
        return {"healthy": True}

    except Exception as e:
        logger.error("stripe_check_failed", error=str(e))
        return {"healthy": False, "error": str(e)}


async def _check_resend() -> dict:
    """
    Vérifie la connectivité avec l'API Resend.

    Returns:
        dict: {"healthy": bool, "error"?: str}
    """
    try:
        resend.api_key = settings.resend_api_key

        # Lister les API keys (opération légère qui vérifie la connectivité)
        resend.api_keys.list()

        logger.debug("resend_check_passed")
        return {"healthy": True}

    except Exception as e:
        logger.error("resend_check_failed", error=str(e))
        return {"healthy": False, "error": str(e)}
