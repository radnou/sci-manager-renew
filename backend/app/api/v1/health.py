from __future__ import annotations

import socket
from datetime import datetime, timezone
from time import perf_counter
from urllib.parse import urlparse

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
        # In local docker setup we may have PostgreSQL without full Supabase API.
        if settings.app_env == Environment.DEVELOPMENT and settings.database_url:
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
        if settings.app_env == Environment.DEVELOPMENT:
            return {
                "healthy": True,
                "degraded": True,
                "warning": f"supabase storage unavailable in development: {exc}",
            }
        return {"healthy": False, "error": str(exc)}


async def _check_stripe() -> dict:
    if not settings.stripe_secret_key:
        return {"healthy": False, "error": "missing stripe secret key"}

    stripe.api_key = settings.stripe_secret_key
    if settings.stripe_secret_key.startswith("sk_test"):
        return {"healthy": True, "mode": "test"}
    if settings.stripe_secret_key.startswith("sk_live"):
        return {"healthy": True, "mode": "live"}
    return {"healthy": False, "error": "invalid stripe key format"}


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
