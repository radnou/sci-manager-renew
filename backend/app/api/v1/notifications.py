from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from supabase import create_client

from app.core.config import settings
from app.core.exceptions import DatabaseError, ResourceNotFoundError
from app.core.security import get_current_user

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _get_client():
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    metadata: dict = {}
    read_at: Optional[str] = None
    created_at: str


class NotificationCreate(BaseModel):
    type: str
    title: str
    message: str
    metadata: dict = {}


@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    user_id: str = Depends(get_current_user),
):
    """List notifications for the current user."""
    client = _get_client()

    query = (
        client.table("notifications")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
    )

    if unread_only:
        query = query.is_("read_at", "null")

    result = query.execute()

    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    return result.data or []


@router.get("/count")
async def unread_count(user_id: str = Depends(get_current_user)):
    """Get the count of unread notifications."""
    client = _get_client()

    result = (
        client.table("notifications")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .is_("read_at", "null")
        .execute()
    )

    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    return {"count": result.count or 0}


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    user_id: str = Depends(get_current_user),
):
    """Mark a notification as read."""
    client = _get_client()

    result = (
        client.table("notifications")
        .update({"read_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", notification_id)
        .eq("user_id", user_id)
        .execute()
    )

    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    if not result.data:
        raise ResourceNotFoundError("Notification", notification_id)

    return result.data[0]


@router.patch("/read-all")
async def mark_all_as_read(user_id: str = Depends(get_current_user)):
    """Mark all notifications as read for the current user."""
    client = _get_client()

    result = (
        client.table("notifications")
        .update({"read_at": datetime.now(timezone.utc).isoformat()})
        .eq("user_id", user_id)
        .is_("read_at", "null")
        .execute()
    )

    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    return {"updated": len(result.data or [])}
