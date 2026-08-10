from __future__ import annotations

import socket
from datetime import datetime, timezone
from time import perf_counter
from urllib.parse import urlparse
from collections import OrderedDict

import stripe
import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import Environment, settings
from app.core.lifecycle import is_shutting_down
from app.core.entitlements import PlanKey, resolve_price_id_for_plan
from app.core.supabase_client import get_supabase_service_client

router = APIRouter(tags=["health"])
logger = structlog.get_logger(__name__)


def _check_database_socket(database_url: str) -> dict:
    parsed = urlparse(database_url)
    host = parsed.hostname
    port = parsed.port or 5432
    if not host:
        return {"healthy": False, "error": "database_url missing host"}

    start = perf_counter()
    try:
        with socket.create_connection((host, port), timeout=settings.database_socket_timeout_seconds):
            latency = int((perf_counter() - start) * 1000)
            return {"healthy": True, "latency_ms": latency, "mode": "postgres_socket"}
    except OSError as exc:
        return {"healthy": False, "error": str(exc)}


async def _check_database() -> dict:
    start = perf_counter()
    try:
        client = get_supabase_service_client()
        client.table("sci").select("id").limit(1).execute()
        latency = int((perf_counter() - start) * 1000)
        return {"healthy": True, "latency_ms": latency}
    except Exception as exc:  # pragma: no cover - network dependent
        fallback_error = str(exc)
        # Fallback to direct PostgreSQL socket check when Supabase API is unavailable
        if settings.database_url:
            fallback = _check_database_socket(settings.database_url)
            if fallback.get("healthy"):
                fallback["degraded"] = True
                fallback["warning"] = f"supabase query unavailable: {fallback_error}"
                return fallback
        return {"healthy": False, "error": fallback_error}


async def _check_supabase_storage() -> dict:
    try:
        client = get_supabase_service_client()
        client.storage.list_buckets()
        return {"healthy": True}
    except Exception as exc:  # pragma: no cover - network dependent
        return {
            "healthy": True,
            "degraded": True,
            "warning": f"supabase storage unavailable: {exc}",
        }


def _is_placeholder_stripe_key(key: str) -> bool:
    """Detect fake/placeholder Stripe keys used in local development."""
    if not key:
        return True
    # Common placeholder patterns: sk_test_fake..., sk_test_xxx, sk_test_placeholder
    placeholder_markers = ("fake", "xxx", "placeholder", "dummy", "test_test", "000")
    key_lower = key.lower()
    return any(marker in key_lower for marker in placeholder_markers)


async def _check_stripe() -> dict:
    if not settings.stripe_secret_key:
        return {"healthy": False, "error": "missing stripe secret key"}

    stripe.api_key = settings.stripe_secret_key
    if settings.stripe_secret_key.startswith("sk_test"):
        mode = "test"
    elif settings.stripe_secret_key.startswith("sk_live"):
        mode = "live"
    else:
        return {"healthy": False, "error": "invalid stripe key format"}

    # In dev with placeholder keys, skip price validation entirely
    if _is_placeholder_stripe_key(settings.stripe_secret_key):
        return {
            "healthy": True,
            "mode": mode,
            "degraded": True,
            "warning": "stripe price validation skipped (placeholder key detected)",
        }

    # Use resolve_price_id_for_plan() — same function the checkout uses.
    # Cabinet est un plan ABANDONNE : ses price IDs sont archivés (inactifs) dans
    # Stripe live et ne doivent plus être validés ici, sinon la sonde renvoie
    # systématiquement "catalog invalid" et bloque la readiness.
    configured_prices = OrderedDict(
        (
            ("starter_monthly", resolve_price_id_for_plan(PlanKey.STARTER, "month")),
            ("starter_annual", resolve_price_id_for_plan(PlanKey.STARTER, "year")),
            ("pro_monthly", resolve_price_id_for_plan(PlanKey.PRO, "month")),
            ("pro_annual", resolve_price_id_for_plan(PlanKey.PRO, "year")),
        )
    )
    # Filter out placeholders
    configured_prices = OrderedDict(
        (name, pid) for name, pid in configured_prices.items()
        if pid and not pid.endswith("_placeholder")
    )
    if not configured_prices:
        return {
            "healthy": False,
            "mode": mode,
            "error": "no valid stripe price ids configured",
        }

    invalid_price_ids: list[str] = []
    inactive_price_ids: list[str] = []

    for name, price_id in configured_prices.items():
        try:
            price = await stripe.Price.retrieve_async(price_id)
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning("stripe_price_validation_failed", price_id=price_id, price_name=name, exc_info=True)
            invalid_price_ids.append(name)
            continue

        is_active = bool(price.get("active", True)) if hasattr(price, "get") else bool(getattr(price, "active", True))
        if not is_active:
            inactive_price_ids.append(name)

    if invalid_price_ids or inactive_price_ids:
        return {
            "healthy": False,
            "mode": mode,
            "error": "stripe checkout catalog invalid",
            "invalid_price_ids": invalid_price_ids,
            "inactive_price_ids": inactive_price_ids,
        }

    return {"healthy": True, "mode": mode, "validated_price_count": len(configured_prices)}


