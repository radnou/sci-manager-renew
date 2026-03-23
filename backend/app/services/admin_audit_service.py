"""Admin audit log service — records all admin write operations."""

from __future__ import annotations

import structlog

from app.core.supabase_client import get_supabase_service_client

logger = structlog.get_logger(__name__)


async def log_admin_action(
    action: str,
    target_user_id: str | None,
    details: dict,
    ip: str,
) -> None:
    """
    Insert an entry into admin_audit_log.
    Non-blocking: errors are logged but never raised to callers.
    """
    try:
        client = get_supabase_service_client()
        row = {
            "admin_action": action,
            "target_user_id": target_user_id,
            "details": details,
            "ip_address": ip,
        }
        client.table("admin_audit_log").insert(row).execute()
        logger.info("admin_action_logged", action=action, target_user_id=target_user_id)
    except Exception as exc:
        logger.warning("admin_audit_log_failed", action=action, error=str(exc))


def get_audit_log(page: int = 1, per_page: int = 50) -> dict:
    """
    Return paginated audit log entries, newest first.
    """
    client = get_supabase_service_client()
    offset = (page - 1) * per_page

    result = (
        client.table("admin_audit_log")
        .select("*", count="exact")
        .order("created_at", desc=True)
        .range(offset, offset + per_page - 1)
        .execute()
    )

    return {
        "entries": result.data or [],
        "total": result.count or 0,
        "page": page,
        "per_page": per_page,
    }
