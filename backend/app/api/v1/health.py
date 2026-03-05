from __future__ import annotations

import socket
from datetime import datetime, timezone
from time import perf_counter
from urllib.parse import urlparse

import stripe
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import Environment, settings
from app.core.supabase_client import get_supabase_service_client

router = APIRouter(tags=["health"])


def _check_database_socket(database_url: str) -> dict:
    parsed = urlparse(database_url)
    host = parsed.hostname
    port = parsed.port or 5432
    if not host:
        return {"healthy": False, "error": "database_url missing host"}

    start = perf_counter()
    try:
        with socket.create_connection((host, port), timeout=2):
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


@router.get("/health/live")
async def liveness():
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness():
    checks = {
        "database": await _check_database(),
        "supabase_storage": await _check_supabase_storage(),
        "stripe": await _check_stripe(),
        "resend": await _check_resend(),
    }

    all_healthy = all(check.get("healthy") is True for check in checks.values())
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
