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

    configured_prices = OrderedDict(
        (
            ("starter_monthly", settings.stripe_starter_price_id),
            ("starter_annual", settings.stripe_starter_annual_price_id),
            ("pro_monthly", settings.stripe_pro_price_id),
            ("pro_annual", settings.stripe_pro_annual_price_id),
            ("cabinet_monthly", settings.stripe_cabinet_price_id),
            ("cabinet_annual", settings.stripe_cabinet_annual_price_id),
        )
    )

    missing_price_ids = [name for name, value in configured_prices.items() if not value]
    if missing_price_ids:
        return {
            "healthy": False,
            "mode": mode,
            "error": "missing stripe price ids",
            "missing_price_ids": missing_price_ids,
        }

    invalid_price_ids: list[str] = []
    inactive_price_ids: list[str] = []

    for name, price_id in configured_prices.items():
        try:
            price = stripe.Price.retrieve(price_id)
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


@router.get("/health/live")
async def liveness():
    return {"status": "alive"}


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness():
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