async def _check_resend() -> dict:
    key = settings.resend_api_key or ""
    if key.startswith("re_"):
        return {"healthy": True}
    return {"healthy": False, "error": "invalid resend key format"}


def _build_readiness_summary(checks: dict[str, dict]) -> tuple[str, int, dict[str, object]]:
    critical_services = ("database", "supabase_storage", "stripe")
    critical_unhealthy = [
        service
        for service in critical_services
        if checks.get(service, {}).get("healthy") is not True
    ]
    degraded_services = [
        service for service, check in checks.items() if check.get("degraded") is True
    ]
    unhealthy_services = [
        service for service, check in checks.items() if check.get("healthy") is not True
    ]

    if critical_unhealthy:
        readiness_status = "not_ready"
        status_code = 503
    elif degraded_services or unhealthy_services:
        readiness_status = "degraded"
        status_code = 200
    else:
        readiness_status = "ready"
        status_code = 200

    return readiness_status, status_code, {
        "critical_services": list(critical_services),
        "critical_unhealthy": critical_unhealthy,
        "degraded_services": degraded_services,
        "unhealthy_services": unhealthy_services,
        "ready_for_traffic": not critical_unhealthy,
    }


@router.get("/health/flags")
async def feature_flags():
    """Return current feature flag state for operational visibility."""
    return {
        "cerfa_generation": settings.feature_cerfa_generation,
        "stripe_payments": settings.feature_stripe_payments,
        "plan_entitlements_enforcement": settings.feature_plan_entitlements_enforcement,
        "new_checkout_catalog": settings.feature_new_checkout_catalog,
        "pdf_render_direct": settings.feature_pdf_render_direct,
        "multi_sci_dashboard_v2": settings.feature_multi_sci_dashboard_v2,
        "maintenance_mode": settings.maintenance_mode,
        "environment": settings.app_env.value,
    }


# ═══════════════════════════════════════════════════════════════════
#  SÉMANTIQUE DES SONDES
#
#  Liveness  = « le processus est-il récupérable ? »  Non -> redémarre-moi.
#  Readiness = « puis-je servir du trafic ? »          Non -> retire-moi du LB.
#
#  Deux défauts corrigés le 2026-08-10, qui rendaient la surface de santé
#  fausse dans les deux sens :
#
#  1. En mode maintenance, `maintenance_middleware` n'exemptait que
#     /api/v1/health*, chemins inexistants. /health/live prenait donc un 503
#     alors que l'application allait bien, et le healthcheck Docker
#     (docker-compose.yml) marquait le conteneur unhealthy à chaque
#     maintenance.
#  2. Pendant un arrêt, `logging_middleware` rejette tout sauf /health*.
#     Les deux sondes répondaient donc 200 pendant que 100 % du trafic
#     partait en 503 : un backend bloqué en shutdown se déclarait sain et
#     n'était jamais redémarré.
#
#  Comportement désormais :
#                      | liveness | readiness
#    nominal           |   200    |   200
#    maintenance       |   200    |   503   (processus sain, ne sert pas)
#    arrêt en cours    |   503    |   503   (redémarre-moi)
# ═══════════════════════════════════════════════════════════════════


@router.get("/health/live")
async def liveness():
    """Sonde de vivacité. 503 en arrêt pour qu'un orchestrateur redémarre."""
    if is_shutting_down():
        return JSONResponse(
            status_code=503,
            content={"status": "shutting_down", "alive": False},
        )
    return {"status": "alive"}


@router.get("/health")
async def health():
    if is_shutting_down():
        return JSONResponse(
            status_code=503,
            content={"status": "shutting_down"},
        )
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness():
    # Un processus qui s'arrête ou qui est en maintenance ne sert pas de
    # trafic, quel que soit l'état de ses dépendances. On répond avant même
    # de les interroger : inutile de payer 500 ms de sondes réseau.
    if is_shutting_down():
        return JSONResponse(
            status_code=503,
            content={"status": "shutting_down", "ready_for_traffic": False},
        )
    if settings.maintenance_mode:
        return JSONResponse(
            status_code=503,
            content={"status": "maintenance", "ready_for_traffic": False},
        )

    checks = {
        "database": await _check_database(),
        "supabase_storage": await _check_supabase_storage(),
        "stripe": await _check_stripe(),
        "resend": await _check_resend(),
    }
    readiness_status, status_code, summary = _build_readiness_summary(checks)
    logger.info(
        "readiness_evaluated",
        readiness_status=readiness_status,
        status_code=status_code,
        degraded_services=summary["degraded_services"],
        critical_unhealthy=summary["critical_unhealthy"],
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "status": readiness_status,
            "checks": checks,
            "summary": summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
